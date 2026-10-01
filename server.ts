import 'reflect-metadata';
import * as path from 'path';

let rawDbUrl = (process.env.DATABASE_URL || '').trim();
if ((rawDbUrl.startsWith('"') && rawDbUrl.endsWith('"')) || (rawDbUrl.startsWith("'") && rawDbUrl.endsWith("'"))) {
  rawDbUrl = rawDbUrl.slice(1, -1).trim();
}
// If empty, dummy localhost postgres, or not a file: URL for SQLite schema, fallback to local dev.db
if (!rawDbUrl || !rawDbUrl.startsWith('file:')) {
  process.env.DATABASE_URL = `file:${path.resolve(process.cwd(), 'backend/prisma/dev.db')}`;
} else {
  process.env.DATABASE_URL = rawDbUrl;
}

import express from 'express';
import { createServer } from 'http';
import { NestFactory } from '@nestjs/core';
import { ExpressAdapter } from '@nestjs/platform-express';
import { IoAdapter } from '@nestjs/platform-socket.io';
import { DocumentBuilder, SwaggerModule } from '@nestjs/swagger';
import { AppModule } from './backend/dist/app.module.js';
import { createServer as createViteServer } from 'vite';
import { Logger } from '@nestjs/common';

async function bootstrap() {
  const logger = new Logger('ServerBootstrap');
  const server = express();
  const httpServer = createServer(server);

  // Initialize NestJS with ExpressAdapter
  const app = await NestFactory.create(AppModule, new ExpressAdapter(server), {
    cors: true,
  });

  // Attach Socket.io WebSocket Gateway to existing HTTP server
  app.useWebSocketAdapter(new IoAdapter(httpServer));

  // Setup Swagger API Documentation
  const config = new DocumentBuilder()
    .setTitle('AURUM Service Intelligence API')
    .setDescription(
      'Enterprise Service Intelligence API integrated with NASA C-MAPSS (FD001-FD004) and AI4I 2020 Predictive Maintenance datasets.',
    )
    .setVersion('1.0.0')
    .addTag('Assets', 'Fleet equipment inventory, telemetry, and health scoring')
    .addTag('Action Center', 'Unified priority issue queue, alerts, and technician dispatch')
    .addTag('Faults', 'Standardized fault taxonomy and unstructured text normalization')
    .addTag('Maintenance', 'Preventive maintenance scheduling and cadence tracking')
    .addTag('Work Orders', 'Corrective and scheduled maintenance work orders')
    .addTag('Contracts', 'SLA agreements, renewal risks, and compliance scoring')
    .addTag('Telemetry', 'Live sensor streams and anomaly detection')
    .addTag('Analytics', 'MTBF, MTTR, fleet availability, and failure mode analysis')
    .addTag('AI Assistant', 'Evidence-grounded equipment intelligence assistant')
    .addTag('Dataset Ingestion', 'NASA C-MAPSS and AI4I dataset import pipeline')
    .build();

  const document = SwaggerModule.createDocument(app, config);
  SwaggerModule.setup('docs', app, document, {
    customSiteTitle: 'AURUM API Documentation',
  });

  // Mount Vite development server middleware for frontend SPA
  if (process.env.NODE_ENV !== 'production') {
    const vite = await createViteServer({
      server: { middlewareMode: true, hmr: false },
      appType: 'spa',
    });
    server.use((req, res, next) => {
      if (req.path.startsWith('/api') || req.path.startsWith('/docs') || req.path.startsWith('/ws')) {
        return next();
      }
      vite.middlewares(req, res, next);
    });
  } else {
    server.use(express.static(path.resolve(process.cwd(), 'dist')));
    server.get('*', (req, res, next) => {
      if (req.path.startsWith('/api') || req.path.startsWith('/docs') || req.path.startsWith('/ws')) {
        return next();
      }
      res.sendFile(path.resolve(process.cwd(), 'dist', 'index.html'));
    });
  }

  // Initialize NestJS routing and lifecycle
  await app.init();

  // Ensure dev server port runs strictly on port 3000 as required by AI Studio runtime
  const port = process.env.APP_PORT || (process.env.PORT && process.env.PORT !== '8080' ? process.env.PORT : 3000);
  httpServer.listen(Number(port), '0.0.0.0', () => {
    logger.log(`AURUM Full-Stack Server running on http://0.0.0.0:${port}`);
    logger.log(`API endpoints accessible under http://0.0.0.0:${port}/api/v1/`);
    logger.log(`Swagger documentation accessible under http://0.0.0.0:${port}/docs`);
  });
}

bootstrap();
