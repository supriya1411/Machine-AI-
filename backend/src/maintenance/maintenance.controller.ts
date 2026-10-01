import { Controller, Get, Post, Patch, Body, Query, Param } from '@nestjs/common';
import { ApiTags, ApiOperation } from '@nestjs/swagger';
import { MaintenanceService } from './maintenance.service';

@ApiTags('Maintenance')
@Controller('api/v1/maintenance')
export class MaintenanceController {
  constructor(private readonly maintenanceService: MaintenanceService) {}

  @Get()
  @ApiOperation({ summary: 'Get preventive maintenance records and overdue status' })
  async findAll(@Query() query: any) {
    return this.maintenanceService.findAll(query);
  }

  @Get('schedule')
  @ApiOperation({ summary: 'Get scheduled preventive maintenance' })
  async getSchedule(@Query() query: any) {
    return this.maintenanceService.findAll(query);
  }

  @Get('cadence')
  @ApiOperation({ summary: 'Evaluate PM cadence compliance and overdue violations' })
  async getCadence() {
    return this.maintenanceService.getCadenceEvaluations();
  }

  @Post()
  @ApiOperation({ summary: 'Schedule new preventive maintenance milestone' })
  async schedule(@Body() body: any) {
    return this.maintenanceService.scheduleMaintenance(body);
  }

  @Patch(':id/complete')
  @ApiOperation({ summary: 'Complete maintenance inspection' })
  async complete(@Param('id') id: string, @Body() body: any) {
    return this.maintenanceService.completeMaintenance(id, body);
  }
}
