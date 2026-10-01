from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.db.session import get_db
from app.models.site import Site
from app.models.asset import Asset
from app.schemas.site import SiteResponse, SiteCreate
from app.schemas.common import ApiResponse

router = APIRouter()

@router.get("", response_model=ApiResponse[List[SiteResponse]], summary="List Enterprise Sites & Facility Locations")
async def list_sites(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Site))
    sites = res.scalars().all()

    items = []
    for s in sites:
        a_res = await db.execute(select(Asset).where(Asset.site_id == s.id))
        assets = a_res.scalars().all()
        hr = sum(1 for a in assets if a.risk_level in ("HIGH", "CRITICAL"))

        items.append(SiteResponse(
            id=s.id,
            name=s.name,
            code=s.code,
            address=s.address,
            city=s.city,
            state=s.state,
            country=s.country,
            latitude=s.latitude,
            longitude=s.longitude,
            status=s.status,
            total_assets=len(assets),
            high_risk_assets=hr
        ))

    return ApiResponse(success=True, data=items, meta={"total_sites": len(items)})

@router.post("", response_model=ApiResponse[SiteResponse], status_code=status.HTTP_201_CREATED, summary="Create Site Location")
async def create_site(payload: SiteCreate, db: AsyncSession = Depends(get_db)):
    site = Site(**payload.dict())
    db.add(site)
    await db.flush()
    return ApiResponse(success=True, data=SiteResponse.model_validate(site), message="Site created successfully")
