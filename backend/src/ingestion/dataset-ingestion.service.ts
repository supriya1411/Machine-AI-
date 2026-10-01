import { Injectable, Logger } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import * as fs from 'fs';
import * as path from 'path';
import AdmZip from 'adm-zip';
import { parse } from 'csv-parse/sync';
import * as bcrypt from 'bcryptjs';

@Injectable()
export class DatasetIngestionService {
  private readonly logger = new Logger(DatasetIngestionService.name);

  constructor(private readonly prisma: PrismaService) {}

  async runIngestion(options: { force?: boolean } = {}) {
    this.logger.log('Starting AURUM Dataset Ingestion pipeline...');
    const startTime = Date.now();

    // 1. Base Taxonomy
    await this.seedTaxonomy();

    // 2. Sites & Locations
    await this.seedSites();

    // 3. Roles & Users (Engineers)
    await this.seedRolesAndUsers();

    // 4. Ingest AI4I 2020 Predictive Maintenance Dataset
    await this.ingestAi4iDataset();

    // 5. Ingest NASA C-MAPSS Turbofan Engine Dataset
    await this.ingestCmapssDataset();

    // 6. Generate Synthetic Operational Data (Contracts, PMs, Work Orders)
    await this.generateOperationalData();

    // 7. Generate Derived Alerts
    await this.generateDerivedAlerts();

    const duration = ((Date.now() - startTime) / 1000).toFixed(2);
    this.logger.log(`AURUM Dataset Ingestion pipeline completed in ${duration}s.`);

    return this.getIngestionSummary();
  }

  private async seedTaxonomy() {
    this.logger.log('Seeding standardized fault categories taxonomy...');
    const categories = [
      {
        code: 'HDF',
        name: 'Heat Dissipation Failure',
        severity: 'HIGH',
        description: 'Insufficient temperature difference between air and process, causing thermal buildup.',
        keywords: JSON.stringify(['temperature', 'dissipation', 'overheating', 'cooling', 'thermal']),
      },
      {
        code: 'PWF',
        name: 'Power Failure',
        severity: 'CRITICAL',
        description: 'Electrical power supply interruption or motor torque/speed product threshold violation.',
        keywords: JSON.stringify(['power', 'electrical', 'blackout', 'surge', 'voltage', 'torque power']),
      },
      {
        code: 'OSF',
        name: 'Overstrain Failure',
        severity: 'CRITICAL',
        description: 'Mechanical overstrain due to excess torque and tool wear combination.',
        keywords: JSON.stringify(['overstrain', 'mechanical stress', 'excess torque', 'shear']),
      },
      {
        code: 'TWF',
        name: 'Tool Wear Failure',
        severity: 'HIGH',
        description: 'Cutting tool wear exceeded critical replacement threshold in machining.',
        keywords: JSON.stringify(['tool wear', 'cutter', 'insert', 'abrasion', 'spindle wear']),
      },
      {
        code: 'RNF',
        name: 'Random Failure',
        severity: 'MEDIUM',
        description: 'Random component failure independent of operating parameters.',
        keywords: JSON.stringify(['random', 'intermittent', 'sporadic', 'hardware fault']),
      },
      {
        code: 'HPC_DEGRADATION',
        name: 'High Pressure Compressor Degradation',
        severity: 'CRITICAL',
        description: 'Turbofan HPC blade erosion and efficiency loss over operating cycles.',
        keywords: JSON.stringify(['hpc', 'compressor', 'turbofan', 'efficiency loss', 't30', 'ps30']),
      },
      {
        code: 'FAN_DEGRADATION',
        name: 'Fan Degradation',
        severity: 'HIGH',
        description: 'Fan blade aerodynamic degradation and vibration in turbofan engine.',
        keywords: JSON.stringify(['fan', 'bypass', 'fan speed', 'nf', 'aerodynamic degradation']),
      },
      {
        code: 'BEARING_VIBRATION',
        name: 'Bearing Vibration Anomalies',
        severity: 'HIGH',
        description: 'High frequency vibration exceeding operational tolerances in rotating components.',
        keywords: JSON.stringify(['vibration', 'bearing', 'harmonic', 'oscillation', 'spindle']),
      },
      {
        code: 'OVERHEATING',
        name: 'Thermal Overheating Warning',
        severity: 'MEDIUM',
        description: 'Sensor temperatures approaching or slightly exceeding safe operating band.',
        keywords: JSON.stringify(['overheating', 'high temp', 'temperature threshold']),
      },
    ];

    for (const cat of categories) {
      await this.prisma.faultCategory.upsert({
        where: { code: cat.code },
        update: { ...cat },
        create: { ...cat, sourceDataset: 'TAXONOMY' },
      });
    }
  }

