from typing import Optional, List, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel

class MaintenanceBase(BaseModel):
    asset_id: str
    pm_type: str = "QUARTERLY_PM"
    scheduled_date: date
    completed_date: Optional[date] = None
    status: str = "SCHEDULED" # SCHEDULED, COMPLETED, OVERDUE, MISSED, CANCELLED
    engineer_id: Optional[str] = None
    contract_id: Optional[str] = None
    notes: Optional[str] = None
    evidence_document_id: Optional[str] = None

class MaintenanceCreate(MaintenanceBase):
    pass

class MaintenanceUpdate(BaseModel):
    pm_type: Optional[str] = None
    scheduled_date: Optional[date] = None
    completed_date: Optional[date] = None
    status: Optional[str] = None
    engineer_id: Optional[str] = None
    notes: Optional[str] = None
    evidence_document_id: Optional[str] = None

class MaintenanceResponse(MaintenanceBase):
    id: str
    asset_name: Optional[str] = None
    site_name: Optional[str] = None
    engineer_name: Optional[str] = None
    contract_name: Optional[str] = None

    class Config:
        from_attributes = True

class CadenceComplianceResult(BaseModel):
    asset_id: str
    asset_name: str
    pm_frequency_days: int
    total_pm_scheduled: int
    total_pm_completed: int
    cadence_compliance: bool
    violation: bool
    reason: Optional[str] = None
    actual_intervals_days: List[int] = []
    max_gap_days: int
    evaluation_detail: str

class WorkOrderBase(BaseModel):
    asset_id: str
    type: str = "CORRECTIVE"
    priority: str = "MEDIUM"
    assigned_engineer_id: Optional[str] = None
    due_date: datetime
    status: str = "OPEN"
    description: str

class WorkOrderCreate(WorkOrderBase):
    pass

class WorkOrderUpdate(BaseModel):
    priority: Optional[str] = None
    assigned_engineer_id: Optional[str] = None
    due_date: Optional[datetime] = None
    status: Optional[str] = None
    description: Optional[str] = None

class WorkOrderResponse(WorkOrderBase):
    id: str
    created_at: datetime
    asset_name: Optional[str] = None
    site_name: Optional[str] = None
    assigned_engineer_name: Optional[str] = None

    class Config:
        from_attributes = True
