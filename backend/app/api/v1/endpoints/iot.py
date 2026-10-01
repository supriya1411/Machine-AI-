from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, or_
from typing import List, Optional
from datetime import datetime, timedelta

from app.db.session import get_db
from app.models.iot import SensorDevice, SensorReading, SensorAnomaly
from app.models.asset import Asset
from app.models.site import Site
from app.models.alert import Alert
from app.schemas.iot import (
    SensorDeviceResponse,
    SensorReadingResponse,
    SensorReadingCreate,
    SensorAnomalyResponse,
    IngestReadingResponse,
    ThresholdConfig
)
from app.schemas.common import ApiResponse
from app.services.iot_engine import IoTEngine

router = APIRouter()

@router.get("/sensors", response_model=ApiResponse[List[SensorDeviceResponse]], summary="List Telemetry Sensors with Real-Time Status")
async def list_sensors(
    sensor_type: Optional[str] = Query(None, description="Filter: temperature, humidity, vibration, power"),
    status: Optional[str] = Query(None, description="ONLINE, OFFLINE, DELAYED, STALE, NO_SENSOR"),
    asset_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(SensorDevice, Asset.name.label("asset_name"), Site.name.label("site_name")).join(Asset, SensorDevice.asset_id == Asset.id).outerjoin(Site, Asset.site_id == Site.id)

    if sensor_type:
        stmt = stmt.where(SensorDevice.sensor_type == sensor_type.lower())
    if status:
        stmt = stmt.where(SensorDevice.status == status.upper())
    if asset_id:
        stmt = stmt.where(SensorDevice.asset_id == asset_id)

    res = await db.execute(stmt)
    rows = res.all()

    sensors = []
    for row in rows:
        sensor, asset_name, site_name = row[0], row[1], row[2]

        # Get latest reading
        read_stmt = select(SensorReading).where(SensorReading.sensor_id == sensor.id).order_by(desc(SensorReading.timestamp)).limit(1)
        read_res = await db.execute(read_stmt)
        latest_reading = read_res.scalar_one_or_none()

        computed_status = IoTEngine.determine_sensor_status(sensor.last_seen)
        config = sensor.configuration or {}

        thresholds = ThresholdConfig(
            safe_min=config.get("safe_min", 18.0),
            safe_max=config.get("safe_max", 24.0),
            warning_min=config.get("warning_min", 15.0),
            warning_max=config.get("warning_max", 28.0),
            critical_min=config.get("critical_min", 10.0),
            critical_max=config.get("critical_max", 35.0)
        )

        sensors.append(SensorDeviceResponse(
            id=sensor.id,
            asset_id=sensor.asset_id,
            device_id=sensor.device_id,
            sensor_type=sensor.sensor_type,
            status=computed_status,
            last_seen=sensor.last_seen,
            configuration=config,
            asset_name=asset_name,
            site_name=site_name,
            current_value=latest_reading.value if latest_reading else None,
            unit=latest_reading.unit if latest_reading else ("°C" if sensor.sensor_type == "temperature" else "%"),
            thresholds=thresholds
        ))

    return ApiResponse(success=True, data=sensors, meta={"total_sensors": len(sensors)})

@router.get("/sensors/{id}", response_model=ApiResponse[SensorDeviceResponse], summary="Get Sensor Detail and Threshold Configuration")
async def get_sensor_detail(id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(SensorDevice, Asset.name.label("asset_name"), Site.name.label("site_name")).join(Asset, SensorDevice.asset_id == Asset.id).outerjoin(Site, Asset.site_id == Site.id).where(or_(SensorDevice.id == id, SensorDevice.device_id == id))
    res = await db.execute(stmt)
    row = res.first()
    if not row:
        raise HTTPException(status_code=404, detail="Sensor not found")

    sensor, asset_name, site_name = row[0], row[1], row[2]
    read_stmt = select(SensorReading).where(SensorReading.sensor_id == sensor.id).order_by(desc(SensorReading.timestamp)).limit(1)
    read_res = await db.execute(read_stmt)
    latest_reading = read_res.scalar_one_or_none()

    config = sensor.configuration or {}
    thresholds = ThresholdConfig(
        safe_min=config.get("safe_min", 18.0),
        safe_max=config.get("safe_max", 24.0),
        warning_min=config.get("warning_min", 15.0),
        warning_max=config.get("warning_max", 28.0),
        critical_min=config.get("critical_min", 10.0),
        critical_max=config.get("critical_max", 35.0)
    )

    resp = SensorDeviceResponse(
        id=sensor.id,
        asset_id=sensor.asset_id,
        device_id=sensor.device_id,
        sensor_type=sensor.sensor_type,
        status=IoTEngine.determine_sensor_status(sensor.last_seen),
        last_seen=sensor.last_seen,
        configuration=config,
        asset_name=asset_name,
        site_name=site_name,
        current_value=latest_reading.value if latest_reading else None,
        unit=latest_reading.unit if latest_reading else ("°C" if sensor.sensor_type == "temperature" else "%"),
        thresholds=thresholds
    )
    return ApiResponse(success=True, data=resp)

@router.get("/readings", response_model=ApiResponse[List[SensorReadingResponse]], summary="Query Historical Sensor Telemetry Stream")
async def get_readings(
    sensor_id: str = Query(..., description="Sensor Device UUID"),
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(SensorReading).where(SensorReading.sensor_id == sensor_id).order_by(desc(SensorReading.timestamp)).limit(limit)
    res = await db.execute(stmt)
    readings = res.scalars().all()
    items = [SensorReadingResponse.model_validate(r) for r in readings]
    return ApiResponse(success=True, data=items)

@router.get("/anomalies", response_model=ApiResponse[List[SensorAnomalyResponse]], summary="Query Detected IoT Threshold Breaches")
async def get_anomalies(
    severity: Optional[str] = Query(None, description="WARNING, CRITICAL"),
    resolved: Optional[str] = Query(None, description="TRUE, FALSE"),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(SensorAnomaly, SensorDevice.device_id, Asset.id.label("asset_id"), Asset.name.label("asset_name")).join(SensorDevice, SensorAnomaly.sensor_id == SensorDevice.id).join(Asset, SensorDevice.asset_id == Asset.id).order_by(desc(SensorAnomaly.timestamp))

    if severity:
        stmt = stmt.where(SensorAnomaly.severity == severity.upper())
    if resolved:
        stmt = stmt.where(SensorAnomaly.resolved == resolved.upper())

    res = await db.execute(stmt)
    rows = res.all()

    items = []
    for row in rows:
        anom, dev_id, a_id, a_name = row[0], row[1], row[2], row[3]
        items.append(SensorAnomalyResponse(
            id=anom.id,
            sensor_id=anom.sensor_id,
            device_id=dev_id,
            asset_id=a_id,
            asset_name=a_name,
            timestamp=anom.timestamp,
            severity=anom.severity,
            value=anom.value,
            unit="°C",
            threshold_breached=anom.threshold_breached,
            duration_minutes=anom.duration_minutes,
            resolved=anom.resolved
        ))

    return ApiResponse(success=True, data=items, meta={"total_anomalies": len(items)})

@router.post("/readings", response_model=ApiResponse[IngestReadingResponse], summary="Ingest Telemetry Reading & Trigger Threshold Engine")
async def ingest_reading(payload: SensorReadingCreate, db: AsyncSession = Depends(get_db)):
    """
    Core IoT Ingestion Pipeline (Flow 9 & 10):
    Sensor Reading -> Threshold Evaluation -> Anomaly Detection -> Deduplicated Alert -> Asset Risk Update -> Recommended Action
    """
    # 1. Fetch sensor & asset
    s_stmt = select(SensorDevice, Asset).join(Asset, SensorDevice.asset_id == Asset.id).where(SensorDevice.id == payload.sensor_id)
    s_res = await db.execute(s_stmt)
    row = s_res.first()
    if not row:
        raise HTTPException(status_code=404, detail="Sensor device not found")

    sensor, asset = row[0], row[1]

    # Record reading
    now = datetime.utcnow()
    reading = SensorReading(
        sensor_id=sensor.id,
        value=payload.value,
        unit=payload.unit,
        timestamp=payload.timestamp or now
    )
    db.add(reading)

    sensor.last_seen = now
    sensor.status = "ONLINE"

    # 2. Evaluate against configurable thresholds
    eval_result = IoTEngine.evaluate_reading(
        sensor_type=sensor.sensor_type,
        value=payload.value,
        config=sensor.configuration or {}
    )

    anomaly_detected = eval_result["is_anomaly"]
    alert_triggered = False
    alert_id = None
    action = eval_result.get("recommended_action")

    if anomaly_detected:
        # Create Anomaly record
        anomaly = SensorAnomaly(
            sensor_id=sensor.id,
            timestamp=now,
            severity=eval_result["severity"],
            value=payload.value,
            threshold_breached=eval_result["threshold_breached"],
            duration_minutes=1.0,
            resolved="FALSE"
        )
        db.add(anomaly)

        # Check for continuing condition / deduplication
        # If an ACTIVE alert already exists for this sensor/asset, update it instead of creating duplicates
        exist_stmt = select(Alert).where(
            Alert.sensor_id == sensor.id,
            Alert.status == "ACTIVE"
        )
        exist_res = await db.execute(exist_stmt)
        existing_alert = exist_res.scalar_one_or_none()

        if existing_alert:
            existing_alert.current_value = f"{payload.value} {payload.unit}"
            existing_alert.duration = "Ongoing condition"
            alert_id = existing_alert.id
            alert_triggered = True
        else:
            # Create new Alert
            new_alert = Alert(
                type="IOT_THRESHOLD",
                severity=eval_result["severity"],
                asset_id=asset.id,
                sensor_id=sensor.id,
                title=f"{eval_result['severity']} {sensor.sensor_type.capitalize()} Breach on {asset.name}",
                message=f"Sensor {sensor.device_id} detected {payload.value} {payload.unit}, breaching {eval_result['threshold_breached']}.",
                current_value=f"{payload.value} {payload.unit}",
                threshold=eval_result["threshold_breached"],
                duration="Just detected",
                reason=f"Operating parameter exceeded safe limits: {eval_result['threshold_breached']}",
                recommended_action=action or "Inspect sensor subsystem",
                status="ACTIVE"
            )
            db.add(new_alert)
            await db.flush()
            alert_id = new_alert.id
            alert_triggered = True

        # Update Asset Risk Score
        penalty = 25 if eval_result["severity"] == "CRITICAL" else 12
        asset.risk_score = min(100, (asset.risk_score or 0) + penalty)
        asset.health_score = max(0, 100 - asset.risk_score)
        asset.risk_level = "CRITICAL" if asset.risk_score >= 70 else ("HIGH" if asset.risk_score >= 50 else "MEDIUM")

    await db.flush()

    return ApiResponse(
        success=True,
        data=IngestReadingResponse(
            reading_id=reading.id,
            status=eval_result["status"],
            anomaly_detected=anomaly_detected,
            alert_triggered=alert_triggered,
            alert_id=alert_id,
            asset_risk_updated=anomaly_detected,
            new_risk_score=asset.risk_score,
            recommended_action=action
        ),
        message="Telemetry reading processed through threshold evaluation pipeline"
    )
