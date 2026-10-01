import { Module } from '@nestjs/common';
import { DatasetIngestionController } from './dataset-ingestion.controller';
import { DatasetIngestionService } from './dataset-ingestion.service';
import { PrismaModule } from '../prisma/prisma.module';

@Module({
  imports: [PrismaModule],
  controllers: [DatasetIngestionController],
  providers: [DatasetIngestionService],
  exports: [DatasetIngestionService],
})
export class DatasetIngestionModule {}
