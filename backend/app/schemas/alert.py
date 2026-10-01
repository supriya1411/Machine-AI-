from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel

class AlertBase(BaseModel):
    type: str # IOT_THRESHOLD, ENVIRONMENTAL_ANOMALY, RECURRING_FAILURE, HIGH_RISK, OVERDUE_PM, PM_CADENCE_VIOLATION, EXPIRING_CONTRACT, RENEWAL_RISK
    severity: str # CRITICAL, HIGH, MEDIUM, LOW
    asset_id: Optional[str] = None
    sensor_id: Optional[str] = None
    contract_id: Optional[str] = None
    title: str
    message: str
    current_value: Optional[str] = None
    threshold: Optional[str] = None
    duration: Optional[str] = None
    reason: str
    recommended_action: str
    status: str = "ACTIVE"

class AlertCreate(AlertBase):
    pass

class AlertResponse(AlertBase):
    id: str
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    asset_name: Optional[str] = None
    site_name: Optional[str] = None
    contract_name: Optional[str] = None

    class Config:
        from_attributes = True

class AlertAcknowledgeRequest(BaseModel):
    notes: Optional[str] = None

class AlertAssignRequest(BaseModel):
    engineer_id: str
    notes: Optional[str] = None

class AlertResolveRequest(BaseModel):
    resolution_notes: str

class ActionCenterItem(BaseModel):
    id: str
    priority: str # CRITICAL, HIGH, MEDIUM, LOW
    type: str # ENVIRONMENTAL, RECURRING_FAULT, OVERDUE_PM, CONTRACT_EXPIRY, ASSET_DEGRADATION
    entity_type: str # ASSET, CONTRACT, MAINTENANCE
    entity_id: str
    asset_name: Optional[str] = None
    issue: str
    risk_level: str # LOW, MEDIUM, HIGH, CRITICAL
    reason: str
    recommended_action: str
    cta: str # INSPECT, CREATE_WORK_ORDER, SCHEDULE_PM, RENEW_CONTRACT, RESOLVE_ALERT
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None
