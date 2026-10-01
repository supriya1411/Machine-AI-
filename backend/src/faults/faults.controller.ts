import { Controller, Get, Post, Body, Query } from '@nestjs/common';
import { ApiTags, ApiOperation } from '@nestjs/swagger';
import { FaultsService } from './faults.service';

@ApiTags('Faults')
@Controller('api/v1/faults')
export class FaultsController {
  constructor(private readonly faultsService: FaultsService) {}

  @Get()
  @ApiOperation({ summary: 'Get list of real and categorized fault records' })
  async findAll(@Query() query: any) {
    return this.faultsService.findAll(query);
  }

  @Get('taxonomy')
  @ApiOperation({ summary: 'Get standardized fault categories taxonomy' })
  async getTaxonomy() {
    return this.faultsService.getTaxonomy();
  }

  @Post('normalize')
  @ApiOperation({ summary: 'Normalize unstructured fault text to standardized taxonomy' })
  async normalize(@Body() body: { text: string }) {
    return this.faultsService.normalizeFault(body?.text);
  }
}
