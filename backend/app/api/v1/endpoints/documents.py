from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from datetime import datetime

from app.db.session import get_db
from app.models.document import Document
from app.schemas.common import ApiResponse
from pydantic import BaseModel

class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    entity_type: str
    entity_id: str
    file_size_bytes: int
    created_at: datetime

    class Config:
        from_attributes = True

router = APIRouter()

@router.get("", response_model=ApiResponse[List[DocumentResponse]], summary="List Asset & Contract Documentation")
async def list_documents(
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Document).order_by(desc(Document.created_at))
    if entity_type:
        stmt = stmt.where(Document.entity_type == entity_type.upper())
    if entity_id:
        stmt = stmt.where(Document.entity_id == entity_id)

    res = await db.execute(stmt)
    docs = res.scalars().all()
    items = [DocumentResponse.model_validate(d) for d in docs]
    return ApiResponse(success=True, data=items)
