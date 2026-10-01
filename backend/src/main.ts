import { NestFactory } from '@nestjs/core';
import { ValidationPipe, Logger } from '@nestjs/common';
import { SwaggerModule, DocumentBuilder } from '@nestjs/swagger';
import { AppModule } from './app.module';

async function bootstrap() {
  const logger = new Logger('AurumBackend');
  const app = await NestFactory.create(AppModule);

  app.enableCors({
    origin: '*',
    methods: 'GET,HEAD,PUT,PATCH,POST,DELETE,OPTIONS',
    credentials: true,
  });

  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      transform: true,
      forbidNonWhitelisted: false,
    }),
  );

  // Setup Swagger API Documentation
  const config = new DocumentBuilder()
    .setTitle('AURUM Service Intelligence API')
    .setDescription(
      'Enterprise Service Intelligence API integrated with NASA C-MAPSS (FD001-FD004) and AI4I 2020 Predictive Maintenance datasets.',
    )
    .setVersion('1.0.0')
    .addBearerAuth()
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

  const port = process.env.PORT || 3001;
  await app.listen(port);
  logger.log(`AURUM Service Intelligence Backend running on http://localhost:${port}`);
  logger.log(`Swagger OpenAPI documentation available at http://localhost:${port}/docs`);
}

bootstrap();
