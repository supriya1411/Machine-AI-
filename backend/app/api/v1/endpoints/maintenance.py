from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, or_
from typing import List, Optional
from datetime import datetime, date, timedelta

from app.db.session import get_db
from app.models.maintenance import Maintenance
from app.models.asset import Asset
from app.models.site import Site
from app.models.user import User
from app.models.contract import Contract
from app.schemas.maintenance import (
    MaintenanceResponse,
    MaintenanceCreate,
    MaintenanceUpdate,
    CadenceComplianceResult
)
from app.schemas.common import ApiResponse
from app.services.maintenance import MaintenanceService

router = APIRouter()

@router.get("", response_model=ApiResponse[List[MaintenanceResponse]], summary="Query Fleet Preventive Maintenance Records")
async def list_maintenance(
    status: Optional[str] = Query(None, description="SCHEDULED, COMPLETED, OVERDUE, MISSED, CANCELLED"),
    asset_id: Optional[str] = Query(None),
    contract_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(
            Maintenance,
            Asset.name.label("asset_name"),
            Site.name.label("site_name"),
            User.name.label("engineer_name"),
            Contract.name.label("contract_name")
        )
        .join(Asset, Maintenance.asset_id == Asset.id)
        .outerjoin(Site, Asset.site_id == Site.id)
        .outerjoin(User, Maintenance.engineer_id == User.id)
        .outerjoin(Contract, Maintenance.contract_id == Contract.id)
        .order_by(desc(Maintenance.scheduled_date))
    )

    if status:
        stmt = stmt.where(Maintenance.status == status.upper())
    if asset_id:
        stmt = stmt.where(Maintenance.asset_id == asset_id)
    if contract_id:
        stmt = stmt.where(Maintenance.contract_id == contract_id)

    stmt = stmt.limit(limit)
    res = await db.execute(stmt)
    rows = res.all()

    items = []
    for row in rows:
        m, a_name, s_name, e_name, c_name = row[0], row[1], row[2], row[3], row[4]
        items.append(MaintenanceResponse(
            id=m.id,
            asset_id=m.asset_id,
            pm_type=m.pm_type,
            scheduled_date=m.scheduled_date,
            completed_date=m.completed_date,
            status=m.status,
            engineer_id=m.engineer_id,
            contract_id=m.contract_id,
            notes=m.notes,
            evidence_document_id=m.evidence_document_id,
            asset_name=a_name,
            site_name=s_name,
            engineer_name=e_name,
            contract_name=c_name
        ))

    return ApiResponse(success=True, data=items, meta={"count": len(items)})

@router.get("/schedule", response_model=ApiResponse[List[MaintenanceResponse]], summary="Get Upcoming PM Schedule")
async def get_schedule(days_ahead: int = Query(60, ge=7, le=365), db: AsyncSession = Depends(get_db)):
    today = date.today()
    cutoff = today + timedelta(days=days_ahead)

    stmt = (
        select(Maintenance, Asset.name.label("asset_name"), Site.name.label("site_name"))
        .join(Asset, Maintenance.asset_id == Asset.id)
        .outerjoin(Site, Asset.site_id == Site.id)
        .where(
            Maintenance.status == "SCHEDULED",
            Maintenance.scheduled_date >= today,
            Maintenance.scheduled_date <= cutoff
        )
        .order_by(Maintenance.scheduled_date)
    )
    res = await db.execute(stmt)
    rows = res.all()

    items = [MaintenanceResponse(
        id=r[0].id,
        asset_id=r[0].asset_id,
        pm_type=r[0].pm_type,
        scheduled_date=r[0].scheduled_date,
        status=r[0].status,
        asset_name=r[1],
        site_name=r[2]
    ) for r in rows]

    return ApiResponse(success=True, data=items, meta={"upcoming_days": days_ahead, "count": len(items)})

