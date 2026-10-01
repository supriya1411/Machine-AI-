import { Controller, Get, Param, Query } from '@nestjs/common';
import { ApiTags, ApiOperation } from '@nestjs/swagger';
import { ContractsService } from './contracts.service';

@ApiTags('Contracts')
@Controller('api/v1/contracts')
export class ContractsController {
  constructor(private readonly contractsService: ContractsService) {}

  @Get()
  @ApiOperation({ summary: 'Get list of service contracts (AMC/CMC) with renewal risk metrics' })
  async findAll(@Query() query: any) {
    return this.contractsService.findAll(query);
  }

  @Get('risk-summary')
  @ApiOperation({ summary: 'Get summary of contract expiration risks across 15/30 day horizons' })
  async getRiskSummary() {
    return this.contractsService.getRiskSummary();
  }

  @Get(':id')
  @ApiOperation({ summary: 'Get single contract detail with covered assets' })
  async findOne(@Param('id') id: string) {
    return this.contractsService.findOne(id);
  }
}
