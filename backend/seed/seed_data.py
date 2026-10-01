import os
import sys
import uuid
import random
from datetime import datetime, date, timedelta

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.orm import Session
from app.db.session import sync_engine, Base, SyncSessionLocal
from app.models.user import User, Role
from app.models.site import Site
from app.models.asset import Asset
from app.models.service_call import ServiceCall, FaultCategory
from app.models.iot import SensorDevice, SensorReading, SensorAnomaly
from app.models.maintenance import Maintenance, WorkOrder
from app.models.contract import Contract, ContractAsset
from app.models.alert import Alert
from app.models.document import Document
from app.models.audit_log import AuditLog
from app.core.security import get_password_hash

def seed_database():
    print("Beginning AURUM Service Intelligence database seeding...")
    # Ensure tables exist
    Base.metadata.create_all(bind=sync_engine)

    session: Session = SyncSessionLocal()
    try:
        # Check if already seeded
        existing_users = session.query(User).count()
        if existing_users > 0:
            print("Database already contains data. Skipping initial seed.")
            return

        # 1. Roles
        roles_data = [
            {"id": str(uuid.uuid4()), "name": "Operations Manager", "description": "Full operational overview and action authorization"},
            {"id": str(uuid.uuid4()), "name": "Field Service Engineer", "description": "Mobile work order execution and diagnostic inspection"},
            {"id": str(uuid.uuid4()), "name": "Facilities Director", "description": "High-level risk management, renewals, and asset governance"},
            {"id": str(uuid.uuid4()), "name": "IoT/Data Analyst", "description": "Telemetry threshold tuning and anomaly analysis"},
            {"id": str(uuid.uuid4()), "name": "Compliance Officer", "description": "PM cadence audit and regulatory contract compliance"},
            {"id": str(uuid.uuid4()), "name": "Administrator", "description": "System configuration, user management, and audit logs"}
        ]
        roles_map = {}
        for r in roles_data:
            role = Role(**r)
            session.add(role)
            roles_map[r["name"]] = role.id

        session.flush()

        # 2. Sites
        sites_data = [
            {"id": str(uuid.uuid4()), "name": "Metro Data Center", "code": "SITE-MDC", "city": "Ashburn", "state": "VA", "country": "USA", "latitude": 39.0438, "longitude": -77.4874},
            {"id": str(uuid.uuid4()), "name": "North Logistics Hub", "code": "SITE-NLH", "city": "Chicago", "state": "IL", "country": "USA", "latitude": 41.8781, "longitude": -87.6298},
            {"id": str(uuid.uuid4()), "name": "Silicon West Fab", "code": "SITE-SWF", "city": "San Jose", "state": "CA", "country": "USA", "latitude": 37.3382, "longitude": -121.8863},
            {"id": str(uuid.uuid4()), "name": "Austin Tech Campus", "code": "SITE-ATC", "city": "Austin", "state": "TX", "country": "USA", "latitude": 30.2672, "longitude": -97.7431},
            {"id": str(uuid.uuid4()), "name": "London Operations Hub", "code": "SITE-LOH", "city": "London", "state": "Greater London", "country": "UK", "latitude": 51.5074, "longitude": -0.1278}
        ]
        created_sites = []
        for s in sites_data:
            site = Site(**s)
            session.add(site)
            created_sites.append(site)

        session.flush()

        # 3. Users
        users_data = [
            {"name": "Sarah Jenkins", "email": "admin@aurum.ai", "role_id": roles_map["Administrator"], "site_id": created_sites[0].id},
            {"name": "Marcus Vance", "email": "marcus.vance@aurum.ai", "role_id": roles_map["Operations Manager"], "site_id": created_sites[0].id},
            {"name": "Elena Rostova", "email": "elena.rostova@aurum.ai", "role_id": roles_map["Field Service Engineer"], "site_id": created_sites[1].id},
            {"name": "David Chen", "email": "david.chen@aurum.ai", "role_id": roles_map["Facilities Director"], "site_id": created_sites[2].id},
            {"name": "Priya Sharma", "email": "priya.sharma@aurum.ai", "role_id": roles_map["IoT/Data Analyst"], "site_id": created_sites[3].id},
            {"name": "Arthur Pendelton", "email": "arthur.p@aurum.ai", "role_id": roles_map["Compliance Officer"], "site_id": created_sites[4].id}
        ]
        created_users = []
        for u in users_data:
            user = User(
                name=u["name"],
                email=u["email"],
                password_hash=get_password_hash("admin123"),
                role_id=u["role_id"],
                site_id=u["site_id"],
                status="ACTIVE"
            )
            session.add(user)
            created_users.append(user)

        session.flush()

        # 4. Fault Taxonomy
        tax_data = [
            {"code": "OVERHEATING", "name": "Overheating & Thermal Excess", "severity": "CRITICAL", "keywords": ["temp", "heat", "hot", "thermal", "boiling", "overheat"]},
            {"code": "VIBRATION_ANOMALY", "name": "Excessive Mechanical Vibration", "severity": "HIGH", "keywords": ["vibration", "shake", "shaking", "unbalance", "resonance", "wobble"]},
            {"code": "PRESSURE_DROP", "name": "Hydraulic / Refrigerant Pressure Loss", "severity": "HIGH", "keywords": ["pressure", "psi", "bar", "depressurization", "suction"]},
            {"code": "FILTER_CLOGGED", "name": "Air / Fluid Filter Restriction", "severity": "MEDIUM", "keywords": ["filter", "clog", "debris", "dp high", "restriction"]},
            {"code": "ELECTRICAL_SHORT", "name": "Electrical Trip / Phase Imbalance", "severity": "CRITICAL", "keywords": ["short", "breaker", "trip", "fuse", "voltage", "current", "ground fault"]},
            {"code": "BEARING_WEAR", "name": "Bearing Fatigue & Lubrication Failure", "severity": "HIGH", "keywords": ["bearing", "grinding", "squeal", "friction", "grease"]},
            {"code": "REFRIGERANT_LOW", "name": "Refrigerant Charge Depletion / Leak", "severity": "HIGH", "keywords": ["refrigerant", "freon", "leak", "r410a", "r134a", "charge"]},
            {"code": "SENSOR_DRIFT", "name": "Telemetry Sensor Calibration Drift", "severity": "LOW", "keywords": ["sensor", "calibration", "drift", "reading error", "false positive"]}
        ]
        tax_map = {}
        for t in tax_data:
            fc = FaultCategory(**t)
            session.add(fc)
            tax_map[t["code"]] = fc

        session.flush()

        # 5. Assets (Full Seed: 100 representative assets covering the 1,248 scale model)
        categories = ["HVAC", "Centrifugal Chiller", "Air Handling Unit (AHU)", "Dry Transformer", "Backup Diesel Generator", "Industrial Water Treatment", "Traction Elevator", "Solar Grid Inverter"]
        manufacturers = ["Carrier", "Trane", "York", "Siemens", "Cummins", "Schneider Electric", "Otis", "ABB"]

        created_assets = []
        today = date.today()

        # Key special assets for user testing (e.g. EQ-204, EQ-102)
        special_specs = [
            {"asset_id": "EQ-102", "name": "Chiller Plant Unit #02", "category": "Centrifugal Chiller", "criticality": "CRITICAL", "health": 48.0, "risk": 78.0, "risk_level": "CRITICAL"},
            {"asset_id": "EQ-204", "name": "Primary Rooftop AHU-204", "category": "Air Handling Unit (AHU)", "criticality": "HIGH", "health": 55.0, "risk": 72.0, "risk_level": "HIGH"},
            {"asset_id": "EQ-305", "name": "Emergency Generator 1200kVA", "category": "Backup Diesel Generator", "criticality": "CRITICAL", "health": 88.0, "risk": 22.0, "risk_level": "LOW"},
            {"asset_id": "EQ-412", "name": "Substation Transformer TX-1", "category": "Dry Transformer", "criticality": "CRITICAL", "health": 62.0, "risk": 58.0, "risk_level": "HIGH"},
            {"asset_id": "EQ-520", "name": "Chilled Water Pump #4", "category": "HVAC", "criticality": "MEDIUM", "health": 94.0, "risk": 12.0, "risk_level": "LOW"}
        ]

        for s in special_specs:
            asset = Asset(
                asset_id=s["asset_id"],
                name=s["name"],
                category=s["category"],
                model="AURUM-PRO-X",
                serial_number=f"SN-{s['asset_id']}-{random.randint(10000, 99999)}",
                manufacturer=random.choice(manufacturers),
                site_id=created_sites[0].id,
                floor="Roof Mechanical Yard",
                installation_date=today - timedelta(days=random.randint(400, 1800)),
                warranty_expiry=today + timedelta(days=random.randint(100, 700)),
                criticality=s["criticality"],
                status="OPERATIONAL" if s["health"] > 50 else "DEGRADED",
                health_score=s["health"],
                risk_score=s["risk"],
                risk_level=s["risk_level"],
                last_risk_assessment=datetime.utcnow()
            )
            session.add(asset)
            created_assets.append(asset)

        # Generate further assets to reach robust portfolio
        for idx in range(6, 65):
            cat = random.choice(categories)
            crit = random.choice(["LOW", "MEDIUM", "MEDIUM", "HIGH", "CRITICAL"])
            health = float(random.choice([92, 88, 85, 76, 68, 54, 42]))
            risk = round(100.0 - health + random.uniform(-5, 5), 1)
            risk = max(0.0, min(100.0, risk))
            risk_level = "CRITICAL" if risk >= 70 else ("HIGH" if risk >= 50 else ("MEDIUM" if risk >= 30 else "LOW"))

            asset = Asset(
                asset_id=f"EQ-{idx:03d}",
                name=f"{cat} #{idx:02d}",
                category=cat,
                model=f"Model-{random.randint(10, 99)}B",
                serial_number=f"SN-{idx:03d}-{random.randint(1000, 9999)}",
                manufacturer=random.choice(manufacturers),
                site_id=random.choice(created_sites).id,
                floor=f"Level {random.randint(1, 4)}",
                installation_date=today - timedelta(days=random.randint(200, 2500)),
                warranty_expiry=today + timedelta(days=random.randint(-200, 600)),
                criticality=crit,
                status="OPERATIONAL" if health >= 60 else "DEGRADED",
                health_score=health,
                risk_score=risk,
                risk_level=risk_level,
                last_risk_assessment=datetime.utcnow()
            )
            session.add(asset)
            created_assets.append(asset)

        session.flush()

        # 6. Service Calls (Realistic text and dates for MTBF and Normalization)
        sample_faults = [
            ("Compressor head temperature boiling hot, thermal trip", "OVERHEATING", 4.5),
            ("High vibration recorded on main drive shaft coupling", "VIBRATION_ANOMALY", 3.0),
            ("Refrigerant suction pressure dropped below 2.1 bar", "PRESSURE_DROP", 2.0),
            ("Air intake differential pressure switch alarmed, heavy dust", "FILTER_CLOGGED", 1.5),
            ("Circuit breaker tripped on phase B overload during startup", "ELECTRICAL_SHORT", 6.0),
            ("Audible squeal and bearing race pitting found", "BEARING_WEAR", 5.0),
            ("Low refrigerant vapor detected by sniffer probe", "REFRIGERANT_LOW", 4.0),
            ("Overheating in control cabinet fan", "OVERHEATING", 2.0),
            ("Mechanical shaking detected on secondary fan shroud", "VIBRATION_ANOMALY", 1.8),
            ("Excess heat generated on transformer terminal lugs", "OVERHEATING", 3.5)
        ]

        for asset in created_assets[:20]:
            # Generate 2 to 4 service calls over past 180 days to enable statistical MTBF
            num_calls = 3 if asset.risk_level in ("HIGH", "CRITICAL") else 2
            curr_date = datetime.utcnow() - timedelta(days=150)
            for i in range(num_calls):
                curr_date += timedelta(days=random.randint(25, 45))
                raw_text, code, dt = random.choice(sample_faults)
                fc = tax_map.get(code)
                sc = ServiceCall(
                    asset_id=asset.id,
                    date=curr_date,
                    raw_fault=raw_text,
                    normalized_fault_id=fc.id if fc else None,
                    fault_code=code,
                    severity=fc.severity if fc else "MEDIUM",
                    description=f"Dispatched technician for {raw_text}",
                    resolution=f"Replaced failed component and reset safety interlock.",
                    engineer_id=created_users[2].id,
                    downtime=dt
                )
                session.add(sc)

        session.flush()

        # 7. Telemetry Sensors & Readings
        for asset in created_assets[:25]:
            # Temperature sensor
            t_sensor = SensorDevice(
                asset_id=asset.id,
                device_id=f"SENS-TEMP-{asset.asset_id}",
                sensor_type="temperature",
                status="ONLINE",
                last_seen=datetime.utcnow(),
                configuration={
                    "safe_min": 18.0,
                    "safe_max": 24.0,
                    "warning_min": 15.0,
                    "warning_max": 28.0,
                    "critical_min": 10.0,
                    "critical_max": 35.0
                }
            )
            session.add(t_sensor)
            session.flush()

            # Readings
            base_temp = 22.0 if asset.health_score > 70 else 29.5
            now = datetime.utcnow()
            for min_ago in range(10, 0, -2):
                val = round(base_temp + random.uniform(-0.5, 0.8), 2)
                reading = SensorReading(
                    sensor_id=t_sensor.id,
                    timestamp=now - timedelta(minutes=min_ago),
                    value=val,
                    unit="°C"
                )
                session.add(reading)

            # If asset is high risk, create an active anomaly
            if asset.risk_level in ("HIGH", "CRITICAL"):
                anomaly = SensorAnomaly(
                    sensor_id=t_sensor.id,
                    timestamp=datetime.utcnow() - timedelta(minutes=18),
                    severity="CRITICAL" if asset.risk_level == "CRITICAL" else "WARNING",
                    value=31.4,
                    threshold_breached="Max Warning (28.0°C) or Critical (35.0°C)",
                    duration_minutes=18.0,
                    resolved="FALSE"
                )
                session.add(anomaly)

                # Active Alert for this anomaly
                alert = Alert(
                    type="ENVIRONMENTAL_IOT",
                    severity="CRITICAL" if asset.risk_level == "CRITICAL" else "HIGH",
                    asset_id=asset.id,
                    sensor_id=t_sensor.id,
                    title=f"High Temperature Anomaly on {asset.name}",
                    message=f"Sensor {t_sensor.device_id} reported 31.4°C, exceeding safe threshold for 18 minutes.",
                    current_value="31.4 °C",
                    threshold="28.0 °C",
                    duration="18 minutes",
                    reason="Temperature exceeded operational ceiling continuously",
                    recommended_action="Inspect cooling airflow dampers and evaporator coil",
                    status="ACTIVE"
                )
                session.add(alert)

        session.flush()

        # 8. Maintenance Schedules & Strict Cadence Demonstration (Section 11)
        # Specially craft EQ-204 with the exact violation from Section 11:
        # Required: every 90 days. Actual: Day 0, Day 30, Day 40, Day 170 -> Cadence violation!
        eq_204 = next((a for a in created_assets if a.asset_id == "EQ-204"), created_assets[0])
        base_pm_date = today - timedelta(days=200)

        # Day 0
        session.add(Maintenance(
            asset_id=eq_204.id,
            pm_type="Quarterly Comprehensive PM",
            scheduled_date=base_pm_date,
            completed_date=base_pm_date,
            status="COMPLETED",
            notes="Initial baseline maintenance executed."
        ))
        # Day 30
        session.add(Maintenance(
            asset_id=eq_204.id,
            pm_type="Quarterly Comprehensive PM",
            scheduled_date=base_pm_date + timedelta(days=30),
            completed_date=base_pm_date + timedelta(days=30),
            status="COMPLETED",
            notes="Erratic early PM execution."
        ))
        # Day 40
        session.add(Maintenance(
            asset_id=eq_204.id,
            pm_type="Quarterly Comprehensive PM",
            scheduled_date=base_pm_date + timedelta(days=40),
            completed_date=base_pm_date + timedelta(days=40),
            status="COMPLETED",
            notes="Erratic clustered PM execution."
        ))
        # Day 170 (130-day gap -> exceeds 90-day requirement!)
        session.add(Maintenance(
            asset_id=eq_204.id,
            pm_type="Quarterly Comprehensive PM",
            scheduled_date=base_pm_date + timedelta(days=170),
            completed_date=base_pm_date + timedelta(days=170),
            status="COMPLETED",
            notes="Executed after 130-day delay, violating cadence."
        ))

        # Add an overdue PM for EQ-102
        eq_102 = next((a for a in created_assets if a.asset_id == "EQ-102"), created_assets[1])
        session.add(Maintenance(
            asset_id=eq_102.id,
            pm_type="Semi-Annual Chiller Overhaul",
            scheduled_date=today - timedelta(days=14),
            status="OVERDUE",
            notes="Awaiting specialized chiller mechanical seal kit."
        ))

        # Alert for overdue PM
        session.add(Alert(
            type="OVERDUE_PM",
            severity="HIGH",
            asset_id=eq_102.id,
            title="Overdue Maintenance: Semi-Annual Chiller Overhaul",
            message="Preventive maintenance was scheduled 14 days ago and remains unfulfilled.",
            reason="Scheduled date passed without logged completion",
            recommended_action="Dispatch certified technician to execute PM",
            status="ACTIVE"
        ))

        session.flush()

        # 9. Contracts & Renewal Risk Pipeline (Section 13 & 14)
        contracts_spec = [
            {
                "contract_id": "AMC-2024-001",
                "name": "Mission-Critical HVAC & Chiller Comprehensive Service",
                "customer": "Global Logistics Corp",
                "vendor": "Johnson Controls Enterprise",
                "type": "CMC",
                "start_date": today - timedelta(days=340),
                "end_date": today + timedelta(days=25), # Expiring in 25 days!
                "value": 145000.0,
                "pm_frequency_days": 90,
                "status": "EXPIRING_SOON",
                "compliance_score": 78.5,
                "renewal_risk": "HIGH"
            },
            {
                "contract_id": "AMC-2024-002",
                "name": "Data Center Power & Backup Generator Maintenance",
                "customer": "Vertex Data Systems",
                "vendor": "Cummins Power Care",
                "type": "AMC",
                "start_date": today - timedelta(days=300),
                "end_date": today + timedelta(days=12), # Expiring in 12 days!
                "value": 88000.0,
                "pm_frequency_days": 60,
                "status": "EXPIRING_SOON",
                "compliance_score": 96.0,
                "renewal_risk": "CRITICAL" # Expiry < 15 days elevates risk
            },
            {
                "contract_id": "AMC-2024-003",
                "name": "Cleanroom Environmental AHU Maintenance Agreement",
                "customer": "BioMed Research Labs",
                "vendor": "Trane Commercial Systems",
                "type": "CMC",
                "start_date": today - timedelta(days=200),
                "end_date": today + timedelta(days=165),
                "value": 210000.0,
                "pm_frequency_days": 90,
                "status": "ACTIVE",
                "compliance_score": 94.2,
                "renewal_risk": "LOW"
            },
            {
                "contract_id": "AMC-2024-004",
                "name": "Campus Electrical Substation & Transformer Care",
                "customer": "Austin Tech Campus",
                "vendor": "Schneider Electric Services",
                "type": "AMC",
                "start_date": today - timedelta(days=180),
                "end_date": today + timedelta(days=48), # Expiring in 48 days
                "value": 120000.0,
                "pm_frequency_days": 180,
                "status": "ACTIVE",
                "compliance_score": 82.0,
                "renewal_risk": "MEDIUM"
            }
        ]

        for cs in contracts_spec:
            contract = Contract(**cs)
            session.add(contract)
            session.flush()

            # Attach assets to contract
            for asset in created_assets[:4]:
                ca = ContractAsset(contract_id=contract.id, asset_id=asset.id)
                session.add(ca)

            # Contract expiry alert if days <= 30
            days_left = (contract.end_date - today).days
            if days_left <= 30:
                alert = Alert(
                    type="CONTRACT_EXPIRY",
                    severity="CRITICAL" if days_left <= 15 else "HIGH",
                    contract_id=contract.id,
                    title=f"Contract Expiry: {contract.name}",
                    message=f"Contract {contract.contract_id} with {contract.customer} expires in {days_left} days.",
                    reason=f"Annual contract term concludes on {contract.end_date}",
                    recommended_action="Initiate formal contract renewal discussions and performance review",
                    status="ACTIVE"
                )
                session.add(alert)

        session.flush()

        # 10. Work Orders
        session.add(WorkOrder(
            asset_id=eq_102.id,
            type="CORRECTIVE",
            priority="CRITICAL",
            assigned_engineer_id=created_users[2].id,
            due_date=datetime.utcnow() + timedelta(hours=8),
            status="IN_PROGRESS",
            description="Investigate recurring thermal trip on Chiller #2 compressor head."
        ))
        session.add(WorkOrder(
            asset_id=eq_204.id,
            type="PREVENTIVE",
            priority="HIGH",
            assigned_engineer_id=created_users[2].id,
            due_date=datetime.utcnow() + timedelta(days=2),
            status="OPEN",
            description="Conduct quarterly PM inspection and resolve air flow damper restriction."
        ))

        # 11. Documents
        session.add(Document(
            filename="Chiller_EQ102_Service_Manual.pdf",
            file_path="/uploads/docs/Chiller_EQ102_Service_Manual.pdf",
            file_type="application/pdf",
            file_size_bytes=4250000,
            entity_type="ASSET",
            entity_id=eq_102.id,
            uploaded_by=created_users[0].id
        ))
        session.add(Document(
            filename="GlobalLogistics_CMC_Executed_Agreement.pdf",
            file_path="/uploads/contracts/GlobalLogistics_CMC_Agreement.pdf",
            file_type="application/pdf",
            file_size_bytes=1820000,
            entity_type="CONTRACT",
            entity_id=contracts_spec[0]["contract_id"],
            uploaded_by=created_users[0].id
        ))

        # 12. Audit Logs
        session.add(AuditLog(
            actor_id=created_users[0].id,
            action="SYSTEM_INITIALIZE",
            entity_type="SYSTEM",
            entity_id="GLOBAL",
            changes={"event": "Database bootstrap seed applied with 65 assets and operational models"}
        ))

        session.commit()
        print("AURUM Service Intelligence database seeding successfully finished!")

    except Exception as e:
        session.rollback()
        print(f"Error during seeding: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    seed_database()
