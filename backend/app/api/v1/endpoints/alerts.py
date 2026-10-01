from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from datetime import datetime

from app.db.session import get_db
from app.models.alert import Alert
from app.models.asset import Asset
from app.models.site import Site
from app.models.contract import Contract
from app.schemas.alert import (
    AlertResponse,
    AlertCreate,
    AlertAcknowledgeRequest,
    AlertAssignRequest,
    AlertResolveRequest
)
from app.schemas.common import ApiResponse
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("", response_model=ApiResponse[List[AlertResponse]], summary="Query System Alerts with Full Evidence Context")
async def list_alerts(
    severity: Optional[str] = Query(None, description="CRITICAL, HIGH, MEDIUM, LOW"),
    status: Optional[str] = Query(None, description="ACTIVE, ACKNOWLEDGED, ASSIGNED, RESOLVED"),
    alert_type: Optional[str] = Query(None, description="IOT_THRESHOLD, RECURRING_FAILURE, HIGH_RISK, OVERDUE_PM, EXPIRING_CONTRACT"),
    asset_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(
            Alert,
            Asset.name.label("asset_name"),
            Site.name.label("site_name"),
            Contract.name.label("contract_name")
        )
        .outerjoin(Asset, Alert.asset_id == Asset.id)
        .outerjoin(Site, Asset.site_id == Site.id)
        .outerjoin(Contract, Alert.contract_id == Contract.id)
        .order_by(desc(Alert.created_at))
    )

    if severity:
        stmt = stmt.where(Alert.severity == severity.upper())
    if status:
        stmt = stmt.where(Alert.status == status.upper())
    if alert_type:
        stmt = stmt.where(Alert.type == alert_type.upper())
    if asset_id:
        stmt = stmt.where(Alert.asset_id == asset_id)

    stmt = stmt.limit(limit)
    res = await db.execute(stmt)
    rows = res.all()

    items = []
    for row in rows:
        al, a_name, s_name, c_name = row[0], row[1], row[2], row[3]
        items.append(AlertResponse(
            id=al.id,
            type=al.type,
            severity=al.severity,
            asset_id=al.asset_id,
            sensor_id=al.sensor_id,
            contract_id=al.contract_id,
            title=al.title,
            message=al.message,
            current_value=al.current_value,
            threshold=al.threshold,
            duration=al.duration,
            reason=al.reason,
            recommended_action=al.recommended_action,
            status=al.status,
            created_at=al.created_at,
            acknowledged_at=al.acknowledged_at,
            acknowledged_by=al.acknowledged_by,
            resolved_at=al.resolved_at,
            asset_name=a_name,
            site_name=s_name,
            contract_name=c_name
        ))

    return ApiResponse(success=True, data=items, meta={"total_alerts": len(items)})

@router.get("/{id}", response_model=ApiResponse[AlertResponse], summary="Get Alert by ID")
async def get_alert(id: str, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(
            Alert,
            Asset.name.label("asset_name"),
            Site.name.label("site_name"),
            Contract.name.label("contract_name")
        )
        .outerjoin(Asset, Alert.asset_id == Asset.id)
        .outerjoin(Site, Asset.site_id == Site.id)
        .outerjoin(Contract, Alert.contract_id == Contract.id)
        .where(Alert.id == id)
    )
    res = await db.execute(stmt)
    row = res.first()
    if not row:
        raise HTTPException(status_code=404, detail="Alert not found")

    al, a_name, s_name, c_name = row[0], row[1], row[2], row[3]
    resp = AlertResponse(
        id=al.id,
        type=al.type,
        severity=al.severity,
        asset_id=al.asset_id,
        sensor_id=al.sensor_id,
        contract_id=al.contract_id,
        title=al.title,
        message=al.message,
        current_value=al.current_value,
        threshold=al.threshold,
        duration=al.duration,
        reason=al.reason,
        recommended_action=al.recommended_action,
        status=al.status,
        created_at=al.created_at,
        acknowledged_at=al.acknowledged_at,
        acknowledged_by=al.acknowledged_by,
        resolved_at=al.resolved_at,
        asset_name=a_name,
        site_name=s_name,
        contract_name=c_name
    )
    return ApiResponse(success=True, data=resp)

@router.patch("/{id}/acknowledge", response_model=ApiResponse[AlertResponse], summary="Acknowledge Alert")
async def acknowledge_alert(
    id: str,
    payload: AlertAcknowledgeRequest = AlertAcknowledgeRequest(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Alert).where(Alert.id == id)
    res = await db.execute(stmt)
    alert = res.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = "ACKNOWLEDGED"
    alert.acknowledged_at = datetime.utcnow()
    alert.acknowledged_by = current_user.id
    await db.flush()

    return await get_alert(id, db)

@router.patch("/{id}/assign", response_model=ApiResponse[AlertResponse], summary="Assign Alert to Field Service Engineer")
async def assign_alert(
    id: str,
    payload: AlertAssignRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Alert).where(Alert.id == id)
    res = await db.execute(stmt)
    alert = res.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = "ASSIGNED"
    await db.flush()

    return await get_alert(id, db)

@router.patch("/{id}/resolve", response_model=ApiResponse[AlertResponse], summary="Mark Alert as Resolved")
async def resolve_alert(
    id: str,
    payload: AlertResolveRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Alert).where(Alert.id == id)
    res = await db.execute(stmt)
    alert = res.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.status = "RESOLVED"
    alert.resolved_at = datetime.utcnow()
    await db.flush()

    return await get_alert(id, db)
