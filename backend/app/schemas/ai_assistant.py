from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel

class AiQueryRequest(BaseModel):
    question: str
    context_asset_id: Optional[str] = None
    session_id: Optional[str] = None

class AiEvidenceItem(BaseModel):
    source: str # e.g. "Asset EQ-102 Service History", "IoT Sensor Stream", "Contract AMC-2025"
    type: str # FAULT_RECORD, SENSOR_READING, PM_RECORD, CONTRACT_RECORD
    timestamp: Optional[str] = None
    detail: str

class AiQueryResponse(BaseModel):
    answer: str
    evidence: List[AiEvidenceItem] = []
    recommended_actions: List[str] = []
    confidence_score: float = 0.95
    grounded_in_db: bool = True
    model_used: str = "aurum-grounded-intelligence"

class ReportGenerateRequest(BaseModel):
    title: str
    type: str # ASSET_HEALTH, FAULT_ANALYSIS, ENVIRONMENTAL_MONITORING, PM_COMPLIANCE, CONTRACT_COMPLIANCE, RENEWAL_RISK
    format: str = "JSON" # JSON, CSV, PDF
    filters: Dict[str, Any] = {}

class ReportResponse(BaseModel):
    id: str
    title: str
    type: str
    created_at: datetime
    data: Dict[str, Any] = {}
    summary: str
    download_url: Optional[str] = None

class DocumentResponse(BaseModel):
    id: str
    name: str
    type: str
    entity_type: str
    entity_id: str
    uploaded_by_name: Optional[str] = None
    uploaded_at: datetime
    file_size_kb: Optional[int] = 128
    download_url: str

    class Config:
        from_attributes = True

class AuditLogResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    metadata_: Optional[Dict[str, Any]] = None
    timestamp: datetime

    class Config:
        from_attributes = True
