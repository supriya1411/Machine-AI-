import { Injectable, NotFoundException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

@Injectable()
export class ContractsService {
  constructor(private readonly prisma: PrismaService) {}

  async findAll(query: {
    status?: string;
    type?: string;
    renewalRisk?: string;
  }) {
    const where: any = {};
    if (query.status && query.status !== 'all') {
      where.status = query.status;
    }
    if (query.type && query.type !== 'all') {
      where.type = query.type;
    }
    if (query.renewalRisk && query.renewalRisk !== 'all') {
      where.renewalRisk = query.renewalRisk;
    }

    const contracts = await this.prisma.contract.findMany({
      where,
      orderBy: [{ renewalRisk: 'desc' }, { endDate: 'asc' }],
      include: {
        _count: { select: { contractAssets: true, maintenances: true, alerts: true } },
      },
    });

    const now = Date.now();
    return {
      data: contracts.map((c) => {
        const daysRemaining = Math.max(0, Math.floor((c.endDate.getTime() - now) / 86400000));
        return {
          id: c.id,
          contractId: c.contractId,
          name: c.name,
          customer: c.customer,
          vendor: c.vendor,
          type: c.type,
          startDate: c.startDate,
          endDate: c.endDate,
          value: c.value,
          pmFrequencyDays: c.pmFrequencyDays,
          status: c.status,
          complianceScore: c.complianceScore,
          renewalRisk: c.renewalRisk,
          daysRemaining,
          isSynthetic: c.isSynthetic,
          sourceDataset: c.sourceDataset,
          coveredAssetsCount: c._count.contractAssets,
          maintenanceCount: c._count.maintenances,
          activeAlertsCount: c._count.alerts,
        };
      }),
      summary: await this.getRiskSummary(),
    };
  }

  async findOne(id: string) {
    const contract = await this.prisma.contract.findFirst({
      where: { OR: [{ id }, { contractId: id }] },
      include: {
        contractAssets: {
          include: {
            asset: {
              include: { site: true },
            },
          },
        },
        maintenances: {
          orderBy: { scheduledDate: 'desc' },
          take: 10,
        },
        alerts: {
          where: { status: 'ACTIVE' },
        },
      },
    });

    if (!contract) throw new NotFoundException('Contract not found');

    const daysRemaining = Math.max(0, Math.floor((contract.endDate.getTime() - Date.now()) / 86400000));

    return {
      ...contract,
      daysRemaining,
      assets: contract.contractAssets.map((ca) => ca.asset),
    };
  }

  async getRiskSummary() {
    const contracts = await this.prisma.contract.findMany();
    const now = Date.now();

    let expiringIn15Days = 0;
    let expiringIn30Days = 0;
    let criticalRiskCount = 0;

    for (const c of contracts) {
      const days = Math.floor((c.endDate.getTime() - now) / 86400000);
      if (days <= 15) expiringIn15Days++;
      if (days <= 30) expiringIn30Days++;
      if (c.renewalRisk === 'CRITICAL' || c.renewalRisk === 'HIGH') criticalRiskCount++;
    }

    return {
      totalContracts: contracts.length,
      expiringIn15Days,
      expiringIn30Days,
      criticalRiskCount,
    };
  }
}