  private async seedSites() {
    this.logger.log('Seeding industrial sites...');
    const sites = [
      {
        code: 'SITE-ASH',
        name: 'Data Center Ashburn DC-1',
        address: '21100 Waxpool Road',
        city: 'Ashburn',
        state: 'VA',
        country: 'USA',
        latitude: 39.0438,
        longitude: -77.4874,
      },
      {
        code: 'SITE-CHI',
        name: 'North Logistics Hub Chicago',
        address: '4400 S Racine Ave',
        city: 'Chicago',
        state: 'IL',
        country: 'USA',
        latitude: 41.8153,
        longitude: -87.6548,
      },
      {
        code: 'SITE-SJC',
        name: 'Silicon West Semiconductor Fab',
        address: '3500 Orchard Parkway',
        city: 'San Jose',
        state: 'CA',
        country: 'USA',
        latitude: 37.3875,
        longitude: -121.9333,
      },
      {
        code: 'SITE-AUS',
        name: 'Austin Tech Campus',
        address: '11501 Domain Dr',
        city: 'Austin',
        state: 'TX',
        country: 'USA',
        latitude: 30.4015,
        longitude: -97.7242,
      },
      {
        code: 'SITE-LON',
        name: 'London Operations Hub',
        address: '25 Bank Street, Canary Wharf',
        city: 'London',
        state: 'Greater London',
        country: 'UK',
        latitude: 51.5033,
        longitude: -0.0195,
      },
    ];

    for (const site of sites) {
      await this.prisma.site.upsert({
        where: { code: site.code },
        update: { ...site },
        create: {
          ...site,
          status: 'ACTIVE',
          isSynthetic: true,
          sourceDataset: 'SYNTHETIC',
        },
      });
    }
  }

  private async seedRolesAndUsers() {
    this.logger.log('Seeding roles and engineers...');
    const roles = [
      { name: 'Admin', description: 'System Administrator with full access' },
      { name: 'Operations Manager', description: 'Facility and maintenance operations manager' },
      { name: 'Reliability Engineer', description: 'Predictive analytics and equipment reliability specialist' },
      { name: 'Field Service Engineer', description: 'Dispatched field engineer for hardware servicing' },
    ];

    const createdRoles: Record<string, string> = {};
    for (const r of roles) {
      const role = await this.prisma.role.upsert({
        where: { name: r.name },
        update: { description: r.description },
        create: { name: r.name, description: r.description },
      });
      createdRoles[r.name] = role.id;
    }

    const sites = await this.prisma.site.findMany();
    const siteMap = new Map(sites.map((s) => [s.code, s.id]));

    const defaultHash = await bcrypt.hash('aurum2026', 10);

    const users = [
      {
        email: 'alex.chen@aurum.io',
        name: 'Alex Chen',
        phone: '+1 (571) 555-0142',
        roleName: 'Operations Manager',
        siteCode: 'SITE-ASH',
      },
      {
        email: 'sarah.jenkins@aurum.io',
        name: 'Sarah Jenkins',
        phone: '+1 (312) 555-0198',
        roleName: 'Reliability Engineer',
        siteCode: 'SITE-CHI',
      },
      {
        email: 'marcus.vance@aurum.io',
        name: 'Marcus Vance',
        phone: '+1 (408) 555-0112',
        roleName: 'Field Service Engineer',
        siteCode: 'SITE-SJC',
      },
      {
        email: 'priya.sharma@aurum.io',
        name: 'Priya Sharma',
        phone: '+1 (512) 555-0187',
        roleName: 'Reliability Engineer',
        siteCode: 'SITE-AUS',
      },
      {
        email: 'david.ross@aurum.io',
        name: 'David Ross',
        phone: '+44 20 7946 0912',
        roleName: 'Field Service Engineer',
        siteCode: 'SITE-LON',
      },
      {
        email: 'admin@aurum.io',
        name: 'AURUM Admin',
        phone: '+1 (800) 555-0100',
        roleName: 'Admin',
        siteCode: 'SITE-ASH',
      },
    ];

    for (const u of users) {
      await this.prisma.user.upsert({
        where: { email: u.email },
        update: {
          name: u.name,
          phone: u.phone,
          roleId: createdRoles[u.roleName],
          roleName: u.roleName,
          siteId: siteMap.get(u.siteCode) || null,
        },
        create: {
          email: u.email,
          name: u.name,
          phone: u.phone,
          passwordHash: defaultHash,
          roleId: createdRoles[u.roleName],
          roleName: u.roleName,
          siteId: siteMap.get(u.siteCode) || null,
          isSynthetic: true,
          sourceDataset: 'SYNTHETIC',
        },
      });
    }
  }

