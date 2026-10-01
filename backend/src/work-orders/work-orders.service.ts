import { Injectable, NotFoundException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

@Injectable()
export class WorkOrdersService {
  constructor(private readonly prisma: PrismaService) {}

  async findAll(query: {
    status?: string;
    priority?: string;
    engineerId?: string;
    assetId?: string;
    page?: number;
    limit?: number;
  }) {
    const page = Math.max(1, Number(query.page) || 1);
    const limit = Math.min(100, Math.max(1, Number(query.limit) || 20));
    const skip = (page - 1) * limit;

    const where: any = {};
    if (query.status && query.status !== 'all') {
      where.status = query.status;
    }
    if (query.priority && query.priority !== 'all') {
      where.priority = query.priority;
    }
    if (query.engineerId && query.engineerId !== 'all') {
      where.assignedEngineerId = query.engineerId;
    }
    if (query.assetId) {
      where.OR = [
        { assetId: query.assetId },
        { asset: { assetId: query.assetId } },
      ];
    }

    const [total, items, statusCounts] = await Promise.all([
      this.prisma.workOrder.count({ where }),
      this.prisma.workOrder.findMany({
        where,
        skip,
        take: limit,
        orderBy: [{ priority: 'desc' }, { createdAt: 'desc' }],
        include: {
          asset: {
            select: { id: true, assetId: true, name: true, category: true, site: true },
          },
          assignedEngineer: {
            select: { id: true, name: true, email: true, phone: true },
          },
        },
      }),
      this.prisma.workOrder.groupBy({
        by: ['status'],
        _count: { id: true },
      }),
    ]);

    return {
      data: items,
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit),
      },
      counts: statusCounts.reduce((acc: any, curr) => {
        acc[curr.status.toLowerCase()] = curr._count.id;
        return acc;
      }, {}),
    };
  }

  async findOne(id: string) {
    const item = await this.prisma.workOrder.findUnique({
      where: { id },
      include: {
        asset: {
          include: { site: true, sensors: true },
        },
        assignedEngineer: true,
      },
    });
    if (!item) throw new NotFoundException('Work Order not found');
    return item;
  }

  async create(dto: {
    assetId: string;
    type?: string;
    priority?: string;
    assignedEngineerId?: string;
    dueDate?: string | Date;
    description: string;
  }) {
    const asset = await this.prisma.asset.findFirst({
      where: { OR: [{ id: dto.assetId }, { assetId: dto.assetId }] },
    });
    if (!asset) throw new NotFoundException('Asset not found');

    return this.prisma.workOrder.create({
      data: {
        assetId: asset.id,
        type: dto.type || 'CORRECTIVE',
        priority: dto.priority || 'HIGH',
        assignedEngineerId: dto.assignedEngineerId || null,
        dueDate: dto.dueDate ? new Date(dto.dueDate) : new Date(Date.now() + 48 * 3600000),
        status: 'OPEN',
        description: dto.description,
        isSynthetic: true,
        sourceDataset: 'SYNTHETIC',
      },
      include: { asset: true, assignedEngineer: true },
    });
  }

  async update(id: string, dto: {
    status?: string;
    assignedEngineerId?: string;
    description?: string;
  }) {
    const wo = await this.prisma.workOrder.findUnique({ where: { id } });
    if (!wo) throw new NotFoundException('Work Order not found');

    const data: any = { ...dto };
    if (dto.status === 'RESOLVED' || dto.status === 'CLOSED') {
      data.completedAt = new Date();
    }

    return this.prisma.workOrder.update({
      where: { id },
      data,
      include: { asset: true, assignedEngineer: true },
    });
  }
}
