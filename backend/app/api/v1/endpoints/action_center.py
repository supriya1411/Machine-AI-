from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime, date
from app.db.session import get_db
from app.schemas.alert import ActionCenterItem
from app.schemas.common import ApiResponse
from app.models.alert import Alert
from app.models.asset import Asset
from app.models.maintenance import Maintenance
from app.models.contract import Contract
from app.services.action_center import ActionCenterService

router = APIRouter()

@router.get("", response_model=ApiResponse[List[ActionCenterItem]], summary="Get Prioritized Operational Actions")
async def get_action_center(
    filter_type: Optional[str] = Query("ALL", description="Filter by: ALL, CRITICAL, HIGH, PM, CONTRACT"),
    db: AsyncSession = Depends(get_db)
):
    """
    Primary Action Center Endpoint:
    Synthesizes active threshold anomalies, overdue PM events, expiring contracts,
    and degraded equipment into an urgency-ranked operational queue.
    """
    # 1. Fetch active alerts
    alert_stmt = select(Alert, Asset.name.label("asset_name")).outerjoin(Asset, Alert.asset_id == Asset.id).where(Alert.status.in_(["ACTIVE", "ASSIGNED"]))
    alert_res = await db.execute(alert_stmt)
    alert_rows = alert_res.all()

    active_alerts = []
    for row in alert_rows:
        alert, asset_name = row[0], row[1]
        active_alerts.append({
            "id": alert.id,
            "type": alert.type,
            "severity": alert.severity,
            "asset_id": alert.asset_id,
            "contract_id": alert.contract_id,
            "asset_name": asset_name,
            "title": alert.title,
            "reason": alert.reason,
            "recommended_action": alert.recommended_action,
            "current_value": alert.current_value,
            "threshold": alert.threshold,
            "duration": alert.duration,
            "status": alert.status,
            "created_at": alert.created_at
        })

    # 2. Fetch overdue PMs
    today = date.today()
    pm_stmt = select(Maintenance, Asset.name.label("asset_name")).join(Asset, Maintenance.asset_id == Asset.id).where(Maintenance.status == "OVERDUE")
    pm_res = await db.execute(pm_stmt)
    pm_rows = pm_res.all()

    overdue_pms = []
    for row in pm_rows:
        pm, asset_name = row[0], row[1]
        overdue_pms.append({
            "id": pm.id,
            "asset_id": pm.asset_id,
            "asset_name": asset_name,
            "pm_type": pm.pm_type,
            "scheduled_date": pm.scheduled_date
        })

    # 3. Fetch expiring contracts
    contract_stmt = select(Contract).where(Contract.status.in_(["ACTIVE", "EXPIRING_SOON"]))
    c_res = await db.execute(contract_stmt)
    contracts = c_res.scalars().all()

    expiring_contracts = []
    for c in contracts:
        days = (c.end_date - today).days
        if days <= 60:
            expiring_contracts.append({
                "id": c.id,
                "contract_id": c.contract_id,
                "name": c.name,
                "customer": c.customer,
                "type": c.type,
                "end_date": c.end_date,
                "days_to_expiry": max(0, days),
                "value": c.value,
                "recommended_strategy": "Expedite renewal review" if days <= 30 else "Prepare renewal proposal"
            })

    # High risk assets
    high_risk_stmt = select(Asset).where(Asset.risk_level.in_(["HIGH", "CRITICAL"]))
    hr_res = await db.execute(high_risk_stmt)
    high_risk_assets = [{"id": a.id, "name": a.name, "risk_score": a.risk_score} for a in hr_res.scalars().all()]

    items = ActionCenterService.prioritize_actions(
        active_alerts=active_alerts,
        overdue_pms=overdue_pms,
        expiring_contracts=expiring_contracts,
        high_risk_assets=high_risk_assets,
        filter_category=filter_type
    )

    action_items = [ActionCenterItem(**item) for item in items]

    return ApiResponse(
        success=True,
        data=action_items,
        meta={"total_actions": len(action_items), "filter": filter_type}
    )