  private async ingestAi4iDataset() {
    const csvPath = path.resolve(process.cwd(), 'backend/data/ai4i2020.csv');
    if (!fs.existsSync(csvPath)) {
      this.logger.warn(`ai4i2020.csv not found at ${csvPath}. Skipping AI4I ingestion.`);
      return;
    }

    this.logger.log(`Parsing AI4I 2020 dataset from ${csvPath}...`);
    const fileContent = fs.readFileSync(csvPath, 'utf8');
    const records = parse(fileContent, {
      columns: true,
      skip_empty_lines: true,
      trim: true,
    });

    this.logger.log(`Loaded ${records.length} raw records from AI4I 2020 dataset.`);

    const sites = await this.prisma.site.findMany();
    const engineers = await this.prisma.user.findMany({
      where: { roleName: { contains: 'Engineer' } },
    });

    const faultCategories = await this.prisma.faultCategory.findMany();
    const categoryMap = new Map(faultCategories.map((c) => [c.code, c.id]));

    // We ingest representative machines: all failure machines (339 failures) plus a balanced sample of healthy machines
    const failureRecords = records.filter((r: any) => parseInt(r['Machine failure'] || r['Machine failure\r'] || '0', 10) === 1);
    const healthyRecords = records
      .filter((r: any) => parseInt(r['Machine failure'] || r['Machine failure\r'] || '0', 10) === 0)
      .filter((_: any, idx: number) => idx % 40 === 0); // sample evenly across healthy machines

    const selectedRecords = [...failureRecords, ...healthyRecords];
    this.logger.log(`Ingesting ${selectedRecords.length} machines from AI4I (including ${failureRecords.length} failure events)...`);

    let assetCount = 0;
    let faultCount = 0;
    let anomalyCount = 0;

    for (let i = 0; i < selectedRecords.length; i++) {
      const row = selectedRecords[i];
      const udi = row['UDI'];
      const productId = row['Product ID'];
      const type = row['Type']; // L, M, H
      const airTempK = parseFloat(row['Air temperature [K]']);
      const procTempK = parseFloat(row['Process temperature [K]']);
      const speedRpm = parseFloat(row['Rotational speed [rpm]']);
      const torqueNm = parseFloat(row['Torque [Nm]']);
      const toolWearMin = parseFloat(row['Tool wear [min]']);

      const machineFailure = parseInt(row['Machine failure'] || '0', 10);
      const twf = parseInt(row['TWF'] || '0', 10);
      const hdf = parseInt(row['HDF'] || '0', 10);
      const pwf = parseInt(row['PWF'] || '0', 10);
      const osf = parseInt(row['OSF'] || '0', 10);
      const rnf = parseInt(row['RNF'] || '0', 10);

      const assetId = `EQ-AI4I-${productId}`;
      const site = sites[i % sites.length];

      // Calculate health & risk score
      let healthScore = 100.0;
      let riskScore = 0.0;
      let riskLevel = 'LOW';
      let status = 'OPERATIONAL';

      if (machineFailure === 1) {
        healthScore = Math.max(15, Math.round(35 - toolWearMin * 0.1));
        riskScore = 95.0;
        riskLevel = 'CRITICAL';
        status = 'DOWN';
      } else if (toolWearMin > 180 || torqueNm > 60 || (procTempK - airTempK) < 8.6) {
        healthScore = Math.max(55, Math.round(90 - (toolWearMin - 150) * 0.4));
        riskScore = Math.min(85, Math.round(100 - healthScore));
        riskLevel = riskScore > 65 ? 'HIGH' : 'MEDIUM';
        status = 'DEGRADED';
      } else {
        healthScore = Math.round(95 + (Math.random() * 5));
        riskScore = Math.round(100 - healthScore);
        riskLevel = 'LOW';
      }

      // Upsert Asset
      const asset = await this.prisma.asset.upsert({
        where: { assetId },
        update: {
          healthScore,
          riskScore,
          riskLevel,
          status,
          updatedAt: new Date(),
        },
        create: {
          assetId,
          name: `CNC Milling Unit ${productId} (${type}-Grade)`,
          category: 'CNC Milling Machine',
          model: `Milling-X${type}`,
          serialNumber: `SN-AI4I-${productId}-${udi}`,
          manufacturer: 'Takumi Precision Dynamics',
          siteId: site.id,
          floor: `Floor ${(i % 3) + 1}`,
          criticality: type === 'H' ? 'HIGH' : type === 'M' ? 'MEDIUM' : 'LOW',
          status,
          healthScore,
          riskScore,
          riskLevel,
          lastRiskAssessment: new Date(),
          rul: machineFailure === 1 ? 0 : Math.max(10, Math.round((250 - toolWearMin) * 8)),
          sourceDataset: 'AI4I_2020',
          sourceRecordId: `AI4I-UDI-${udi}`,
          metadata: JSON.stringify({
            productType: type,
            originalUdi: udi,
            failureFlags: { twf, hdf, pwf, osf, rnf, machineFailure },
          }),
        },
      });
      assetCount++;

      // Create Sensors for this asset
      const sensorsConfig = [
        {
          type: 'air_temperature',
          name: 'Air Temperature Sensor',
          unit: 'K',
          val: airTempK,
          safeMin: 295,
          safeMax: 301,
          warningMax: 303,
          criticalMax: 304.5,
        },
        {
          type: 'process_temperature',
          name: 'Process Temperature Sensor',
          unit: 'K',
          val: procTempK,
          safeMin: 305,
          safeMax: 312,
          warningMax: 313.5,
          criticalMax: 315,
        },
        {
          type: 'rotational_speed',
          name: 'Spindle Rotational Speed',
          unit: 'rpm',
          val: speedRpm,
          safeMin: 1350,
          safeMax: 1750,
          warningMax: 2200,
          criticalMax: 2500,
        },
        {
          type: 'torque',
          name: 'Spindle Motor Torque',
          unit: 'Nm',
          val: torqueNm,
          safeMin: 20,
          safeMax: 55,
          warningMax: 65,
          criticalMax: 72,
        },
        {
          type: 'tool_wear',
          name: 'Tool Wear Accumulator',
          unit: 'min',
          val: toolWearMin,
          safeMin: 0,
          safeMax: 180,
          warningMax: 210,
          criticalMax: 240,
        },
      ];

      for (const s of sensorsConfig) {
        const deviceId = `SENS-${assetId}-${s.type}`;
        const isBreached = s.val >= s.criticalMax || s.val <= (s.safeMin - 5);
        const isWarning = s.val >= s.warningMax;

        const sensor = await this.prisma.sensorDevice.upsert({
          where: { deviceId },
          update: {
            status: isBreached ? 'OFFLINE' : isWarning ? 'DELAYED' : 'ONLINE',
            lastSeen: new Date(),
          },
          create: {
            deviceId,
            assetId: asset.id,
            sensorType: s.type,
            name: s.name,
            unit: s.unit,
            status: isBreached ? 'OFFLINE' : isWarning ? 'DELAYED' : 'ONLINE',
            lastSeen: new Date(),
            safeMin: s.safeMin,
            safeMax: s.safeMax,
            warningMax: s.warningMax,
            criticalMax: s.criticalMax,
            sourceDataset: 'AI4I_2020',
            sourceRecordId: `AI4I-UDI-${udi}-${s.type}`,
          },
        });

        // Store reading
        await this.prisma.sensorReading.create({
          data: {
            sensorId: sensor.id,
            assetId: asset.id,
            timestamp: new Date(Date.now() - (selectedRecords.length - i) * 60000),
            value: s.val,
            unit: s.unit,
            sourceDataset: 'AI4I_2020',
            sourceRecordId: `AI4I-UDI-${udi}-${s.type}-read`,
          },
        });

        // Anomaly creation if breached
        if (isBreached || isWarning) {
          await this.prisma.sensorAnomaly.create({
            data: {
              sensorId: sensor.id,
              assetId: asset.id,
              timestamp: new Date(),
              severity: isBreached ? 'CRITICAL' : 'WARNING',
              value: s.val,
              thresholdBreached: `${s.val} ${s.unit} exceeded ${isBreached ? s.criticalMax : s.warningMax} ${s.unit}`,
              durationMinutes: Math.round(15 + Math.random() * 45),
              sourceDataset: 'AI4I_2020',
              sourceRecordId: `AI4I-UDI-${udi}-anomaly`,
              evidenceDetail: JSON.stringify({
                udi,
                sensorType: s.type,
                value: s.val,
                unit: s.unit,
                threshold: isBreached ? s.criticalMax : s.warningMax,
                allReadings: { airTempK, procTempK, speedRpm, torqueNm, toolWearMin },
              }),
            },
          });
          anomalyCount++;
        }
      }

      // If Machine Failure occurred, record exact FaultRecord linked to source evidence
      if (machineFailure === 1) {
        let failureCode = 'RNF';
        let failureTitle = 'Random Component Failure';
        if (twf === 1) {
          failureCode = 'TWF';
          failureTitle = 'Tool Wear Failure';
        } else if (hdf === 1) {
          failureCode = 'HDF';
          failureTitle = 'Heat Dissipation Failure';
        } else if (pwf === 1) {
          failureCode = 'PWF';
          failureTitle = 'Power Supply / Torque Overload Failure';
        } else if (osf === 1) {
          failureCode = 'OSF';
          failureTitle = 'Mechanical Overstrain Failure';
        }

        const categoryId = categoryMap.get(failureCode) || null;
        const engineer = engineers[i % (engineers.length || 1)] || null;

        await this.prisma.faultRecord.create({
          data: {
            assetId: asset.id,
            date: new Date(Date.now() - (i * 3600000)),
            rawFault: `${failureTitle} observed on CNC unit ${productId} during machining cycle`,
            normalizedFaultId: categoryId,
            faultCode: failureCode,
            failureType: failureCode,
            severity: 'CRITICAL',
            description: `Automatic trip triggered by ${failureTitle}. Tool wear: ${toolWearMin}min, Torque: ${torqueNm}Nm, Temp: ${procTempK}K.`,
            resolution: 'Replaced cutting insert, recalibrated spindle drive, and performed thermal inspection.',
            engineerId: engineer?.id || null,
            downtime: parseFloat((2.5 + Math.random() * 4).toFixed(1)),
            sourceDataset: 'AI4I_2020',
            sourceRecordId: `AI4I-UDI-${udi}`,
            isSynthetic: false,
            evidenceDetail: JSON.stringify({
              udi,
              productId,
              failureFlags: { twf, hdf, pwf, osf, rnf },
              telemetryAtFailure: {
                airTempK,
                procTempK,
                speedRpm,
                torqueNm,
                toolWearMin,
              },
            }),
          },
        });
        faultCount++;
      }
    }

    this.logger.log(`AI4I Ingestion completed: ${assetCount} assets, ${faultCount} faults, ${anomalyCount} anomalies.`);
  }

