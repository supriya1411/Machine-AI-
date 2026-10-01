import { Controller, Get, Param, Query } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiQuery, ApiResponse } from '@nestjs/swagger';
import { AssetsService } from './assets.service';

@ApiTags('Assets')
@Controller('api/v1/assets')
export class AssetsController {
  constructor(private readonly assetsService: AssetsService) {}

  @Get()
  @ApiOperation({ summary: 'Get paginated list of assets with telemetry aggregates and filters' })
  @ApiQuery({ name: 'page', required: false, type: Number })
  @ApiQuery({ name: 'limit', required: false, type: Number })
  @ApiQuery({ name: 'search', required: false, type: String })
  @ApiQuery({ name: 'siteId', required: false, type: String })
  @ApiQuery({ name: 'category', required: false, type: String })
  @ApiQuery({ name: 'status', required: false, type: String })
  @ApiQuery({ name: 'riskLevel', required: false, type: String })
  @ApiQuery({ name: 'sourceDataset', required: false, type: String })
  async findAll(@Query() query: any) {
    return this.assetsService.findAll(query);
  }

  @Get(':id')
  @ApiOperation({ summary: 'Get comprehensive asset profile with sensors, active alerts, and faults' })
  async findOne(@Param('id') id: string) {
    return this.assetsService.findOne(id);
  }

  @Get(':id/telemetry')
  @ApiOperation({ summary: 'Get time-series or cycle-series sensor readings for an asset' })
  @ApiQuery({ name: 'limit', required: false, type: Number })
  @ApiQuery({ name: 'sensorType', required: false, type: String })
  async getTelemetry(@Param('id') id: string, @Query() query: any) {
    return this.assetsService.getTelemetry(id, query);
  }

  @Get(':id/health-history')
  @ApiOperation({ summary: 'Get historical health scores and degradation progression' })
  async getHealthHistory(@Param('id') id: string) {
    return this.assetsService.getHealthHistory(id);
  }
}
