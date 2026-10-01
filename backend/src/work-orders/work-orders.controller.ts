import { Controller, Get, Post, Patch, Body, Query, Param } from '@nestjs/common';
import { ApiTags, ApiOperation } from '@nestjs/swagger';
import { WorkOrdersService } from './work-orders.service';

@ApiTags('Work Orders')
@Controller('api/v1/work-orders')
export class WorkOrdersController {
  constructor(private readonly workOrdersService: WorkOrdersService) {}

  @Get()
  @ApiOperation({ summary: 'Get paginated list of maintenance work orders' })
  async findAll(@Query() query: any) {
    return this.workOrdersService.findAll(query);
  }

  @Get(':id')
  @ApiOperation({ summary: 'Get single work order detail' })
  async findOne(@Param('id') id: string) {
    return this.workOrdersService.findOne(id);
  }

  @Post()
  @ApiOperation({ summary: 'Create new corrective or preventive work order' })
  async create(@Body() body: any) {
    return this.workOrdersService.create(body);
  }

  @Patch(':id')
  @ApiOperation({ summary: 'Update work order status or assigned technician' })
  async update(@Param('id') id: string, @Body() body: any) {
    return this.workOrdersService.update(id, body);
  }
}