  private async ingestCmapssDataset() {
    this.logger.log('Inspecting and extracting C-MAPSS dataset...');
    const zipPath = path.resolve(process.cwd(), 'backend/data/CMAPSSData.zip');
    const rawDir = path.resolve(process.cwd(), 'backend/data/raw/cmapss');

    let zipEntries: { [key: string]: string } = {};

    if (fs.existsSync(zipPath)) {
      this.logger.log(`Extracting C-MAPSS files in-memory from archive: ${zipPath}`);
      const zip = new AdmZip(zipPath);
      for (const entry of zip.getEntries()) {
        if (!entry.isDirectory && entry.entryName.endsWith('.txt')) {
          const fileName = path.basename(entry.entryName);
          zipEntries[fileName] = entry.getData().toString('utf8');
        }
      }
    } else if (fs.existsSync(rawDir)) {
      this.logger.log(`Reading raw C-MAPSS files directly from ${rawDir}`);
      for (const f of fs.readdirSync(rawDir)) {
        if (f.endsWith('.txt')) {
          zipEntries[f] = fs.readFileSync(path.join(rawDir, f), 'utf8');
        }
      }
    } else {
      this.logger.warn('C-MAPSS data not found. Skipping C-MAPSS ingestion.');
      return;
    }

    const sites = await this.prisma.site.findMany();
    const faultCategories = await this.prisma.faultCategory.findMany();
    const hpcCatId = faultCategories.find((c) => c.code === 'HPC_DEGRADATION')?.id || null;
    const fanCatId = faultCategories.find((c) => c.code === 'FAN_DEGRADATION')?.id || null;

    // Process all sub-datasets: FD001, FD002, FD003, FD004
    const subDatasets = ['FD001', 'FD002', 'FD003', 'FD004'];

    let totalEngines = 0;
    let totalCmapssFaults = 0;

    for (const sub of subDatasets) {
      const trainKey = `train_${sub}.txt`;
      const rulKey = `RUL_${sub}.txt`;
      const trainData = zipEntries[trainKey];
      const rulData = zipEntries[rulKey];

      if (!trainData) {
        this.logger.warn(`File ${trainKey} not found in C-MAPSS archive.`);
        continue;
      }

      this.logger.log(`Processing C-MAPSS ${sub} trajectories...`);
      const lines = trainData.split('\n').filter((l) => l.trim().length > 0);

      // Parse unit trajectories: unitNumber -> Array of cycle rows
      const unitMap = new Map<number, any[]>();
      for (const line of lines) {
        const parts = line.trim().split(/\s+/).map(Number);
        if (parts.length < 26) continue;
        const [unit, cycle, s1, s2, s3, ...sensors] = parts;
        if (!unitMap.has(unit)) {
          unitMap.set(unit, []);
        }
        unitMap.get(unit)!.push({
          cycle,
          settings: [s1, s2, s3],
          sensors,
        });
      }

      // Read RUL test values if available
      const rulValues = rulData
        ? rulData
            .split('\n')
            .map((l) => parseInt(l.trim(), 10))
            .filter((n) => !isNaN(n))
        : [];

      // Import representative engines from this sub-dataset (e.g. first 25 engines per subset to maintain high fidelity)
      const unitsToImport = Array.from(unitMap.keys()).slice(0, 25);

      for (const unitId of unitsToImport) {
        const cycles = unitMap.get(unitId)!;
        const maxCycle = Math.max(...cycles.map((c) => c.cycle));
        const finalCycle = cycles.find((c) => c.cycle === maxCycle)!;
        const initialCycle = cycles[0];

        const assetId = `EQ-CMAPSS-${sub}-${String(unitId).padStart(3, '0')}`;
        const site = sites[(unitId + sub.charCodeAt(4)) % sites.length];

        // Degradation dynamics:
        // C-MAPSS engines run until terminal failure at maxCycle.
        // Final cycle RUL = 0.
        const currentRul = 0; // Training engine at terminal lifecycle state
        const healthScore = 20.0 + Math.random() * 8; // Degraded state
        const riskScore = 92.0;
        const riskLevel = 'CRITICAL';
        const status = 'DOWN';

        const asset = await this.prisma.asset.upsert({
          where: { assetId },
          update: {
            healthScore,
            riskScore,
            riskLevel,
            status,
            rul: currentRul,
            updatedAt: new Date(),
          },
          create: {
            assetId,
            name: `Turbofan Engine ${sub}-U${unitId}`,
            category: 'Turbofan Engine',
            model: `GE90-CMAPSS-${sub}`,
            serialNumber: `SN-CMAPSS-${sub}-${unitId}`,
            manufacturer: 'AeroPower Propulsion Systems',
            siteId: site.id,
            floor: 'Test Bay Alpha',
            criticality: 'CRITICAL',
            status,
            healthScore,
            riskScore,
            riskLevel,
            lastRiskAssessment: new Date(),
            rul: currentRul,
            sourceDataset: 'CMAPSS',
            sourceRecordId: `${sub}-unit-${unitId}`,
            metadata: JSON.stringify({
              subDataset: sub,
              unitId,
              totalCyclesRun: maxCycle,
              operatingConditions: sub === 'FD001' || sub === 'FD003' ? 'Sea Level' : 'Six Operating Modes',
              primaryFaultMode: sub === 'FD001' || sub === 'FD002' ? 'HPC Degradation' : 'HPC & Fan Degradation',
            }),
          },
        });
        totalEngines++;

        // Key C-MAPSS sensors:
        // s2: T24 - Total temperature at LPC outlet (°R)
        // s3: T30 - Total temperature at HPC outlet (°R)
        // s4: T50 - Total temperature at LPT outlet (°R)
        // s7: P30 - Total pressure at HPC outlet (psia)
        // s8: Nf - Physical fan speed (rpm)
        // s9: Nc - Physical core speed (rpm)
        // s11: Ps30 - Static pressure at HPC outlet (psia)
        // s12: phi - Ratio of fuel flow to Ps30 (pps/psi)
        const sensorConfigs = [
          { index: 1, type: 't24_temp', name: 'LPC Outlet Temperature', unit: '°R', safeMax: 643.5, critMax: 644.5 },
          { index: 2, type: 't30_temp', name: 'HPC Outlet Temperature', unit: '°R', safeMax: 1590, critMax: 1605 },
          { index: 3, type: 't50_temp', name: 'LPT Outlet Temperature', unit: '°R', safeMax: 1410, critMax: 1425 },
          { index: 6, type: 'p30_pres', name: 'HPC Outlet Total Pressure', unit: 'psia', safeMax: 554, critMax: 558 },
          { index: 7, type: 'nf_speed', name: 'Fan Physical Speed', unit: 'rpm', safeMax: 2388.5, critMax: 2390 },
          { index: 8, type: 'nc_speed', name: 'Core Physical Speed', unit: 'rpm', safeMax: 9065, critMax: 9080 },
          { index: 10, type: 'ps30_pres', name: 'HPC Outlet Static Pressure', unit: 'psia', safeMax: 47.6, critMax: 48.0 },
        ];

        for (const sc of sensorConfigs) {
          const deviceId = `SENS-${assetId}-${sc.type}`;
          const finalVal = finalCycle.sensors[sc.index];
          const initialVal = initialCycle.sensors[sc.index];

          const sensor = await this.prisma.sensorDevice.upsert({
            where: { deviceId },
            update: {
              status: finalVal >= sc.critMax ? 'OFFLINE' : 'ONLINE',
              lastSeen: new Date(),
            },
            create: {
              deviceId,
              assetId: asset.id,
              sensorType: sc.type,
              name: sc.name,
              unit: sc.unit,
              status: finalVal >= sc.critMax ? 'OFFLINE' : 'ONLINE',
              lastSeen: new Date(),
              safeMax: sc.safeMax,
              criticalMax: sc.critMax,
              sourceDataset: 'CMAPSS',
              sourceRecordId: `${sub}-u${unitId}-${sc.type}`,
            },
          });

          // Ingest telemetry samples: initial cycle, midpoint cycle, and final degradation cycle
          const sampleCycles = [
            initialCycle,
            cycles[Math.floor(cycles.length / 2)],
            finalCycle,
          ];

          for (const c of sampleCycles) {
            await this.prisma.sensorReading.create({
              data: {
                sensorId: sensor.id,
                assetId: asset.id,
                timestamp: new Date(Date.now() - (maxCycle - c.cycle) * 3600000),
                cycle: c.cycle,
                value: parseFloat(c.sensors[sc.index].toFixed(2)),
                unit: sc.unit,
                setting1: c.settings[0],
                setting2: c.settings[1],
                setting3: c.settings[2],
                sourceDataset: 'CMAPSS',
                sourceRecordId: `${sub}-u${unitId}-c${c.cycle}`,
              },
            });
          }

          // Create anomaly on final cycle if critical threshold exceeded
          if (finalVal >= sc.critMax) {
            await this.prisma.sensorAnomaly.create({
              data: {
                sensorId: sensor.id,
                assetId: asset.id,
                timestamp: new Date(),
                severity: 'CRITICAL',
                value: finalVal,
                thresholdBreached: `${finalVal} ${sc.unit} exceeded critical threshold ${sc.critMax} ${sc.unit}`,
                durationMinutes: 120,
                sourceDataset: 'CMAPSS',
                sourceRecordId: `${sub}-u${unitId}-c${maxCycle}-anom`,
                evidenceDetail: JSON.stringify({
                  subDataset: sub,
                  unitId,
                  cycle: maxCycle,
                  sensorType: sc.type,
                  initialValue: initialVal,
                  finalValue: finalVal,
                  delta: parseFloat((finalVal - initialVal).toFixed(2)),
                }),
              },
            });
          }
        }

        // Terminal degradation fault record linking to dataset evidence
        const faultCatId = (sub === 'FD003' || sub === 'FD004') && (unitId % 2 === 0) ? fanCatId : hpcCatId;
        const faultCode = faultCatId === fanCatId ? 'FAN_DEGRADATION' : 'HPC_DEGRADATION';

        await this.prisma.faultRecord.create({
          data: {
            assetId: asset.id,
            date: new Date(Date.now() - 86400000),
            rawFault: `Terminal ${faultCode.replace('_', ' ')} reached at cycle ${maxCycle}`,
            normalizedFaultId: faultCatId,
            faultCode,
            failureType: faultCode,
            severity: 'CRITICAL',
            description: `Engine reached run-to-failure boundary at cycle ${maxCycle}. Severe thermal rise in HPC Outlet (T30: ${finalCycle.sensors[2]}°R) and drop in pressure ratio.`,
            resolution: 'Disassembled turbine module for hot section overhaul and HPC blade ring replacement.',
            downtime: 48.0,
            sourceDataset: 'CMAPSS',
            sourceRecordId: `${sub}-unit-${unitId}-failure`,
            isSynthetic: false,
            evidenceDetail: JSON.stringify({
              subDataset: sub,
              unitId,
              terminalCycle: maxCycle,
              failureMode: faultCode,
              operatingSettings: finalCycle.settings,
              finalReadings: {
                T24: finalCycle.sensors[1],
                T30: finalCycle.sensors[2],
                T50: finalCycle.sensors[3],
                P30: finalCycle.sensors[6],
                Nf: finalCycle.sensors[7],
                Nc: finalCycle.sensors[8],
                Ps30: finalCycle.sensors[10],
              },
            }),
          },
        });
        totalCmapssFaults++;
      }
    }

    this.logger.log(`C-MAPSS Ingestion completed: ${totalEngines} engines imported, ${totalCmapssFaults} terminal faults recorded.`);
  }

