from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel

class ThresholdConfig(BaseModel):
    safe_min: float
    safe_max: float
    warning_min: float
    warning_max: float
    critical_min: float
    critical_max: float

class SensorDeviceBase(BaseModel):
    asset_id: str
    device_id: str
    sensor_type: str # temperature, humidity, vibration, power
    status: str = "ONLINE"
    configuration: Dict[str, Any] = {}

class SensorDeviceCreate(SensorDeviceBase):
    pass

class SensorDeviceResponse(SensorDeviceBase):
    id: str
    last_seen: Optional[datetime] = None
    asset_name: Optional[str] = None
    site_name: Optional[str] = None
    current_value: Optional[float] = None
    unit: Optional[str] = None
    thresholds: Optional[ThresholdConfig] = None

    class Config:
        from_attributes = True

class SensorReadingBase(BaseModel):
    sensor_id: str
    value: float
    unit: str
    timestamp: Optional[datetime] = None

class SensorReadingCreate(SensorReadingBase):
    pass

class SensorReadingResponse(SensorReadingBase):
    id: str
    timestamp: datetime

    class Config:
        from_attributes = True

class SensorAnomalyResponse(BaseModel):
    id: str
    sensor_id: str
    device_id: Optional[str] = None
    asset_id: Optional[str] = None
    asset_name: Optional[str] = None
    timestamp: datetime
    severity: str # WARNING, CRITICAL
    value: float
    unit: str
    threshold_breached: str
    duration_minutes: float
    resolved: str

    class Config:
        from_attributes = True

class IngestReadingResponse(BaseModel):
    reading_id: str
    status: str # NORMAL, WARNING, CRITICAL
    anomaly_detected: bool
    alert_triggered: bool
    alert_id: Optional[str] = None
    asset_risk_updated: bool
    new_risk_score: Optional[int] = None
    recommended_action: Optional[str] = None
