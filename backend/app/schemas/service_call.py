from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel

class FaultCategoryBase(BaseModel):
    code: str
    name: str
    severity: str = "MEDIUM"
    keywords: List[str] = []

class FaultCategoryCreate(FaultCategoryBase):
    pass

class FaultCategoryResponse(FaultCategoryBase):
    id: str

    class Config:
        from_attributes = True

class ServiceCallBase(BaseModel):
    asset_id: str
    date: datetime
    raw_fault: str
    description: Optional[str] = None
    resolution: Optional[str] = None
    engineer_id: Optional[str] = None
    downtime: float = 0.0

class ServiceCallCreate(ServiceCallBase):
    pass

class ServiceCallResponse(ServiceCallBase):
    id: str
    normalized_fault_id: Optional[str] = None
    fault_code: Optional[str] = None
    severity: str
    created_at: datetime
    asset_name: Optional[str] = None
    engineer_name: Optional[str] = None

    class Config:
        from_attributes = True

class FaultAnalyticsFilter(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    site_id: Optional[str] = None
    category: Optional[str] = None
    severity: Optional[str] = None
    fault_code: Optional[str] = None

class FaultAnalyticsResponse(BaseModel):
    total_faults: int
    unique_fault_codes: int
    fault_frequency_per_month: float
    top_faults: List[Dict[str, Any]]
    affected_assets_count: int
    severity_distribution: Dict[str, int]
    fault_trends: List[Dict[str, Any]]
    recurring_faults: List[Dict[str, Any]]
    system_mtbf_hours: Optional[float]
    average_resolution_time_hours: float
    possible_correlations: List[Dict[str, Any]]

class MtbfCalculationResponse(BaseModel):
    entity_type: str # ASSET or CATEGORY
    entity_id: str
    entity_name: str
    has_sufficient_data: bool
    mtbf_hours: Optional[float] = None
    total_failures: int
    failure_intervals_hours: List[float] = []
    average_failure_interval_hours: Optional[float] = None
    trend: Optional[str] = None # IMPROVING, DEGRADING, STABLE, INSUFFICIENT_DATA
    reason: Optional[str] = None