  private async generateOperationalData() {
    this.logger.log('Generating synthetic operational contracts, PM schedules, and work orders...');
    const assets = await this.prisma.asset.findMany();
    const engineers = await this.prisma.user.findMany({
      where: { roleName: { contains: 'Engineer' } },
    });

    const contractsData = [
      {
        contractId: 'AMC-2024-ASH-01',
        name: 'Enterprise Precision Machining & Turbine Maintenance Agreement',
        customer: 'Global Tech Facilities LLC',
        vendor: 'AeroPower & Takumi Engineering Services',
        type: 'AMC',
        startDate: new Date('2024-01-01'),
        endDate: new Date(Date.now() + 18 * 86400000), // Expiring in 18 days!
        value: 450000,
        pmFrequencyDays: 90,
        status: 'EXPIRING_SOON',
        complianceScore: 78.5,
        renewalRisk: 'CRITICAL',
      },
      {
        contractId: 'CMC-2025-CHI-02',
        name: 'Comprehensive Midwest Logistics Equipment Coverage',
        customer: 'Midwest Intermodal Systems',
        vendor: 'Industrial Reliability Solutions',
        type: 'CMC',
        startDate: new Date('2024-06-01'),
        endDate: new Date(Date.now() + 120 * 86400000),
        value: 620000,
        pmFrequencyDays: 60,
        status: 'ACTIVE',
        complianceScore: 94.2,
        renewalRisk: 'LOW',
      },
      {
        contractId: 'AMC-2025-SJC-03',
        name: 'Silicon Fab Cleanroom Tooling Critical SLA',
        customer: 'Silicon West Foundry Inc',
        vendor: 'Semiconductor Precision Maintenance',
        type: 'AMC',
        startDate: new Date('2024-03-15'),
        endDate: new Date(Date.now() + 25 * 86400000), // Expiring in 25 days!
        value: 890000,
        pmFrequencyDays: 30,
        status: 'EXPIRING_SOON',
        complianceScore: 82.0,
        renewalRisk: 'HIGH',
      },
      {
        contractId: 'CMC-2026-LON-04',
        name: 'London Financial Hub Critical Infrastructure Agreement',
        customer: 'Canary Wharf Utilities Ltd',
        vendor: 'AeroPower Europe Support',
        type: 'CMC',
        startDate: new Date('2025-01-01'),
        endDate: new Date(Date.now() + 300 * 86400000),
        value: 520000,
        pmFrequencyDays: 90,
        status: 'ACTIVE',
        complianceScore: 98.0,
        renewalRisk: 'LOW',
      },
    ];

    for (const c of contractsData) {
      const contract = await this.prisma.contract.upsert({
        where: { contractId: c.contractId },
        update: { ...c },
        create: {
          ...c,
          isSynthetic: true,
          sourceDataset: 'SYNTHETIC',
        },
      });

      // Link subset of assets to this contract
      const assetsForContract = assets.slice(0, 15);
      for (const a of assetsForContract) {
        await this.prisma.contractAsset.upsert({
          where: {
            contractId_assetId: {
              contractId: contract.id,
              assetId: a.id,
            },
          },
          update: {},
          create: {
            contractId: contract.id,
            assetId: a.id,
            isSynthetic: true,
          },
        });
      }
    }

    // Generate Preventative Maintenance (PM) milestones, including OVERDUE cadence milestones
    this.logger.log('Generating PM schedules and cadence violation records...');
    for (let i = 0; i < Math.min(assets.length, 40); i++) {
      const a = assets[i];
      const isOverdue = i % 4 === 0; // 25% of sampled assets have overdue PM
      const eng = engineers[i % (engineers.length || 1)] || null;

      const scheduledDate = isOverdue
        ? new Date(Date.now() - (7 + (i % 14)) * 86400000) // 7-20 days ago
        : new Date(Date.now() + (10 + (i % 60)) * 86400000);

      await this.prisma.maintenance.create({
        data: {
          assetId: a.id,
          pmType: a.category === 'Turbofan Engine' ? 'Turbine Boroscope & Hot Section PM' : 'Spindle Calibration & Thermal PM',
          scheduledDate,
          completedDate: isOverdue ? null : (i % 3 === 0 ? new Date(Date.now() - 30 * 86400000) : null),
          status: isOverdue ? 'OVERDUE' : (i % 3 === 0 ? 'COMPLETED' : 'SCHEDULED'),
          cadenceDays: 90,
          engineerId: eng?.id || null,
          notes: isOverdue
            ? 'CRITICAL CADENCE VIOLATION: Preventive maintenance window expired without technician sign-off.'
            : 'Scheduled quarterly preventive inspection in accordance with manufacturer SLA.',
          isSynthetic: true,
          sourceDataset: 'SYNTHETIC',
        },
      });
    }

    // Generate Work Orders linked to critical assets/faults
    this.logger.log('Generating Work Orders for active issues...');
    const criticalAssets = assets.filter((a) => a.riskLevel === 'CRITICAL' || a.status === 'DOWN').slice(0, 20);

    for (let i = 0; i < criticalAssets.length; i++) {
      const ca = criticalAssets[i];
      const eng = engineers[i % (engineers.length || 1)] || null;

      await this.prisma.workOrder.create({
        data: {
          assetId: ca.id,
          type: 'CORRECTIVE',
          priority: 'CRITICAL',
          assignedEngineerId: eng?.id || null,
          dueDate: new Date(Date.now() + 48 * 3600000),
          status: i % 2 === 0 ? 'OPEN' : 'IN_PROGRESS',
          description: `Emergency repair dispatch for ${ca.name}: Severe degradation / failure detected in telemetry data. Inspect sensor anomalies and restore operational integrity.`,
          isSynthetic: true,
          sourceDataset: 'SYNTHETIC',
        },
      });
    }
  }

