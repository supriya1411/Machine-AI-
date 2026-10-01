import { Module } from '@nestjs/common';
import { PrismaModule } from './prisma/prisma.module';
import { AuthModule } from './auth/auth.module';
import { AssetsModule } from './assets/assets.module';
import { ActionCenterModule } from './action-center/action-center.module';
import { FaultsModule } from './faults/faults.module';
import { MaintenanceModule } from './maintenance/maintenance.module';
import { WorkOrdersModule } from './work-orders/work-orders.module';
import { ContractsModule } from './contracts/contracts.module';
import { TelemetryModule } from './telemetry/telemetry.module';
import { SitesModule } from './sites/sites.module';
import { AnalyticsModule } from './analytics/analytics.module';
import { AiModule } from './ai/ai.module';
import { EventsModule } from './websocket/events.module';
import { DatasetIngestionModule } from './ingestion/dataset-ingestion.module';
import { DashboardModule } from './dashboard/dashboard.module';
import { HealthController } from './health.controller';

@Module({
  imports: [
    PrismaModule,
    AuthModule,
    AssetsModule,
    ActionCenterModule,
    FaultsModule,
    MaintenanceModule,
    WorkOrdersModule,
    ContractsModule,
    TelemetryModule,
    SitesModule,
    AnalyticsModule,
    AiModule,
    EventsModule,
    DatasetIngestionModule,
    DashboardModule,
  ],
  controllers: [HealthController],
})
export class AppModule {}
