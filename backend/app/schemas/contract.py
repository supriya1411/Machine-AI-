from typing import Optional, List, Dict, Any
from datetime import date
from pydantic import BaseModel

class ContractBase(BaseModel):
    contract_id: str
    name: str
    customer: str
    vendor: str
    type: str = "AMC" # AMC, CMC
    start_date: date
    end_date: date
    value: float = 0.0
    pm_frequency_days: int = 90
    status: str = "ACTIVE"

class ContractCreate(ContractBase):
    covered_asset_ids: List[str] = []

class ContractUpdate(BaseModel):
    name: Optional[str] = None
    customer: Optional[str] = None
    vendor: Optional[str] = None
    type: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    value: Optional[float] = None
    pm_frequency_days: Optional[int] = None
    status: Optional[str] = None
    covered_asset_ids: Optional[List[str]] = None

class ContractResponse(ContractBase):
    id: str
    compliance_score: float
    renewal_risk: str
    days_to_expiry: int
    covered_assets_count: int = 0
    covered_asset_names: List[str] = []

    class Config:
        from_attributes = True

class ContractComplianceReport(BaseModel):
    overall_compliance: float # e.g. 92.4%
    pm_compliance: float
    schedule_compliance: float
    documentation_compliance: float
    total_contracts: int
    active_contracts: int
    at_risk_contracts: int
    monthly_history: List[Dict[str, Any]] = []

class RenewalPipelineItem(BaseModel):
    contract_id: str
    name: str
    customer: str
    type: str
    end_date: date
    days_to_expiry: int
    value: float
    compliance_score: float
    renewal_risk: str # LOW, MEDIUM, HIGH, CRITICAL
    risk_factors: List[str] = []
    recommended_strategy: str
