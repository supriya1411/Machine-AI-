import { Injectable, NotFoundException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

@Injectable()
export class MaintenanceService {
  constructor(private readonly prisma: PrismaService) {}

  async findAll(query: {
    status?: string;
    siteId?: string;
    assetId?: string;
    page?: number;
    limit?: number;
  }) {
    const page = Math.max(1, Number(query.page) || 1);
    const limit = Math.min(100, Math.max(1, Number(query.limit) || 25));
    const skip = (page - 1) * limit;

    const where: any = {};
    if (query.status && query.status !== 'all') {
      where.status = query.status;
    }
    if (query.assetId) {
      where.OR = [
        { assetId: query.assetId },
        { asset: { assetId: query.assetId } },
      ];
    }
    if (query.siteId && query.siteId !== 'all') {
      where.asset = { siteId: query.siteId };
    }

    const [total, items, statusCounts] = await Promise.all([
      this.prisma.maintenance.count({ where }),
      this.prisma.maintenance.findMany({
        where,
        skip,
        take: limit,
        orderBy: [{ status: 'asc' }, { scheduledDate: 'asc' }],
        include: {
          asset: {
            select: { id: true, assetId: true, name: true, category: true, site: true },
          },
          engineer: {
            select: { id: true, name: true, email: true },
          },
        },
      }),
      this.prisma.maintenance.groupBy({
        by: ['status'],
        _count: { id: true },
      }),
    ]);

    return {
      data: items,
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit),
      },
      counts: statusCounts.reduce((acc: any, curr) => {
        acc[curr.status.toLowerCase()] = curr._count.id;
        return acc;
      }, {}),
    };
  }

  async getCadenceEvaluations() {
    const pms = await this.prisma.maintenance.findMany({
      where: {
        OR: [{ status: 'OVERDUE' }, { status: 'SCHEDULED' }],
      },
      include: {
        asset: { include: { site: true } },
        engineer: true,
      },
      orderBy: { scheduledDate: 'asc' },
    });

    const now = Date.now();
    const evaluated = pms.map((pm) => {
      const scheduledTime = pm.scheduledDate.getTime();
      const diffDays = Math.floor((now - scheduledTime) / 86400000);
      const isViolation = diffDays > 0;

      return {
        id: pm.id,
        assetId: pm.asset.assetId,
        assetName: pm.asset.name,
        siteName: pm.asset.site?.name || 'Unassigned',
        pmType: pm.pmType,
        cadenceDays: pm.cadenceDays,
        scheduledDate: pm.scheduledDate,
        daysOverdue: Math.max(0, diffDays),
        hasCadenceViolation: isViolation,
        urgency: diffDays > 14 ? 'CRITICAL' : diffDays > 0 ? 'HIGH' : 'NORMAL',
        assignedEngineer: pm.engineer?.name || 'Unassigned',
        status: pm.status,
      };
    });

    return {
      totalEvaluated: evaluated.length,
      violationsCount: evaluated.filter((e) => e.hasCadenceViolation).length,
      items: evaluated,
    };
  }

  async scheduleMaintenance(dto: {
    assetId: string;
    pmType: string;
    scheduledDate: string | Date;
    engineerId?: string;
    cadenceDays?: number;
    notes?: string;
  }) {
    const asset = await this.prisma.asset.findFirst({
      where: { OR: [{ id: dto.assetId }, { assetId: dto.assetId }] },
    });
    if (!asset) throw new NotFoundException('Asset not found');

    return this.prisma.maintenance.create({
      data: {
        assetId: asset.id,
        pmType: dto.pmType,
        scheduledDate: new Date(dto.scheduledDate),
        engineerId: dto.engineerId || null,
        cadenceDays: dto.cadenceDays || 90,
        notes: dto.notes,
        status: 'SCHEDULED',
        isSynthetic: true,
        sourceDataset: 'SYNTHETIC',
      },
      include: { asset: true, engineer: true },
    });
  }

  async completeMaintenance(id: string, dto: { notes?: string; engineerId?: string }) {
    const pm = await this.prisma.maintenance.findUnique({ where: { id } });
    if (!pm) throw new NotFoundException('Maintenance record not found');

    return this.prisma.maintenance.update({
      where: { id },
      data: {
        status: 'COMPLETED',
        completedDate: new Date(),
        notes: dto.notes ? `${pm.notes || ''} | Completion: ${dto.notes}` : pm.notes,
        engineerId: dto.engineerId || pm.engineerId,
      },
    });
  }
}
