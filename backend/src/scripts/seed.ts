import { PrismaClient } from '@prisma/client';
import { DatasetIngestionService } from '../ingestion/dataset-ingestion.service';
import { Logger } from '@nestjs/common';

async function main() {
  const logger = new Logger('SeedCLI');
  const dbUrl = process.env.DATABASE_URL || 'file:/app/applet/backend/prisma/dev.db';
  logger.log(`Connecting to database at ${dbUrl}...`);

  const prisma = new PrismaClient({
    datasources: {
      db: { url: dbUrl },
    },
  });

  try {
    await prisma.$connect();
    logger.log('Connected to database. Initializing DatasetIngestionService...');

    const ingestionService = new DatasetIngestionService(prisma as any);
    const result = await ingestionService.runIngestion({ force: true });

    logger.log('=== Ingestion Pipeline Complete ===');
    console.log(JSON.stringify(result, null, 2));
  } catch (error) {
    logger.error('Failed to run seed script:', error);
    process.exit(1);
  } finally {
    await prisma.$disconnect();
  }
}

main();
