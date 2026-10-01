from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.db.session import get_db
from app.models.service_call import FaultCategory
from app.schemas.service_call import FaultCategoryResponse, FaultCategoryCreate
from app.schemas.common import ApiResponse
from app.services.fault_normalization import FaultNormalizationService

router = APIRouter()

@router.get("/categories", response_model=ApiResponse[List[FaultCategoryResponse]], summary="List Normalized Fault Taxonomy")
async def list_fault_categories(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(FaultCategory))
    categories = res.scalars().all()
    items = [FaultCategoryResponse.model_validate(c) for c in categories]
    return ApiResponse(success=True, data=items)

@router.post("/categories", response_model=ApiResponse[FaultCategoryResponse], status_code=status.HTTP_201_CREATED, summary="Add / Configure Taxonomy Node")
async def create_fault_category(payload: FaultCategoryCreate, db: AsyncSession = Depends(get_db)):
    fc = FaultCategory(**payload.dict())
    db.add(fc)
    await db.flush()
    return ApiResponse(success=True, data=FaultCategoryResponse.model_validate(fc), message="Fault taxonomy updated")

@router.post("/normalize", response_model=ApiResponse[dict], summary="Test Text Normalization Engine")
async def test_normalize(raw_text: str):
    service = FaultNormalizationService()
    code, name, severity = service.normalize(raw_text)
    return ApiResponse(success=True, data={
        "raw_text": raw_text,
        "normalized_code": code,
        "normalized_name": name,
        "assigned_severity": severity
    })
