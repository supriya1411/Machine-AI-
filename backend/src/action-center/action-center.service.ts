import { Injectable, NotFoundException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

@Injectable()
export class ActionCenterService {
  constructor(private readonly prisma: PrismaService) {}

  async getActionCenterFeed(query: {
    tab?: 'all' | 'alerts' | 'pm' | 'contracts';
    severity?: string;
    siteId?: string;
    status?: string;
    page?: number;
    limit?: number;
  }) {
    const page = Math.max(1, Number(query.page) || 1);
    const limit = Math.min(100, Math.max(1, Number(query.limit) || 25));
    const skip = (page - 1) * limit;

    const where: any = {};

    if (query.status && query.status !== 'all') {
      where.status = query.status;
    } else {
      where.status = { not: 'RESOLVED' }; // default active items
    }

    if (query.severity && query.severity !== 'all') {
      where.severity = query.severity;
    }

    if (query.siteId && query.siteId !== 'all') {
      where.OR = [
        { asset: { siteId: query.siteId } },
        { asset: null },
      ];
    }

    if (query.tab === 'alerts') {
      where.type = 'ENVIRONMENTAL_IOT';
    } else if (query.tab === 'pm') {
      where.type = 'OVERDUE_PM';
    } else if (query.tab === 'contracts') {
      where.type = 'CONTRACT_EXPIRY';
    }

    const [total, alerts, stats] = await Promise.all([
      this.prisma.alert.count({ where }),
      this.prisma.alert.findMany({
        where,
        skip,
        take: limit,
        orderBy: [{ severity: 'desc' }, { createdAt: 'desc' }],
        include: {
          asset: {
            select: {
              id: true,
              assetId: true,
              name: true,
              category: true,
              status: true,
              healthScore: true,
              riskLevel: true,
              site: { select: { id: true, name: true, code: true } },
            },
          },
          sensor: {
            select: { id: true, deviceId: true, name: true, unit: true, sensorType: true },
          },
          contract: {
            select: { id: true, contractId: true, name: true, customer: true, renewalRisk: true },
          },
        },
      }),
      this.getActionStats(),
    ]);

    return {
      items: alerts.map((a) => ({
        id: a.id,
        type: a.type,
        severity: a.severity,
        title: a.title,
        message: a.message,
        currentValue: a.currentValue,
        threshold: a.threshold,
        duration: a.duration,
        reason: a.reason,
        recommendedAction: a.recommendedAction,
        status: a.status,
        sourceDataset: a.sourceDataset,
        sourceRecordId: a.sourceRecordId,
        sourceEvidence: a.sourceEvidence ? JSON.parse(a.sourceEvidence) : null,
        isSynthetic: a.isSynthetic,
        createdAt: a.createdAt,
        asset: a.asset,
        sensor: a.sensor,
        contract: a.contract,
      })),
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit),
      },
      stats,
    };
  }

  async acknowledgeAlert(alertId: string, userId?: string) {
    const alert = await this.prisma.alert.findUnique({ where: { id: alertId } });
    if (!alert) throw new NotFoundException('Alert not found');

    return this.prisma.alert.update({
      where: { id: alertId },
      data: {
        status: 'ACKNOWLEDGED',
        acknowledgedAt: new Date(),
        acknowledgedBy: userId || null,
      },
    });
  }

  async resolveAlert(alertId: string, resolutionNotes?: string) {
    const alert = await this.prisma.alert.findUnique({ where: { id: alertId } });
    if (!alert) throw new NotFoundException('Alert not found');

    return this.prisma.alert.update({
      where: { id: alertId },
      data: {
        status: 'RESOLVED',
        resolvedAt: new Date(),
        message: resolutionNotes ? `${alert.message} | Resolved: ${resolutionNotes}` : alert.message,
      },
    });
  }

  async dispatchWorkOrder(dto: { alertId: string; engineerId?: string; priority?: string }) {
    const alert = await this.prisma.alert.findUnique({
      where: { id: dto.alertId },
      include: { asset: true },
    });
    if (!alert) throw new NotFoundException('Alert not found');
    if (!alert.assetId) throw new NotFoundException('Alert is not tied to a dispatchable asset');

    const wo = await this.prisma.workOrder.create({
      data: {
        assetId: alert.assetId,
        type: 'CORRECTIVE',
        priority: dto.priority || (alert.severity === 'CRITICAL' ? 'CRITICAL' : 'HIGH'),
        assignedEngineerId: dto.engineerId || null,
        dueDate: new Date(Date.now() + 24 * 3600000),
        status: 'OPEN',
        description: `Dispatched from Action Center Alert [${alert.title}]: ${alert.recommendedAction || alert.message}`,
        isSynthetic: true,
        sourceDataset: 'SYNTHETIC',
      },
    });

    // Mark alert acknowledged
    await this.prisma.alert.update({
      where: { id: dto.alertId },
      data: { status: 'ACKNOWLEDGED', acknowledgedAt: new Date() },
    });

    return {
      success: true,
      workOrder: wo,
      message: `Work Order ${wo.id} created and dispatched.`,
    };
  }

  private async getActionStats() {
    const [critical, high, medium, environmental, pm, contracts] = await Promise.all([
      this.prisma.alert.count({ where: { severity: 'CRITICAL', status: { not: 'RESOLVED' } } }),
      this.prisma.alert.count({ where: { severity: 'HIGH', status: { not: 'RESOLVED' } } }),
      this.prisma.alert.count({ where: { severity: 'MEDIUM', status: { not: 'RESOLVED' } } }),
      this.prisma.alert.count({ where: { type: 'ENVIRONMENTAL_IOT', status: { not: 'RESOLVED' } } }),
      this.prisma.alert.count({ where: { type: 'OVERDUE_PM', status: { not: 'RESOLVED' } } }),
      this.prisma.alert.count({ where: { type: 'CONTRACT_EXPIRY', status: { not: 'RESOLVED' } } }),
    ]);

    return {
      totalActive: critical + high + medium,
      critical,
      high,
      medium,
      environmentalAlerts: environmental,
      overduePms: pm,
      contractRisks: contracts,
    };
  }
}
