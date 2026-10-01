import { Controller, Get } from '@nestjs/common';
import { ApiTags, ApiOperation } from '@nestjs/swagger';
import { SitesService } from './sites.service';

@ApiTags('Sites')
@Controller('api/v1/sites')
export class SitesController {
  constructor(private readonly sitesService: SitesService) {}

  @Get()
  @ApiOperation({ summary: 'Get list of operating sites with health index and active alert counts' })
  async findAll() {
    return this.sitesService.findAll();
  }
}
