import { Injectable, NotFoundException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

@Injectable()
export class TelemetryService {
  constructor(private readonly prisma: PrismaService) {}

  async getLatestReadings(query: { limit?: number; sensorType?: string }) {
    const limit = Math.min(100, Math.max(1, Number(query.limit) || 20));
    const where: any = {};
    if (query.sensorType) {
      where.sensor = { sensorType: query.sensorType };
    }

    const readings = await this.prisma.sensorReading.findMany({
      where,
      orderBy: { timestamp: 'desc' },
      take: limit,
      include: {
        sensor: {
          select: { id: true, deviceId: true, name: true, sensorType: true, unit: true, status: true },
        },
        asset: {
          select: { id: true, assetId: true, name: true, category: true, site: true },
        },
      },
    });

    return readings;
  }

  async getAnomalies(query: {
    severity?: string;
    assetId?: string;
    sensorType?: string;
    page?: number;
    limit?: number;
  }) {
    const page = Math.max(1, Number(query.page) || 1);
    const limit = Math.min(100, Math.max(1, Number(query.limit) || 20));
    const skip = (page - 1) * limit;

    const where: any = {};
    if (query.severity && query.severity !== 'all') {
      where.severity = query.severity;
    }
    if (query.assetId) {
      where.OR = [
        { assetId: query.assetId },
        { asset: { assetId: query.assetId } },
      ];
    }
    if (query.sensorType) {
      where.sensor = { sensorType: query.sensorType };
    }

    const [total, anomalies] = await Promise.all([
      this.prisma.sensorAnomaly.count({ where }),
      this.prisma.sensorAnomaly.findMany({
        where,
        skip,
        take: limit,
        orderBy: { timestamp: 'desc' },
        include: {
          sensor: {
            select: { id: true, deviceId: true, name: true, sensorType: true, unit: true },
          },
          asset: {
            select: { id: true, assetId: true, name: true, category: true, site: true },
          },
        },
      }),
    ]);

    return {
      data: anomalies.map((a) => ({
        id: a.id,
        timestamp: a.timestamp,
        severity: a.severity,
        value: a.value,
        thresholdBreached: a.thresholdBreached,
        durationMinutes: a.durationMinutes,
        sourceDataset: a.sourceDataset,
        sourceRecordId: a.sourceRecordId,
        evidenceDetail: a.evidenceDetail ? JSON.parse(a.evidenceDetail) : null,
        asset: a.asset,
        sensor: a.sensor,
      })),
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit),
      },
    };
  }

  async ingestReading(dto: {
    assetId: string;
    deviceId: string;
    value: number;
    timestamp?: string | Date;
  }) {
    const sensor = await this.prisma.sensorDevice.findUnique({
      where: { deviceId: dto.deviceId },
      include: { asset: true },
    });

    if (!sensor) throw new NotFoundException(`Sensor with deviceId ${dto.deviceId} not found.`);

    const readingTime = dto.timestamp ? new Date(dto.timestamp) : new Date();

    // Store reading
    const reading = await this.prisma.sensorReading.create({
      data: {
        sensorId: sensor.id,
        assetId: sensor.assetId,
        timestamp: readingTime,
        value: dto.value,
        unit: sensor.unit,
        sourceDataset: 'SYNTHETIC_LIVE',
        sourceRecordId: `LIVE-${Date.now()}`,
      },
    });

    // Check breach
    let breached = false;
    let severity = 'NORMAL';
    if (sensor.criticalMax && dto.value >= sensor.criticalMax) {
      breached = true;
      severity = 'CRITICAL';
    } else if (sensor.warningMax && dto.value >= sensor.warningMax) {
      breached = true;
      severity = 'WARNING';
    }

    let anomaly = null;
    let alert = null;

    if (breached) {
      anomaly = await this.prisma.sensorAnomaly.create({
        data: {
          sensorId: sensor.id,
          assetId: sensor.assetId,
          timestamp: readingTime,
          severity,
          value: dto.value,
          thresholdBreached: `${dto.value} ${sensor.unit} exceeded threshold ${severity === 'CRITICAL' ? sensor.criticalMax : sensor.warningMax} ${sensor.unit}`,
          durationMinutes: 1,
          sourceDataset: 'SYNTHETIC_LIVE',
          sourceRecordId: `LIVE-ANOM-${Date.now()}`,
          evidenceDetail: JSON.stringify({
            deviceId: sensor.deviceId,
            sensorType: sensor.sensorType,
            value: dto.value,
            unit: sensor.unit,
            threshold: severity === 'CRITICAL' ? sensor.criticalMax : sensor.warningMax,
          }),
        },
      });

      if (severity === 'CRITICAL') {
        alert = await this.prisma.alert.create({
          data: {
            type: 'ENVIRONMENTAL_IOT',
            severity: 'CRITICAL',
            assetId: sensor.assetId,
            sensorId: sensor.id,
            title: `Live Breach: ${sensor.name} critical threshold exceeded`,
            message: `${sensor.asset.name} logged ${dto.value} ${sensor.unit} (critical limit: ${sensor.criticalMax} ${sensor.unit}).`,
            currentValue: `${dto.value} ${sensor.unit}`,
            threshold: `${sensor.criticalMax} ${sensor.unit}`,
            duration: '1 min',
            reason: 'Live IoT telemetry stream threshold breached',
            recommendedAction: 'Immediate hardware check recommended.',
            status: 'ACTIVE',
            sourceDataset: 'SYNTHETIC_LIVE',
            sourceEvidence: JSON.stringify({ deviceId: sensor.deviceId, reading: dto.value }),
            isSynthetic: true,
          },
        });
      }
    }

    return {
      success: true,
      reading,
      breached,
      severity,
      anomaly,
      alert,
    };
  }
}
