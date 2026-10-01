import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

@Injectable()
export class AnalyticsService {
  constructor(private readonly prisma: PrismaService) {}

  async getMtbfMetrics() {
    const assets = await this.prisma.asset.findMany({
      include: {
        faults: true,
      },
    });

    const categoryStats: Record<string, { totalOperatingHours: number; downtimeHours: number; failures: number }> = {};
    let fleetOperatingHours = 0;
    let fleetDowntimeHours = 0;
    let fleetFailures = 0;

    for (const a of assets) {
      const cat = a.category;
      if (!categoryStats[cat]) {
        categoryStats[cat] = { totalOperatingHours: 0, downtimeHours: 0, failures: 0 };
      }

      // Operational lifetime in hours
      const opHours = a.category === 'Turbofan Engine' ? 1200 : 2500;
      const downHours = a.faults.reduce((sum, f) => sum + f.downtime, 0);
      const fails = a.faults.length;

      categoryStats[cat].totalOperatingHours += opHours;
      categoryStats[cat].downtimeHours += downHours;
      categoryStats[cat].failures += fails;

      fleetOperatingHours += opHours;
      fleetDowntimeHours += downHours;
      fleetFailures += fails;
    }

    const categories = Object.entries(categoryStats).map(([category, stats]) => {
      const mtbf = stats.failures > 0
        ? parseFloat(((stats.totalOperatingHours - stats.downtimeHours) / stats.failures).toFixed(1))
        : stats.totalOperatingHours;

      const mttr = stats.failures > 0
        ? parseFloat((stats.downtimeHours / stats.failures).toFixed(1))
        : 0;

      const availability = stats.totalOperatingHours > 0
        ? parseFloat((((stats.totalOperatingHours - stats.downtimeHours) / stats.totalOperatingHours) * 100).toFixed(2))
        : 100;

      return {
        category,
        totalOperatingHours: stats.totalOperatingHours,
        totalDowntimeHours: parseFloat(stats.downtimeHours.toFixed(1)),
        failureCount: stats.failures,
        mtbfHours: mtbf,
        mttrHours: mttr,
        availabilityPercentage: availability,
      };
    });

    const fleetMtbf = fleetFailures > 0
      ? parseFloat(((fleetOperatingHours - fleetDowntimeHours) / fleetFailures).toFixed(1))
      : fleetOperatingHours;

    const fleetMttr = fleetFailures > 0
      ? parseFloat((fleetDowntimeHours / fleetFailures).toFixed(1))
      : 0;

    return {
      fleetSummary: {
        totalOperatingHours: fleetOperatingHours,
        totalDowntimeHours: parseFloat(fleetDowntimeHours.toFixed(1)),
        totalFailures: fleetFailures,
        fleetMtbfHours: fleetMtbf,
        fleetMttrHours: fleetMttr,
        fleetAvailability: parseFloat((((fleetOperatingHours - fleetDowntimeHours) / fleetOperatingHours) * 100).toFixed(2)),
      },
      categories,
    };
  }

  async getFleetHealthDistribution() {
    const [riskGroups, categoryGroups, sourceGroups] = await Promise.all([
      this.prisma.asset.groupBy({
        by: ['riskLevel'],
        _count: { id: true },
      }),
      this.prisma.asset.groupBy({
        by: ['category'],
        _count: { id: true },
        _avg: { healthScore: true, riskScore: true },
      }),
      this.prisma.asset.groupBy({
        by: ['sourceDataset'],
        _count: { id: true },
      }),
    ]);

    return {
      byRiskLevel: riskGroups.reduce((acc: any, curr) => {
        acc[curr.riskLevel.toLowerCase()] = curr._count.id;
        return acc;
      }, {}),
      byCategory: categoryGroups.map((cg) => ({
        category: cg.category,
        count: cg._count.id,
        avgHealthScore: parseFloat((cg._avg.healthScore || 0).toFixed(1)),
        avgRiskScore: parseFloat((cg._avg.riskScore || 0).toFixed(1)),
      })),
      bySourceDataset: sourceGroups.map((sg) => ({
        sourceDataset: sg.sourceDataset,
        count: sg._count.id,
      })),
    };
  }

  async getFailureModesBreakdown() {
    const faultGroups = await this.prisma.faultRecord.groupBy({
      by: ['failureType'],
      _count: { id: true },
      _sum: { downtime: true },
    });

    return faultGroups.map((fg) => ({
      failureType: fg.failureType || 'OTHER',
      count: fg._count.id,
      totalDowntimeHours: parseFloat((fg._sum.downtime || 0).toFixed(1)),
    }));
  }

  async getOverview() {
    const [mtbf, fleetHealth, failureModes] = await Promise.all([
      this.getMtbfMetrics(),
      this.getFleetHealthDistribution(),
      this.getFailureModesBreakdown(),
    ]);

    return {
      mtbf,
      fleetHealth,
      failureModes,
    };
  }
}
