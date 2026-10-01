import { describe, it } from 'node:test';
import * as assert from 'node:assert';
import { PrismaClient } from '@prisma/client';
import { FaultsService } from '../src/faults/faults.service';
import { AnalyticsService } from '../src/analytics/analytics.service';
import { AiService } from '../src/ai/ai.service';
import { DatasetIngestionService } from '../src/ingestion/dataset-ingestion.service';
import { AssetsService } from '../src/assets/assets.service';
import { ActionCenterService } from '../src/action-center/action-center.service';
import { TelemetryService } from '../src/telemetry/telemetry.service';
import { MaintenanceService } from '../src/maintenance/maintenance.service';
import { ContractsService } from '../src/contracts/contracts.service';
import { HealthController } from '../src/health.controller';

let testDbUrl = (process.env.DATABASE_URL || '').trim();
if ((testDbUrl.startsWith('"') && testDbUrl.endsWith('"')) || (testDbUrl.startsWith("'") && testDbUrl.endsWith("'"))) {
  testDbUrl = testDbUrl.slice(1, -1).trim();
}
if (!testDbUrl || !testDbUrl.startsWith('file:')) {
  testDbUrl = 'file:/app/applet/backend/prisma/dev.db';
}
process.env.DATABASE_URL = testDbUrl;

const prisma = new PrismaClient({
  datasources: {
    db: { url: testDbUrl },
  },
});

describe('AURUM Service Intelligence Test Suite', () => {
  it('1. Database connectivity and dataset counts', async () => {
    const assetCount = await prisma.asset.count();
    const faultCount = await prisma.faultRecord.count();
    const sensorCount = await prisma.sensorDevice.count();
    const alertCount = await prisma.alert.count();

    assert.ok(assetCount >= 100, `Expected at least 100 assets, found ${assetCount}`);
    assert.ok(faultCount >= 50, `Expected at least 50 faults, found ${faultCount}`);
    assert.ok(sensorCount >= 200, `Expected at least 200 sensors, found ${sensorCount}`);
    assert.ok(alertCount >= 10, `Expected at least 10 alerts, found ${alertCount}`);
  });

  it('2. Dataset provenance and source isolation', async () => {
    const cmapssAssets = await prisma.asset.count({ where: { sourceDataset: 'CMAPSS' } });
    const ai4iAssets = await prisma.asset.count({ where: { sourceDataset: 'AI4I_2020' } });

    assert.ok(cmapssAssets > 0, `Expected C-MAPSS assets, found ${cmapssAssets}`);
    assert.ok(ai4iAssets > 0, `Expected AI4I 2020 assets, found ${ai4iAssets}`);

    // Verify source record IDs are preserved
    const sampleCmapss = await prisma.asset.findFirst({ where: { sourceDataset: 'CMAPSS' } });
    assert.ok(sampleCmapss?.sourceRecordId?.includes('unit'), 'C-MAPSS asset should preserve unit ID');

    const sampleAi4i = await prisma.asset.findFirst({ where: { sourceDataset: 'AI4I_2020' } });
    assert.ok(sampleAi4i?.sourceRecordId?.includes('UDI'), 'AI4I asset should preserve UDI ID');
  });

  it('3. Fault Normalization Service Keyword Matching', async () => {
    const faultsService = new FaultsService(prisma as any);

    // Test Heat Dissipation Failure matching
    const hdfResult = await faultsService.normalizeFault('High thermal buildup and insufficient heat dissipation observed');
    assert.strictEqual(hdfResult.normalizedCode, 'HDF');
    assert.ok(hdfResult.confidence > 0.6);

    // Test Tool Wear Failure matching
    const twfResult = await faultsService.normalizeFault('Cutting insert severely worn out with excessive tool wear');
    assert.strictEqual(twfResult.normalizedCode, 'TWF');
    assert.ok(twfResult.confidence > 0.6);

    // Test HPC Degradation matching
    const hpcResult = await faultsService.normalizeFault('HPC compressor blade erosion and thermal rise in stage 4');
    assert.strictEqual(hpcResult.normalizedCode, 'HPC_DEGRADATION');
    assert.ok(hpcResult.confidence > 0.6);
  });

  it('4. MTBF and Reliability Analytics Calculation', async () => {
    const analyticsService = new AnalyticsService(prisma as any);
    const metrics = await analyticsService.getMtbfMetrics();

    assert.ok(metrics.fleetSummary.totalOperatingHours > 0);
    assert.ok(metrics.fleetSummary.fleetMtbfHours > 0);
    assert.ok(metrics.fleetSummary.fleetAvailability > 80);
    assert.ok(Array.isArray(metrics.categories));
  });

  it('5. Grounded AI Assistant with Database Evidence Linkage', async () => {
    const aiService = new AiService(prisma as any);
    const result = await aiService.processQuery('Which equipment has high risk?');

    assert.ok(result.answer.length > 20);
    assert.ok(result.evidence.length > 0, 'Response must include attached database evidence');
    assert.ok(result.evidence[0].id, 'Evidence item must retain record ID');
  });

  it('6. Assets Service pagination, filtering and asset details', async () => {
    const assetsService = new AssetsService(prisma as any);
    const res = await assetsService.findAll({ limit: 10, page: 1 });
    assert.strictEqual(res.data.length, 10);
    assert.ok(res.pagination.total >= 600);

    const asset = await assetsService.findOne(res.data[0].assetId);
    assert.ok(asset);
    assert.strictEqual(asset.assetId, res.data[0].assetId);
    assert.ok(Array.isArray(asset.sensors));
  });

  it('7. Action Center alert aggregation and dispatch', async () => {
    const actionService = new ActionCenterService(prisma as any);
    const feed = await actionService.getActionCenterFeed({});
    assert.ok(feed.pagination.total > 0);
    assert.ok(Array.isArray(feed.items));

    // Test dispatch technician
    const firstAlert = feed.items.find((a: any) => a.asset);
    if (firstAlert) {
      const dispatchRes = await actionService.dispatchWorkOrder({
        alertId: firstAlert.id,
        priority: 'HIGH',
      });
      assert.strictEqual(dispatchRes.success, true);
      assert.ok(dispatchRes.workOrder);
      assert.strictEqual(dispatchRes.workOrder.priority, 'HIGH');
    }
  });

  it('8. Telemetry Service sensor anomalies retrieval', async () => {
    const telemetryService = new TelemetryService(prisma as any);
    const anomalies = await telemetryService.getAnomalies({ limit: 5 });
    assert.ok(anomalies.data.length > 0);
    assert.ok(anomalies.data[0].severity);
    assert.ok(anomalies.data[0].value !== undefined);
  });

  it('9. Preventive Maintenance schedule and cadence', async () => {
    const pmService = new MaintenanceService(prisma as any);
    const cadence = await pmService.getCadenceEvaluations();
    assert.ok(cadence.totalEvaluated >= 0);
    assert.ok(Array.isArray(cadence.items));
  });

  it('10. Contracts Service renewal risk summary', async () => {
    const contractsService = new ContractsService(prisma as any);
    const risk = await contractsService.getRiskSummary();
    assert.ok(risk.totalContracts > 0);
    assert.ok(risk.expiringIn30Days >= 0);
  });

  it('11. System Health and status endpoints', async () => {
    const healthController = new HealthController(prisma as any);
    const health = await healthController.getHealth();
    assert.strictEqual(health.status, 'HEALTHY');
    assert.strictEqual(health.database, 'CONNECTED');

    const status = await healthController.getRoot();
    assert.strictEqual(status.status, 'OPERATIONAL');
    assert.ok(status.telemetry.totalAssets >= 600);
  });
});
