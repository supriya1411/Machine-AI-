from typing import Optional, List
from pydantic import BaseModel

class SiteBase(BaseModel):
    name: str
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    status: str = "OPERATIONAL"

class SiteCreate(SiteBase):
    pass

class SiteUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    status: Optional[str] = None

class SiteResponse(SiteBase):
    id: str
    total_assets: Optional[int] = 0
    high_risk_assets: Optional[int] = 0

    class Config:
        from_attributes = True
