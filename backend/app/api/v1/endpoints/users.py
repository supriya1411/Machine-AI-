from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.db.session import get_db
from app.models.user import User, Role
from app.schemas.user import UserResponse, RoleResponse
from app.schemas.common import ApiResponse
from app.api.deps import require_roles

router = APIRouter()

@router.get("", response_model=ApiResponse[List[UserResponse]], summary="List Enterprise Personnel Directory")
async def list_users(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(User, Role.name.label("role_name")).outerjoin(Role, User.role_id == Role.id))
    rows = res.all()
    items = []
    for u, r_name in rows:
        items.append(UserResponse(
            id=u.id,
            name=u.name,
            email=u.email,
            phone=u.phone,
            role_id=u.role_id,
            role_name=r_name,
            status=u.status,
            site_id=u.site_id,
            created_at=u.created_at
        ))
    return ApiResponse(success=True, data=items)

@router.get("/roles", response_model=ApiResponse[List[RoleResponse]], summary="List RBAC Roles and Permissions")
async def list_roles(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Role))
    roles = res.scalars().all()
    items = [RoleResponse.model_validate(r) for r in roles]
    return ApiResponse(success=True, data=items)
