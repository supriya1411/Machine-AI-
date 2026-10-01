import { Module } from '@nestjs/common';
import { FaultsController } from './faults.controller';
import { FaultsService } from './faults.service';
import { PrismaModule } from '../prisma/prisma.module';

@Module({
  imports: [PrismaModule],
  controllers: [FaultsController],
  providers: [FaultsService],
  exports: [FaultsService],
})
export class FaultsModule {}
