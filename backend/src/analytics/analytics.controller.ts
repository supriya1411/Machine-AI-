import { Controller, Get } from '@nestjs/common';
import { ApiTags, ApiOperation } from '@nestjs/swagger';
import { AnalyticsService } from './analytics.service';

@ApiTags('Analytics')
@Controller('api/v1/analytics')
export class AnalyticsController {
  constructor(private readonly analyticsService: AnalyticsService) {}

  @Get('mtbf')
  @ApiOperation({ summary: 'Get Mean Time Between Failures (MTBF) and availability metrics' })
  async getMtbf() {
    return this.analyticsService.getMtbfMetrics();
  }

  @Get('fleet-health')
  @ApiOperation({ summary: 'Get fleet health and risk score distribution' })
  async getFleetHealth() {
    return this.analyticsService.getFleetHealthDistribution();
  }

  @Get('failure-modes')
  @ApiOperation({ summary: 'Get failure mode frequency and downtime breakdown' })
  async getFailureModes() {
    return this.analyticsService.getFailureModesBreakdown();
  }

  @Get('overview')
  @ApiOperation({ summary: 'Get composite overview of MTBF, fleet health, and failure modes' })
  async getOverview() {
    return this.analyticsService.getOverview();
  }

  @Get()
  @ApiOperation({ summary: 'Get composite analytics' })
  async getAll() {
    return this.analyticsService.getOverview();
  }
}
