import { Controller, Get } from '@nestjs/common';
import { ApiTags, ApiOperation } from '@nestjs/swagger';
import { PrismaService } from './prisma/prisma.service';

@ApiTags('Health')
@Controller('api/v1')
export class HealthController {
  constructor(private readonly prisma: PrismaService) {}

  @Get('status')
  @ApiOperation({ summary: 'Backend root status and system information' })
  async getRoot() {
    const [assets, faults, anomalies, alerts] = await Promise.all([
      this.prisma.asset.count().catch(() => 0),
      this.prisma.faultRecord.count().catch(() => 0),
      this.prisma.sensorAnomaly.count().catch(() => 0),
      this.prisma.alert.count().catch(() => 0),
    ]);

    return {
      name: 'AURUM Service Intelligence API',
      version: '1.0.0',
      status: 'OPERATIONAL',
      datasets: {
        nasaCmapss: 'Integrated (FD001, FD002, FD003, FD004)',
        ai4i2020: 'Integrated (AI4I Predictive Maintenance)',
      },
      telemetry: {
        totalAssets: assets,
        faultRecords: faults,
        sensorAnomalies: anomalies,
        activeAlerts: alerts,
      },
      docsUrl: '/docs',
      timestamp: new Date().toISOString(),
    };
  }

  @Get('health')
  @ApiOperation({ summary: 'System health check and database connectivity' })
  async getHealth() {
    let dbStatus = 'CONNECTED';
    let dbError: string | undefined = undefined;
    try {
      await this.prisma.asset.count();
    } catch (e: any) {
      dbStatus = 'DEGRADED';
      dbError = e?.message || String(e);
    }

    return {
      status: 'HEALTHY',
      database: dbStatus,
      dbError,
      uptimeSeconds: Math.floor(process.uptime()),
      timestamp: new Date().toISOString(),
    };
  }
}
