import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

@Injectable()
export class DashboardService {
  constructor(private readonly prisma: PrismaService) {}

  async getExecutiveDashboard() {
    const [
      totalAssets,
      criticalRiskAssets,
      downAssets,
      degradedAssets,
      criticalAlertsCount,
      activeContracts,
      sites,
      topFaults,
      sensorCount,
      recentAnomalies,
      actionCenterItems,
    ] = await Promise.all([
      this.prisma.asset.count(),
      this.prisma.asset.count({ where: { riskLevel: 'CRITICAL' } }),
      this.prisma.asset.count({ where: { status: 'DOWN' } }),
      this.prisma.asset.count({ where: { status: 'DEGRADED' } }),
      this.prisma.alert.count({ where: { severity: 'CRITICAL', status: { not: 'RESOLVED' } } }),
      this.prisma.contract.findMany({ select: { value: true, endDate: true } }),
      this.prisma.site.findMany({
        include: {
          _count: { select: { assets: true } },
          assets: { select: { riskLevel: true, healthScore: true } },
        },
      }),
      this.prisma.faultRecord.groupBy({
        by: ['failureType'],
        _count: { id: true },
        _sum: { downtime: true },
        orderBy: { _count: { id: 'desc' } },
        take: 5,
      }),
      this.prisma.sensorDevice.count(),
      this.prisma.sensorAnomaly.count(),
      this.prisma.alert.findMany({
        where: { status: { not: 'RESOLVED' } },
        orderBy: { severity: 'desc' },
        take: 5,
        include: { asset: { select: { name: true, assetId: true } } },
      }),
    ]);

    const aggregates = await this.prisma.asset.aggregate({
      _avg: { healthScore: true, riskScore: true },
    });

    const now = Date.now();
    let totalContractValue = 0;
    let expiring30Days = 0;
    for (const c of activeContracts) {
      totalContractValue += c.value;
      const days = (c.endDate.getTime() - now) / 86400000;
      if (days >= 0 && days <= 30) expiring30Days++;
    }

    return {
      kpis: {
        totalAssets,
        operationalAssets: totalAssets - (downAssets + degradedAssets),
        highRiskAssets: criticalRiskAssets,
        criticalAlertsCount,
        overallHealthIndex: parseFloat((aggregates._avg.healthScore || 85.0).toFixed(1)),
        activeContractsValue: totalContractValue,
        contractsExpiring30Days: expiring30Days,
        monitoredSensors: sensorCount,
        detectedAnomalies: recentAnomalies,
      },
      healthDistribution: {
        critical: criticalRiskAssets,
        degraded: degradedAssets,
        operational: totalAssets - (downAssets + degradedAssets),
      },
      locations: sites.map((s) => ({
        id: s.id,
        name: s.name,
        code: s.code,
        city: s.city,
        country: s.country,
        latitude: s.latitude,
        longitude: s.longitude,
        totalAssets: s._count.assets,
        criticalAssets: s.assets.filter((a) => a.riskLevel === 'CRITICAL').length,
      })),
      topFaults: topFaults.map((tf) => ({
        failureType: tf.failureType || 'OTHER',
        count: tf._count.id,
        downtimeHours: parseFloat((tf._sum.downtime || 0).toFixed(1)),
      })),
      actionCenterPreview: actionCenterItems.map((a) => ({
        id: a.id,
        priority: a.severity,
        type: a.type,
        title: a.title,
        asset: a.asset?.name || a.assetId,
        recommendedAction: a.recommendedAction,
      })),
      liveSystemStatus: {
        iotGatewayStatus: 'HEALTHY',
        databaseEngine: 'PostgreSQL / Prisma Relational Store',
        ingestedDatasets: ['NASA C-MAPSS (FD001-FD004)', 'AI4I 2020 Predictive Maintenance'],
      },
    };
  }
}