  private async generateDerivedAlerts() {
    this.logger.log('Generating derived Action Center alerts linked to evidence...');
    // Clean up existing alerts to make regeneration idempotent
    await this.prisma.alert.deleteMany();

    // 1. Alerts from critical anomalies (Real Telemetry Derived)
    const anomalies = await this.prisma.sensorAnomaly.findMany({
      where: { severity: 'CRITICAL' },
      include: { asset: true, sensor: true },
      take: 25,
    });

    for (const anom of anomalies) {
      await this.prisma.alert.create({
        data: {
          type: 'ENVIRONMENTAL_IOT',
          severity: 'CRITICAL',
          assetId: anom.assetId,
          sensorId: anom.sensorId,
          title: `Sensor Breach: ${anom.sensor?.name || 'Telemetry'} out of bounds`,
          message: `${anom.asset?.name || 'Asset'} recorded critical threshold breach: ${anom.thresholdBreached}.`,
          currentValue: `${anom.value} ${anom.sensor?.unit || ''}`,
          threshold: anom.thresholdBreached,
          duration: `${anom.durationMinutes} mins`,
          reason: 'Operational parameter exceeded manufacturer safe envelope.',
          recommendedAction: 'Throttle rotational speed, verify cooling system, and dispatch technician.',
          status: 'ACTIVE',
          sourceDataset: anom.sourceDataset,
          sourceRecordId: anom.sourceRecordId,
          sourceEvidence: anom.evidenceDetail,
          isSynthetic: false,
          createdAt: anom.timestamp,
        },
      });
    }

    // 2. Alerts from Overdue PMs (Derived Operational)
    const overduePms = await this.prisma.maintenance.findMany({
      where: { status: 'OVERDUE' },
      include: { asset: true },
      take: 15,
    });

    for (const pm of overduePms) {
      const daysOverdue = Math.floor((Date.now() - pm.scheduledDate.getTime()) / 86400000);
      await this.prisma.alert.create({
        data: {
          type: 'OVERDUE_PM',
          severity: daysOverdue > 14 ? 'CRITICAL' : 'HIGH',
          assetId: pm.assetId,
          title: `Overdue Preventive Maintenance: ${pm.pmType}`,
          message: `Asset ${pm.asset?.name || pm.assetId} is ${daysOverdue} days past scheduled PM inspection date.`,
          currentValue: `${daysOverdue} days overdue`,
          threshold: '0 days grace period',
          duration: `${daysOverdue} days`,
          reason: 'Missed maintenance cadence creates heightened risk of unpredicted failure.',
          recommendedAction: 'Schedule immediate technician dispatch to clear compliance violation.',
          status: 'ACTIVE',
          sourceDataset: 'SYNTHETIC',
          sourceRecordId: pm.id,
          sourceEvidence: JSON.stringify({
            pmId: pm.id,
            scheduledDate: pm.scheduledDate,
            daysOverdue,
            assetName: pm.asset?.name,
          }),
          isSynthetic: true,
          createdAt: new Date(),
        },
      });
    }

    // 3. Alerts from Expiring Contracts
    const expiringContracts = await this.prisma.contract.findMany({
      where: { status: 'EXPIRING_SOON' },
    });

    for (const c of expiringContracts) {
      const daysRemaining = Math.max(0, Math.floor((c.endDate.getTime() - Date.now()) / 86400000));
      await this.prisma.alert.create({
        data: {
          type: 'CONTRACT_EXPIRY',
          severity: daysRemaining <= 20 ? 'CRITICAL' : 'HIGH',
          contractId: c.id,
          title: `Contract Expiry Warning: ${c.contractId}`,
          message: `Service agreement "${c.name}" with ${c.customer} expires in ${daysRemaining} days.`,
          currentValue: `${daysRemaining} days left`,
          threshold: '30-day threshold',
          duration: `${daysRemaining} days`,
          reason: 'Service Level Agreement lapse will suspend on-site coverage and technician dispatch.',
          recommendedAction: 'Initiate vendor renewal approval workflow and review SLA terms.',
          status: 'ACTIVE',
          sourceDataset: 'SYNTHETIC',
          sourceRecordId: c.contractId,
          sourceEvidence: JSON.stringify({
            contractId: c.contractId,
            endDate: c.endDate,
            daysRemaining,
            renewalRisk: c.renewalRisk,
          }),
          isSynthetic: true,
          createdAt: new Date(),
        },
      });
    }

    this.logger.log('Alert generation completed.');
  }

  async getIngestionSummary() {
    const [
      sites,
      assets,
      sensors,
      readings,
      faults,
      anomalies,
      contracts,
      maintenances,
      workOrders,
      alerts,
    ] = await Promise.all([
      this.prisma.site.count(),
      this.prisma.asset.count(),
      this.prisma.sensorDevice.count(),
      this.prisma.sensorReading.count(),
      this.prisma.faultRecord.count(),
      this.prisma.sensorAnomaly.count(),
      this.prisma.contract.count(),
      this.prisma.maintenance.count(),
      this.prisma.workOrder.count(),
      this.prisma.alert.count(),
    ]);

    const datasetCounts = await this.prisma.asset.groupBy({
      by: ['sourceDataset'],
      _count: { id: true },
    });

    return {
      status: 'SUCCESS',
      summary: {
        sites,
        assets,
        sensors,
        sensorReadings: readings,
        faults,
        anomalies,
        contracts,
        maintenances,
        workOrders,
        alerts,
      },
      datasetBreakdown: datasetCounts.map((d) => ({
        sourceDataset: d.sourceDataset,
        count: d._count.id,
      })),
      timestamp: new Date().toISOString(),
    };
  }
}
