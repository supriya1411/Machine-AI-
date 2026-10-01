from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, or_
from typing import List, Optional
from datetime import datetime

from app.db.session import get_db
from app.models.service_call import ServiceCall, FaultCategory
from app.models.asset import Asset
from app.models.user import User
from app.schemas.service_call import ServiceCallResponse, ServiceCallCreate
from app.schemas.common import ApiResponse
from app.services.fault_normalization import FaultNormalizationService

router = APIRouter()

@router.get("", response_model=ApiResponse[List[ServiceCallResponse]], summary="List Service Call Logs with Normalized Classifications")
async def list_service_calls(
    asset_id: Optional[str] = Query(None),
    fault_code: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(
            ServiceCall,
            Asset.name.label("asset_name"),
            User.name.label("engineer_name")
        )
        .join(Asset, ServiceCall.asset_id == Asset.id)
        .outerjoin(User, ServiceCall.engineer_id == User.id)
        .order_by(desc(ServiceCall.date))
    )

    if asset_id:
        stmt = stmt.where(ServiceCall.asset_id == asset_id)
    if fault_code:
        stmt = stmt.where(ServiceCall.fault_code == fault_code)
    if severity:
        stmt = stmt.where(ServiceCall.severity == severity.upper())

    stmt = stmt.limit(limit)
    res = await db.execute(stmt)
    rows = res.all()

    items = []
    for row in rows:
        sc, a_name, e_name = row[0], row[1], row[2]
        items.append(ServiceCallResponse(
            id=sc.id,
            asset_id=sc.asset_id,
            date=sc.date,
            raw_fault=sc.raw_fault,
            normalized_fault_id=sc.normalized_fault_id,
            fault_code=sc.fault_code,
            severity=sc.severity,
            description=sc.description,
            resolution=sc.resolution,
            engineer_id=sc.engineer_id,
            downtime=sc.downtime,
            created_at=sc.created_at,
            asset_name=a_name,
            engineer_name=e_name
        ))

    return ApiResponse(success=True, data=items, meta={"total_calls": len(items)})

@router.post("", response_model=ApiResponse[ServiceCallResponse], status_code=status.HTTP_201_CREATED, summary="Log Service Call with Automatic Fault Normalization")
async def create_service_call(payload: ServiceCallCreate, db: AsyncSession = Depends(get_db)):
    """
    Ingests field technician log.
    Automatically applies fault normalization while preserving verbatim raw_fault.
    """
    # Verify asset
    a_res = await db.execute(select(Asset).where(or_(Asset.id == payload.asset_id, Asset.asset_id == payload.asset_id)))
    asset = a_res.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    normalizer = FaultNormalizationService()
    code, name, severity = normalizer.normalize(payload.raw_fault)

    # Find category id
    fc_res = await db.execute(select(FaultCategory).where(FaultCategory.code == code))
    fc = fc_res.scalar_one_or_none()

    sc = ServiceCall(
        asset_id=asset.id,
        date=payload.date,
        raw_fault=payload.raw_fault, # Never delete original text!
        normalized_fault_id=fc.id if fc else None,
        fault_code=code,
        severity=severity,
        description=payload.description,
        resolution=payload.resolution,
        engineer_id=payload.engineer_id,
        downtime=payload.downtime
    )
    db.add(sc)
    await db.flush()

    # Recalculate asset health
    asset.risk_score = min(100, (asset.risk_score or 0) + (20 if severity == "CRITICAL" else 10))
    asset.health_score = max(0, 100 - asset.risk_score)
    asset.risk_level = "CRITICAL" if asset.risk_score >= 70 else ("HIGH" if asset.risk_score >= 50 else "MEDIUM")
    await db.flush()

    return ApiResponse(
        success=True,
        data=ServiceCallResponse(
            id=sc.id,
            asset_id=sc.asset_id,
            date=sc.date,
            raw_fault=sc.raw_fault,
            normalized_fault_id=sc.normalized_fault_id,
            fault_code=sc.fault_code,
            severity=sc.severity,
            description=sc.description,
            resolution=sc.resolution,
            engineer_id=sc.engineer_id,
            downtime=sc.downtime,
            created_at=sc.created_at,
            asset_name=asset.name
        ),
        message=f"Service call logged and normalized as {code} [{severity}]"
    )
