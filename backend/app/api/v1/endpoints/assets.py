from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, desc, asc, func
from typing import List, Optional
from datetime import datetime

from app.db.session import get_db
from app.models.asset import Asset
from app.models.site import Site
from app.models.service_call import ServiceCall
from app.models.iot import SensorDevice, SensorReading, SensorAnomaly
from app.models.maintenance import Maintenance
from app.models.contract import Contract, ContractAsset
from app.models.alert import Alert
from app.models.document import Document
from app.schemas.asset import (
    AssetResponse,
    AssetDetailResponse,
    AssetCreate,
    AssetUpdate,
    RiskExplanationResponse,
    RiskFactor
)
from app.schemas.common import ApiResponse, PaginationMeta
from app.services.risk_engine import RiskEngine
from app.services.mtbf import MtbfService

router = APIRouter()

@router.get("", response_model=ApiResponse[List[AssetResponse]], summary="Search & Filter Asset Fleet with Health & Risk Scores")
async def list_assets(
    query: Optional[str] = Query(None, description="Search by name, asset_id, serial_number, or model"),
    category: Optional[str] = Query(None, description="Filter by category (e.g. HVAC, Chiller, Transformer)"),
    site_id: Optional[str] = Query(None, description="Filter by site ID"),
    risk_level: Optional[str] = Query(None, description="Filter by LOW, MEDIUM, HIGH, CRITICAL"),
    status: Optional[str] = Query(None, description="Filter by OPERATIONAL, DEGRADED, DOWN, MAINTENANCE"),
    sort_by: Optional[str] = Query("risk_score", description="Sort field: risk_score, health_score, name, asset_id, created_at"),
    sort_desc: Optional[bool] = Query(True, description="Sort descending"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Asset, Site.name.label("site_name")).outerjoin(Site, Asset.site_id == Site.id)

    # Search filter
    if query:
        search_pattern = f"%{query}%"
        stmt = stmt.where(
            or_(
                Asset.name.ilike(search_pattern),
                Asset.asset_id.ilike(search_pattern),
                Asset.serial_number.ilike(search_pattern),
                Asset.model.ilike(search_pattern)
            )
        )

    if category:
        stmt = stmt.where(Asset.category.ilike(f"%{category}%"))
    if site_id:
        stmt = stmt.where(Asset.site_id == site_id)
    if risk_level:
        stmt = stmt.where(Asset.risk_level == risk_level.upper())
    if status:
        stmt = stmt.where(Asset.status == status.upper())

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_res = await db.execute(count_stmt)
    total_count = total_res.scalar() or 0

    # Sorting
    sort_col = getattr(Asset, sort_by, Asset.risk_score)
    if sort_desc:
        stmt = stmt.order_by(desc(sort_col))
    else:
        stmt = stmt.order_by(asc(sort_col))

    # Pagination
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    rows = result.all()

    items = []
    for row in rows:
        asset, site_name = row[0], row[1]
        data = {
            "id": asset.id,
            "asset_id": asset.asset_id,
            "name": asset.name,
            "category": asset.category,
            "model": asset.model,
            "serial_number": asset.serial_number,
            "manufacturer": asset.manufacturer,
            "site_id": asset.site_id,
            "site_name": site_name,
            "floor": asset.floor,
            "installation_date": asset.installation_date,
            "warranty_expiry": asset.warranty_expiry,
            "criticality": asset.criticality,
            "status": asset.status,
            "health_score": asset.health_score or 100,
            "risk_score": asset.risk_score or 0,
            "risk_level": asset.risk_level or "LOW",
            "last_risk_assessment": asset.last_risk_assessment,
            "created_at": asset.created_at,
            "updated_at": asset.updated_at
        }
        items.append(AssetResponse(**data))

    total_pages = (total_count + page_size - 1) // page_size

    return ApiResponse(
        success=True,
        data=items,
        meta=PaginationMeta(
            page=page,
            page_size=page_size,
            total=total_count,
            total_pages=total_pages
        )
    )

@router.get("/{id}", response_model=ApiResponse[AssetDetailResponse], summary="Get Aggregated Asset Detail with Full Operational Intelligence")
async def get_asset_detail(id: str, db: AsyncSession = Depends(get_db)):
    """
    Returns single asset with aggregated overview, health score, risk explanation,
    telemetry devices, service call history, PM compliance, active contracts, and documents.
    """
    stmt = select(Asset, Site.name.label("site_name")).outerjoin(Site, Asset.site_id == Site.id).where(or_(Asset.id == id, Asset.asset_id == id))
    res = await db.execute(stmt)
    row = res.first()

    if not row:
        raise HTTPException(status_code=404, detail="Asset not found")

    asset, site_name = row[0], row[1]

    # Service calls
    sc_res = await db.execute(select(ServiceCall).where(ServiceCall.asset_id == asset.id).order_by(desc(ServiceCall.date)).limit(10))
    service_calls = sc_res.scalars().all()

    # Sensors
    s_res = await db.execute(select(SensorDevice).where(SensorDevice.asset_id == asset.id))
    sensors = s_res.scalars().all()

    # Sensor Anomalies
    anom_res = await db.execute(select(SensorAnomaly).join(SensorDevice, SensorAnomaly.sensor_id == SensorDevice.id).where(SensorDevice.asset_id == asset.id))
    anomalies = anom_res.scalars().all()

    # Alerts
    al_res = await db.execute(select(Alert).where(Alert.asset_id == asset.id, Alert.status.in_(["ACTIVE", "ASSIGNED"])))
    alerts = al_res.scalars().all()

    # PM
    pm_res = await db.execute(select(Maintenance).where(Maintenance.asset_id == asset.id).order_by(desc(Maintenance.scheduled_date)))
    maintenances = pm_res.scalars().all()

    # Calculate MTBF
    failure_dates = [c.date for c in service_calls if c.date]
    mtbf_res = MtbfService.calculate_mtbf_for_dates(failure_dates)

    # Dynamic Risk Engine Evaluation
    pm_compliant = not any(m.status == "OVERDUE" for m in maintenances)
    h_score, r_score, r_level, factors, actions, pred_avail, pred_reason = RiskEngine.calculate_asset_health_and_risk(
        asset_criticality=asset.criticality,
        service_calls=[{"date": c.date, "severity": c.severity} for c in service_calls],
        sensor_anomalies=[{"severity": a.severity, "resolved": a.resolved} for a in anomalies],
        active_alerts=[{"severity": al.severity, "status": al.status} for al in alerts],
        pm_compliance_flag=pm_compliant,
        mtbf_trend=mtbf_res.get("trend")
    )

    risk_explanation = RiskExplanationResponse(
        asset_id=asset.asset_id,
        asset_name=asset.name,
        health_score=h_score,
        risk_score=r_score,
        risk_level=r_level,
        factors=[RiskFactor(**f) for f in factors],
        recommended_actions=actions,
        prediction_available=pred_avail,
        prediction_reason=pred_reason,
        evaluation_type="MULTI_FACTOR_HEURISTIC_RISK"
    )

    detail_data = {
        "id": asset.id,
        "asset_id": asset.asset_id,
        "name": asset.name,
        "category": asset.category,
        "model": asset.model,
        "serial_number": asset.serial_number,
        "manufacturer": asset.manufacturer,
        "site_id": asset.site_id,
        "site_name": site_name,
        "floor": asset.floor,
        "installation_date": asset.installation_date,
        "warranty_expiry": asset.warranty_expiry,
        "criticality": asset.criticality,
        "status": asset.status,
        "health_score": h_score,
        "risk_score": r_score,
        "risk_level": r_level,
        "last_risk_assessment": datetime.utcnow(),
        "created_at": asset.created_at,
        "updated_at": asset.updated_at,
        "risk_explanation": risk_explanation,
        "active_alerts_count": len(alerts),
        "active_alerts": [{
            "id": a.id, "title": a.title, "severity": a.severity, "reason": a.reason,
            "recommended_action": a.recommended_action, "current_value": a.current_value, "created_at": a.created_at
        } for a in alerts],
        "recent_service_calls": [{
            "id": sc.id, "date": sc.date, "raw_fault": sc.raw_fault, "fault_code": sc.fault_code,
            "severity": sc.severity, "resolution": sc.resolution, "downtime": sc.downtime
        } for sc in service_calls[:5]],
        "sensor_devices": [{
            "id": s.id, "device_id": s.device_id, "sensor_type": s.sensor_type, "status": s.status, "last_seen": s.last_seen
        } for s in sensors],
        "upcoming_maintenance": [{
            "id": m.id, "pm_type": m.pm_type, "scheduled_date": m.scheduled_date, "status": m.status
        } for m in maintenances[:3]],
        "documents": [],
        "mtbf_hours": mtbf_res.get("mtbf_hours")
    }

    return ApiResponse(success=True, data=AssetDetailResponse(**detail_data))

@router.get("/{id}/risk-explanation", response_model=ApiResponse[RiskExplanationResponse], summary="Explain Asset Risk (Section 5)")
async def get_asset_risk_explanation(id: str, db: AsyncSession = Depends(get_db)):
    """
    Dedicated endpoint answering: Why is this asset risky?
    Grounded strictly in historical failures, IoT anomalies, and PM compliance.
    """
    detail_res = await get_asset_detail(id, db)
    return ApiResponse(success=True, data=detail_res.data.risk_explanation)

@router.post("", response_model=ApiResponse[AssetResponse], status_code=status.HTTP_201_CREATED, summary="Register New Asset")
async def create_asset(payload: AssetCreate, db: AsyncSession = Depends(get_db)):
    new_asset = Asset(**payload.dict())
    new_asset.health_score = 100
    new_asset.risk_score = 0
    new_asset.risk_level = "LOW"
    db.add(new_asset)
    await db.flush()

    res = await get_asset_detail(new_asset.id, db)
    return ApiResponse(success=True, data=res.data, message="Asset registered successfully")

@router.patch("/{id}", response_model=ApiResponse[AssetResponse], summary="Update Asset Specifications")
async def update_asset(id: str, payload: AssetUpdate, db: AsyncSession = Depends(get_db)):
    stmt = select(Asset).where(or_(Asset.id == id, Asset.asset_id == id))
    res = await db.execute(stmt)
    asset = res.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    update_data = payload.dict(exclude_unset=True)
    for field, val in update_data.items():
        setattr(asset, field, val)

    await db.flush()
    return await get_asset_detail(asset.id, db)

@router.delete("/{id}", response_model=ApiResponse[bool], summary="Decommission / Remove Asset")
async def delete_asset(id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Asset).where(or_(Asset.id == id, Asset.asset_id == id))
    res = await db.execute(stmt)
    asset = res.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    await db.delete(asset)
    return ApiResponse(success=True, data=True, message=f"Asset {asset.asset_id} successfully deleted")
