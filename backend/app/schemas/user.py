from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr

class RoleBase(BaseModel):
    name: str
    permissions: List[str] = []

class RoleResponse(RoleBase):
    id: str

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserResponse"

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class UserBase(BaseModel):
    name: str
    email: EmailStr
    role_id: Optional[str] = None
    status: str = "ACTIVE"

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role_id: Optional[str] = None
    status: Optional[str] = None
    password: Optional[str] = None

class UserResponse(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime
    role: Optional[RoleResponse] = None

    class Config:
        from_attributes = True

TokenResponse.update_forward_refs()
