import { Controller, Post, Get, Body } from '@nestjs/common';
import { ApiTags, ApiOperation } from '@nestjs/swagger';
import { DatasetIngestionService } from './dataset-ingestion.service';

@ApiTags('Dataset Ingestion')
@Controller('api/v1/ingestion')
export class DatasetIngestionController {
  constructor(private readonly ingestionService: DatasetIngestionService) {}

  @Post('run')
  @ApiOperation({ summary: 'Trigger ingestion of NASA C-MAPSS and AI4I 2020 datasets' })
  async runIngestion(@Body() body: { force?: boolean }) {
    return this.ingestionService.runIngestion(body);
  }

  @Get('summary')
  @ApiOperation({ summary: 'Get summary statistics of imported and derived records' })
  async getSummary() {
    return this.ingestionService.getIngestionSummary();
  }
}
