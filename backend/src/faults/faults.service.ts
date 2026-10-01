import { Injectable, NotFoundException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

@Injectable()
export class FaultsService {
  constructor(private readonly prisma: PrismaService) {}

  async findAll(query: {
    page?: number;
    limit?: number;
    assetId?: string;
    failureType?: string;
    severity?: string;
    sourceDataset?: string;
    search?: string;
  }) {
    const page = Math.max(1, Number(query.page) || 1);
    const limit = Math.min(100, Math.max(1, Number(query.limit) || 20));
    const skip = (page - 1) * limit;

    const where: any = {};

    if (query.assetId) {
      where.OR = [
        { assetId: query.assetId },
        { asset: { assetId: query.assetId } },
      ];
    }
    if (query.failureType && query.failureType !== 'all') {
      where.failureType = query.failureType;
    }
    if (query.severity && query.severity !== 'all') {
      where.severity = query.severity;
    }
    if (query.sourceDataset && query.sourceDataset !== 'all') {
      where.sourceDataset = query.sourceDataset;
    }
    if (query.search) {
      where.OR = [
        { rawFault: { contains: query.search } },
        { description: { contains: query.search } },
        { resolution: { contains: query.search } },
        { faultCode: { contains: query.search } },
      ];
    }

    const [total, faults, taxonomyCounts] = await Promise.all([
      this.prisma.faultRecord.count({ where }),
      this.prisma.faultRecord.findMany({
        where,
        skip,
        take: limit,
        orderBy: { date: 'desc' },
        include: {
          asset: {
            select: { id: true, assetId: true, name: true, category: true, site: true },
          },
          faultCategory: true,
          engineer: {
            select: { id: true, name: true, email: true },
          },
        },
      }),
      this.prisma.faultRecord.groupBy({
        by: ['failureType'],
        _count: { id: true },
      }),
    ]);

    return {
      data: faults.map((f) => ({
        id: f.id,
        date: f.date,
        rawFault: f.rawFault,
        faultCode: f.faultCode,
        failureType: f.failureType,
        severity: f.severity,
        description: f.description,
        resolution: f.resolution,
        downtime: f.downtime,
        sourceDataset: f.sourceDataset,
        sourceRecordId: f.sourceRecordId,
        evidenceDetail: f.evidenceDetail ? JSON.parse(f.evidenceDetail) : null,
        isSynthetic: f.isSynthetic,
        asset: f.asset,
        faultCategory: f.faultCategory,
        engineer: f.engineer,
      })),
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit),
      },
      failureTypeBreakdown: taxonomyCounts.map((tc) => ({
        type: tc.failureType || 'UNKNOWN',
        count: tc._count.id,
      })),
    };
  }

  async getTaxonomy() {
    return this.prisma.faultCategory.findMany({
      include: {
        _count: { select: { faults: true } },
      },
    });
  }

  async normalizeFault(rawText: string) {
    if (!rawText || rawText.trim().length === 0) {
      return {
        matched: false,
        category: null,
        confidence: 0,
        explanation: 'Empty fault description provided',
      };
    }

    const categories = await this.prisma.faultCategory.findMany();
    const lower = rawText.toLowerCase();

    let bestMatch: any = null;
    let highestScore = 0;

    for (const cat of categories) {
      const keywords: string[] = cat.keywords ? JSON.parse(cat.keywords) : [];
      let matchCount = 0;

      if (lower.includes(cat.name.toLowerCase()) || lower.includes(cat.code.toLowerCase())) {
        matchCount += 3;
      }

      for (const kw of keywords) {
        if (lower.includes(kw.toLowerCase())) {
          matchCount += 1;
        }
      }

      if (matchCount > highestScore) {
        highestScore = matchCount;
        bestMatch = cat;
      }
    }

    if (bestMatch && highestScore > 0) {
      const confidence = Math.min(0.98, Math.max(0.65, highestScore * 0.22));
      return {
        matched: true,
        category: bestMatch,
        normalizedCode: bestMatch.code,
        confidence: parseFloat(confidence.toFixed(2)),
        suggestedResolution: this.getResolutionForCategory(bestMatch.code),
        explanation: `Matched category [${bestMatch.name}] based on semantic keyword overlap (${highestScore} signals).`,
      };
    }

    // Default fallback to RNF (Random Failure)
    const fallback = categories.find((c) => c.code === 'RNF') || categories[0];
    return {
      matched: false,
      category: fallback,
      normalizedCode: fallback?.code || 'RNF',
      confidence: 0.45,
      suggestedResolution: 'Perform diagnostic component isolation and hardware health check.',
      explanation: 'No direct taxonomy keyword match detected. Classified as General / Random Failure.',
    };
  }

  private getResolutionForCategory(code: string): string {
    switch (code) {
      case 'HDF':
        return 'Verify heat exchanger coolant flow rate, clean radiator fins, and replace thermal paste on heat sink.';
      case 'PWF':
        return 'Check 3-phase line voltage balance, inspect VFD drive capacitors, and verify motor torque-to-speed ratio.';
      case 'OSF':
        return 'Reduce feed rate by 15%, inspect tool geometry for excessive cutting forces, and lubricate guide rails.';
      case 'TWF':
        return 'Index cutting inserts immediately, reset tool wear accumulator, and verify spindle concentricity.';
      case 'HPC_DEGRADATION':
        return 'Perform boroscope inspection of HPC stages 4-7, inspect blade leading edges, and schedule module wash.';
      case 'FAN_DEGRADATION':
        return 'Conduct blade tip rub check, re-balance fan disc assembly, and inspect acoustic containment liner.';
      case 'BEARING_VIBRATION':
        return 'Execute FFT vibration analysis, lubricate bearing housing with high-temp grease, and inspect for cage wear.';
      default:
        return 'Execute standard diagnostic cycle and inspect mechanical linkages.';
    }
  }
}
