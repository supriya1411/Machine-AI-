from typing import Optional, List, Any
from datetime import datetime, date
from pydantic import BaseModel

class RiskFactor(BaseModel):
    factor: str
    value: str
    impact: str # LOW, MEDIUM, HIGH, CRITICAL

class RiskExplanationResponse(BaseModel):
    asset_id: str
    asset_name: str
    health_score: int
    risk_score: int
    risk_level: str # LOW, MEDIUM, HIGH, CRITICAL
    factors: List[RiskFactor] = []
    recommended_actions: List[str] = []
    prediction_available: bool = True
    prediction_reason: Optional[str] = None
    evaluation_type: str = "MULTI_FACTOR_HEURISTIC_RISK" # Clearly distinguish from ML prediction

class AssetBase(BaseModel):
    asset_id: str
    name: str
    category: str
    model: Optional[str] = None
    serial_number: Optional[str] = None
    manufacturer: Optional[str] = None
    site_id: str
    floor: Optional[str] = None
    installation_date: Optional[date] = None
    warranty_expiry: Optional[date] = None
    criticality: str = "MEDIUM"
    status: str = "OPERATIONAL"

class AssetCreate(AssetBase):
    pass

class AssetUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    manufacturer: Optional[str] = None
    site_id: Optional[str] = None
    floor: Optional[str] = None
    installation_date: Optional[date] = None
    warranty_expiry: Optional[date] = None
    criticality: Optional[str] = None
    status: Optional[str] = None

class AssetResponse(AssetBase):
    id: str
    health_score: int
    risk_score: int
    risk_level: str
    last_risk_assessment: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    site_name: Optional[str] = None

    class Config:
        from_attributes = True

class AssetDetailResponse(AssetResponse):
    risk_explanation: Optional[RiskExplanationResponse] = None
    active_alerts_count: int = 0
    active_alerts: List[Any] = []
    recent_service_calls: List[Any] = []
    sensor_devices: List[Any] = []
    upcoming_maintenance: List[Any] = []
    active_contract: Optional[Any] = None
    documents: List[Any] = []
    mtbf_hours: Optional[float] = None