@router.get("/overdue", response_model=ApiResponse[List[MaintenanceResponse]], summary="Get Overdue Preventive Maintenance Tasks")
async def get_overdue(db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Maintenance, Asset.name.label("asset_name"), Site.name.label("site_name"))
        .join(Asset, Maintenance.asset_id == Asset.id)
        .outerjoin(Site, Asset.site_id == Site.id)
        .where(Maintenance.status == "OVERDUE")
        .order_by(Maintenance.scheduled_date)
    )
    res = await db.execute(stmt)
    rows = res.all()

    items = [MaintenanceResponse(
        id=r[0].id,
        asset_id=r[0].asset_id,
        pm_type=r[0].pm_type,
        scheduled_date=r[0].scheduled_date,
        status=r[0].status,
        asset_name=r[1],
        site_name=r[2]
    ) for r in rows]

    return ApiResponse(success=True, data=items, meta={"overdue_count": len(items)})

@router.get("/compliance", response_model=ApiResponse[List[CadenceComplianceResult]], summary="Evaluate Strict PM Cadence & Interval Adherence (Section 11)")
async def evaluate_compliance(
    asset_id: Optional[str] = Query(None, description="Evaluate specific asset or whole fleet"),
    db: AsyncSession = Depends(get_db)
):
    """
    Rigorously evaluates PM interval/cadence, not just total PM count.
    Flags cadence violations when intervals between completed PMs exceed tolerance or cluster erratically.
    """
    asset_stmt = select(Asset)
    if asset_id:
        asset_stmt = asset_stmt.where(or_(Asset.id == asset_id, Asset.asset_id == asset_id))
    else:
        asset_stmt = asset_stmt.limit(50)

    a_res = await db.execute(asset_stmt)
    assets = a_res.scalars().all()

    results = []
    for asset in assets:
        # Fetch completed PMs
        pm_stmt = select(Maintenance).where(
            Maintenance.asset_id == asset.id,
            Maintenance.status == "COMPLETED",
            Maintenance.completed_date.isnot(None)
        ).order_by(Maintenance.completed_date)
        pm_res = await db.execute(pm_stmt)
        pms = pm_res.scalars().all()

        completed_dates = [p.completed_date for p in pms]

        cadence_eval = MaintenanceService.evaluate_pm_cadence(
            required_frequency_days=90,
            completed_dates=completed_dates
        )

        results.append(CadenceComplianceResult(
            asset_id=asset.asset_id,
            asset_name=asset.name,
            pm_frequency_days=90,
            total_pm_scheduled=len(pms),
            total_pm_completed=len(completed_dates),
            cadence_compliance=cadence_eval["cadence_compliance"],
            violation=cadence_eval["violation"],
            reason=cadence_eval["reason"],
            actual_intervals_days=cadence_eval["actual_intervals_days"],
            max_gap_days=cadence_eval["max_gap_days"],
            evaluation_detail=cadence_eval["evaluation_detail"]
        ))

    return ApiResponse(success=True, data=results)

@router.post("", response_model=ApiResponse[MaintenanceResponse], status_code=status.HTTP_201_CREATED, summary="Schedule New PM Visit")
async def create_maintenance(payload: MaintenanceCreate, db: AsyncSession = Depends(get_db)):
    new_pm = Maintenance(**payload.dict())
    db.add(new_pm)
    await db.flush()

    return ApiResponse(success=True, data=MaintenanceResponse.model_validate(new_pm), message="PM scheduled successfully")

@router.patch("/{id}", response_model=ApiResponse[MaintenanceResponse], summary="Update PM Status or Log Completion")
async def update_maintenance(id: str, payload: MaintenanceUpdate, db: AsyncSession = Depends(get_db)):
    stmt = select(Maintenance).where(Maintenance.id == id)
    res = await db.execute(stmt)
    pm = res.scalar_one_or_none()
    if not pm:
        raise HTTPException(status_code=404, detail="Maintenance record not found")

    update_data = payload.dict(exclude_unset=True)
    for k, v in update_data.items():
        setattr(pm, k, v)

    await db.flush()
    return ApiResponse(success=True, data=MaintenanceResponse.model_validate(pm), message="Maintenance updated")
