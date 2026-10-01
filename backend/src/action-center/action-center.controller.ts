import { Controller, Get, Post, Body, Query, Param } from '@nestjs/common';
import { ApiTags, ApiOperation } from '@nestjs/swagger';
import { ActionCenterService } from './action-center.service';

@ApiTags('Action Center')
@Controller('api/v1/action-center')
export class ActionCenterController {
  constructor(private readonly actionCenterService: ActionCenterService) {}

  @Get()
  @ApiOperation({ summary: 'Get unified action center feed uniting alerts, overdue PMs, and contract risks' })
  async getFeed(@Query() query: any) {
    return this.actionCenterService.getActionCenterFeed(query);
  }

  @Post(':id/acknowledge')
  @ApiOperation({ summary: 'Acknowledge an alert item' })
  async acknowledge(@Param('id') id: string, @Body() body: { userId?: string }) {
    return this.actionCenterService.acknowledgeAlert(id, body?.userId);
  }

  @Post(':id/resolve')
  @ApiOperation({ summary: 'Resolve an alert item with resolution notes' })
  async resolve(@Param('id') id: string, @Body() body: { notes?: string }) {
    return this.actionCenterService.resolveAlert(id, body?.notes);
  }

  @Post('dispatch')
  @ApiOperation({ summary: 'Dispatch technician work order directly from an alert' })
  async dispatch(@Body() body: { alertId: string; engineerId?: string; priority?: string }) {
    return this.actionCenterService.dispatchWorkOrder(body);
  }
}
