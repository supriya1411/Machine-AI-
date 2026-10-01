import {
  WebSocketGateway,
  WebSocketServer,
  SubscribeMessage,
  OnGatewayInit,
  OnGatewayConnection,
  OnGatewayDisconnect,
} from '@nestjs/websockets';
import { Server, Socket } from 'socket.io';
import { Logger } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

@WebSocketGateway({
  cors: {
    origin: '*',
  },
  namespace: '/ws',
})
export class EventsGateway implements OnGatewayInit, OnGatewayConnection, OnGatewayDisconnect {
  @WebSocketServer()
  server: Server;

  private readonly logger = new Logger(EventsGateway.name);
  private simulationInterval: NodeJS.Timeout | null = null;

  constructor(private readonly prisma: PrismaService) {}

  afterInit(server: Server) {
    this.logger.log('AURUM WebSocket Gateway initialized on /ws namespace.');
    this.startLiveTelemetryStream();
  }

  handleConnection(client: Socket) {
    this.logger.log(`Client connected: ${client.id}`);
    client.emit('connected', {
      status: 'ONLINE',
      gateway: 'AURUM Service Intelligence Live Gateway',
      timestamp: new Date().toISOString(),
    });
  }

  handleDisconnect(client: Socket) {
    this.logger.log(`Client disconnected: ${client.id}`);
  }

  @SubscribeMessage('subscribe:asset')
  handleSubscribeAsset(client: Socket, payload: { assetId: string }) {
    if (payload?.assetId) {
      client.join(`asset:${payload.assetId}`);
      return { status: 'SUBSCRIBED', room: `asset:${payload.assetId}` };
    }
  }

  @SubscribeMessage('subscribe:site')
  handleSubscribeSite(client: Socket, payload: { siteId: string }) {
    if (payload?.siteId) {
      client.join(`site:${payload.siteId}`);
      return { status: 'SUBSCRIBED', room: `site:${payload.siteId}` };
    }
  }

  private startLiveTelemetryStream() {
    if (this.simulationInterval) return;

    // Periodically pulse live simulated sensor reading every 5 seconds to demonstrate live telemetry
    this.simulationInterval = setInterval(async () => {
      try {
        if (!this.server) return;

        // Pick a random online sensor
        const randomSensor = await this.prisma.sensorDevice.findFirst({
          where: { status: 'ONLINE' },
          include: { asset: true },
        });

        if (randomSensor) {
          const base = randomSensor.safeMax ? (randomSensor.safeMax * 0.85) : 100;
          const fluctuation = (Math.random() - 0.5) * 5;
          const value = parseFloat((base + fluctuation).toFixed(2));

          const payload = {
            deviceId: randomSensor.deviceId,
            assetId: randomSensor.asset.assetId,
            assetName: randomSensor.asset.name,
            sensorType: randomSensor.sensorType,
            value,
            unit: randomSensor.unit,
            timestamp: new Date().toISOString(),
          };

          // Broadcast general telemetry update
          this.server.emit('telemetry:stream', payload);

          // Broadcast to specific asset room
          this.server.to(`asset:${randomSensor.asset.assetId}`).emit('telemetry:asset', payload);
        }
      } catch (err) {
        // Silently catch in simulation loop
      }
    }, 5000);
  }
}
