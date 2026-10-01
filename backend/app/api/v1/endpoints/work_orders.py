from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, or_
from typing import List, Optional
from datetime import datetime

from app.db.session import get_db
from app.models.maintenance import WorkOrder
from app.models.asset import Asset
from app.models.site import Site
from app.models.user import User
from app.schemas.maintenance import WorkOrderResponse, WorkOrderCreate, WorkOrderUpdate
from app.schemas.common import ApiResponse

router = APIRouter()

@router.get("", response_model=ApiResponse[List[WorkOrderResponse]], summary="List Work Orders")
async def list_work_orders(
    status: Optional[str] = Query(None, description="OPEN, IN_PROGRESS, PENDING_PARTS, COMPLETED, CANCELLED"),
    priority: Optional[str] = Query(None, description="LOW, MEDIUM, HIGH, CRITICAL"),
    asset_id: Optional[str] = Query(None),
    engineer_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(
            WorkOrder,
            Asset.name.label("asset_name"),
            Site.name.label("site_name"),
            User.name.label("engineer_name")
        )
        .join(Asset, WorkOrder.asset_id == Asset.id)
        .outerjoin(Site, Asset.site_id == Site.id)
        .outerjoin(User, WorkOrder.assigned_engineer_id == User.id)
        .order_by(desc(WorkOrder.created_at))
    )

    if status:
        stmt = stmt.where(WorkOrder.status == status.upper())
    if priority:
        stmt = stmt.where(WorkOrder.priority == priority.upper())
    if asset_id:
        stmt = stmt.where(WorkOrder.asset_id == asset_id)
    if engineer_id:
        stmt = stmt.where(WorkOrder.assigned_engineer_id == engineer_id)

    stmt = stmt.limit(limit)
    res = await db.execute(stmt)
    rows = res.all()

    items = []
    for row in rows:
        wo, a_name, s_name, e_name = row[0], row[1], row[2], row[3]
        items.append(WorkOrderResponse(
            id=wo.id,
            asset_id=wo.asset_id,
            type=wo.type,
            priority=wo.priority,
            assigned_engineer_id=wo.assigned_engineer_id,
            created_at=wo.created_at,
            due_date=wo.due_date,
            status=wo.status,
            description=wo.description,
            asset_name=a_name,
            site_name=s_name,
            assigned_engineer_name=e_name
        ))

    return ApiResponse(success=True, data=items, meta={"total_orders": len(items)})

@router.post("", response_model=ApiResponse[WorkOrderResponse], status_code=status.HTTP_201_CREATED, summary="Create Work Order")
async def create_work_order(payload: WorkOrderCreate, db: AsyncSession = Depends(get_db)):
    wo = WorkOrder(**payload.dict())
    db.add(wo)
    await db.flush()

    return ApiResponse(success=True, data=WorkOrderResponse.model_validate(wo), message="Work order created")

@router.patch("/{id}", response_model=ApiResponse[WorkOrderResponse], summary="Update Work Order Status / Assignment")
async def update_work_order(id: str, payload: WorkOrderUpdate, db: AsyncSession = Depends(get_db)):
    stmt = select(WorkOrder).where(WorkOrder.id == id)
    res = await db.execute(stmt)
    wo = res.scalar_one_or_none()
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")

    update_dict = payload.dict(exclude_unset=True)
    for k, v in update_dict.items():
        setattr(wo, k, v)

    await db.flush()
    return ApiResponse(success=True, data=WorkOrderResponse.model_validate(wo), message="Work order updated")
