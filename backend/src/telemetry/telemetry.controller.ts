import { Controller, Get, Post, Body, Query } from '@nestjs/common';
import { ApiTags, ApiOperation } from '@nestjs/swagger';
import { TelemetryService } from './telemetry.service';

@ApiTags('Telemetry')
@Controller('api/v1/telemetry')
export class TelemetryController {
  constructor(private readonly telemetryService: TelemetryService) {}

  @Get('latest')
  @ApiOperation({ summary: 'Get latest sensor telemetry readings' })
  async getLatest(@Query() query: any) {
    return this.telemetryService.getLatestReadings(query);
  }

  @Get('anomalies')
  @ApiOperation({ summary: 'Get anomaly events derived from telemetry threshold breaches' })
  async getAnomalies(@Query() query: any) {
    return this.telemetryService.getAnomalies(query);
  }

  @Post('ingest')
  @ApiOperation({ summary: 'Ingest live sensor reading and evaluate threshold breaches' })
  async ingest(@Body() body: any) {
    return this.telemetryService.ingestReading(body);
  }
}
