import { Injectable, NotFoundException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

@Injectable()
export class AssetsService {
  constructor(private readonly prisma: PrismaService) {}

  async findAll(query: {
    page?: number;
    limit?: number;
    search?: string;
    siteId?: string;
    category?: string;
    status?: string;
    riskLevel?: string;
    sourceDataset?: string;
  }) {
    const page = Math.max(1, Number(query.page) || 1);
    const limit = Math.min(100, Math.max(1, Number(query.limit) || 20));
    const skip = (page - 1) * limit;

    const where: any = {};

    if (query.siteId && query.siteId !== 'all') {
      where.siteId = query.siteId;
    }
    if (query.category && query.category !== 'all') {
      where.category = query.category;
    }
    if (query.status && query.status !== 'all') {
      where.status = query.status;
    }
    if (query.riskLevel && query.riskLevel !== 'all') {
      where.riskLevel = query.riskLevel;
    }
    if (query.sourceDataset && query.sourceDataset !== 'all') {
      where.sourceDataset = query.sourceDataset;
    }
    if (query.search) {
      where.OR = [
        { name: { contains: query.search } },
        { assetId: { contains: query.search } },
        { serialNumber: { contains: query.search } },
        { manufacturer: { contains: query.search } },
      ];
    }

    const [total, assets, summaryCounts] = await Promise.all([
      this.prisma.asset.count({ where }),
      this.prisma.asset.findMany({
        where,
        skip,
        take: limit,
        orderBy: [{ riskScore: 'desc' }, { healthScore: 'asc' }],
        include: {
          site: {
            select: { id: true, name: true, code: true, city: true },
          },
          _count: {
            select: {
              faults: true,
              anomalies: true,
              alerts: { where: { status: 'ACTIVE' } },
              sensors: true,
            },
          },
        },
      }),
      this.getFleetSummary(),
    ]);

    return {
      data: assets.map((a) => ({
        id: a.id,
        assetId: a.assetId,
        name: a.name,
        category: a.category,
        model: a.model,
        serialNumber: a.serialNumber,
        manufacturer: a.manufacturer,
        site: a.site,
        floor: a.floor,
        criticality: a.criticality,
        status: a.status,
        healthScore: a.healthScore,
        riskScore: a.riskScore,
        riskLevel: a.riskLevel,
        rul: a.rul,
        sourceDataset: a.sourceDataset,
        sourceRecordId: a.sourceRecordId,
        activeAlertsCount: a._count.alerts,
        faultsCount: a._count.faults,
        anomaliesCount: a._count.anomalies,
        sensorsCount: a._count.sensors,
        updatedAt: a.updatedAt,
      })),
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit),
      },
      summary: summaryCounts,
    };
  }

  async findOne(id: string) {
    const asset = await this.prisma.asset.findFirst({
      where: {
        OR: [{ id }, { assetId: id }],
      },
      include: {
        site: true,
        sensors: {
          include: {
            _count: { select: { readings: true, anomalies: true } },
          },
        },
        faults: {
          orderBy: { date: 'desc' },
          take: 10,
          include: {
            faultCategory: true,
            engineer: { select: { id: true, name: true, email: true } },
          },
        },
        anomalies: {
          orderBy: { timestamp: 'desc' },
          take: 10,
          include: { sensor: true },
        },
        alerts: {
          where: { status: 'ACTIVE' },
          orderBy: { createdAt: 'desc' },
          take: 10,
        },
        maintenances: {
          orderBy: { scheduledDate: 'desc' },
          take: 5,
          include: { engineer: { select: { id: true, name: true } } },
        },
        contractAssets: {
          include: { contract: true },
        },
      },
    });

    if (!asset) {
      throw new NotFoundException(`Asset with identifier ${id} not found.`);
    }

    return {
      ...asset,
      metadata: asset.metadata ? JSON.parse(asset.metadata) : null,
      contracts: asset.contractAssets.map((ca) => ca.contract),
    };
  }

  async getTelemetry(id: string, query: { limit?: number; sensorType?: string }) {
    const asset = await this.prisma.asset.findFirst({
      where: { OR: [{ id }, { assetId: id }] },
      select: { id: true, assetId: true, name: true },
    });

    if (!asset) throw new NotFoundException('Asset not found');

    const limit = Math.min(500, Math.max(1, Number(query.limit) || 100));

    const where: any = { assetId: asset.id };
    if (query.sensorType) {
      where.sensor = { sensorType: query.sensorType };
    }

    const readings = await this.prisma.sensorReading.findMany({
      where,
      orderBy: { timestamp: 'asc' },
      take: limit,
      include: {
        sensor: {
          select: { id: true, deviceId: true, name: true, sensorType: true, unit: true },
        },
      },
    });

    return {
      assetId: asset.assetId,
      name: asset.name,
      count: readings.length,
      readings,
    };
  }

  async getHealthHistory(id: string) {
    const asset = await this.prisma.asset.findFirst({
      where: { OR: [{ id }, { assetId: id }] },
      select: { id: true, assetId: true, healthScore: true, riskScore: true, rul: true },
    });

    if (!asset) throw new NotFoundException('Asset not found');

    const histories = await this.prisma.healthScoreHistory.findMany({
      where: { assetId: asset.id },
      orderBy: { calculatedAt: 'asc' },
    });

    // If no explicit history records yet, synthesize 7-day degradation progression based on current health
    if (histories.length === 0) {
      const simulatedPoints = [];
      const currentH = asset.healthScore;
      const initialH = Math.min(100, currentH + 18);

      for (let i = 6; i >= 0; i--) {
        const factor = (6 - i) / 6;
        const h = parseFloat((initialH - (initialH - currentH) * factor).toFixed(1));
        simulatedPoints.push({
          calculatedAt: new Date(Date.now() - i * 86400000),
          healthScore: h,
          riskScore: parseFloat((100 - h).toFixed(1)),
          rul: asset.rul,
        });
      }
      return { assetId: asset.assetId, history: simulatedPoints };
    }

    return { assetId: asset.assetId, history: histories };
  }

  private async getFleetSummary() {
    const [total, criticalRisk, downStatus, degradedStatus] = await Promise.all([
      this.prisma.asset.count(),
      this.prisma.asset.count({ where: { riskLevel: 'CRITICAL' } }),
      this.prisma.asset.count({ where: { status: 'DOWN' } }),
      this.prisma.asset.count({ where: { status: 'DEGRADED' } }),
    ]);

    const aggregates = await this.prisma.asset.aggregate({
      _avg: { healthScore: true, riskScore: true },
    });

    return {
      totalAssets: total,
      criticalRiskCount: criticalRisk,
      downCount: downStatus,
      degradedCount: degradedStatus,
      operationalCount: total - (downStatus + degradedStatus),
      avgHealthScore: parseFloat((aggregates._avg.healthScore || 0).toFixed(1)),
      avgRiskScore: parseFloat((aggregates._avg.riskScore || 0).toFixed(1)),
    };
  }
}
