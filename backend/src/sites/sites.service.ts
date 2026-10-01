import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

@Injectable()
export class SitesService {
  constructor(private readonly prisma: PrismaService) {}

  async findAll() {
    const sites = await this.prisma.site.findMany({
      include: {
        _count: {
          select: {
            assets: true,
            users: true,
          },
        },
        assets: {
          select: {
            healthScore: true,
            riskLevel: true,
            status: true,
            _count: { select: { alerts: { where: { status: 'ACTIVE' } } } },
          },
        },
      },
    });

    return sites.map((s) => {
      const assetCount = s._count.assets;
      let totalHealth = 0;
      let criticalCount = 0;
      let activeAlerts = 0;

      for (const a of s.assets) {
        totalHealth += a.healthScore;
        if (a.riskLevel === 'CRITICAL' || a.status === 'DOWN') {
          criticalCount++;
        }
        activeAlerts += a._count.alerts;
      }

      const avgHealth = assetCount > 0 ? parseFloat((totalHealth / assetCount).toFixed(1)) : 100;

      return {
        id: s.id,
        name: s.name,
        code: s.code,
        address: s.address,
        city: s.city,
        state: s.state,
        country: s.country,
        latitude: s.latitude,
        longitude: s.longitude,
        status: s.status,
        assetCount,
        criticalAssetsCount: criticalCount,
        activeAlertsCount: activeAlerts,
        avgHealthScore: avgHealth,
        isSynthetic: s.isSynthetic,
        sourceDataset: s.sourceDataset,
      };
    });
  }
}
