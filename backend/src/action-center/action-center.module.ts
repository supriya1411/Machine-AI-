import { Module } from '@nestjs/common';
import { ActionCenterController } from './action-center.controller';
import { ActionCenterService } from './action-center.service';
import { PrismaModule } from '../prisma/prisma.module';

@Module({
  imports: [PrismaModule],
  controllers: [ActionCenterController],
  providers: [ActionCenterService],
  exports: [ActionCenterService],
})
export class ActionCenterModule {}
