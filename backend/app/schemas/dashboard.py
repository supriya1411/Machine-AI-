from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.schemas.alert import ActionCenterItem
from app.schemas.contract import RenewalPipelineItem

class KpiMetrics(BaseModel):
    total_assets: int
    operational_assets: int
    high_risk_assets: int
    critical_alerts_count: int
    overall_health_index: float
    pm_compliance_rate: float
    active_contracts_value: float
    contracts_expiring_30_days: int

class HealthDistribution(BaseModel):
    optimal: int # 85-100
    good: int # 70-84
    fair: int # 50-69
    critical: int # 0-49

class LocationAssetCount(BaseModel):
    site_id: str
    site_name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    total_assets: int
    high_risk_assets: int
    status: str

class LiveSystemStatus(BaseModel):
    iot_gateway_status: str # HEALTHY
    anomaly_detection_latency_ms: float
    sensors_online: int
    sensors_offline: int
    sensors_warning: int
    background_worker_status: str # ACTIVE
    last_sync_timestamp: str

class HighRiskEquipmentItem(BaseModel):
    id: str
    asset_id: str
    name: str
    category: str
    site_name: str
    health_score: int
    risk_score: int
    risk_level: str
    primary_risk_driver: str
    recommended_action: str

class IotSummary(BaseModel):
    total_sensors: int
    online_count: int
    anomalies_active: int
    average_ambient_temp: float
    average_ambient_humidity: float

class PmSummary(BaseModel):
    scheduled_this_month: int
    completed_this_month: int
    overdue_count: int
    cadence_compliance_rate: float

class AiWidgetData(BaseModel):
    daily_insight: str
    top_predicted_vulnerability: str
    action_item_highlight: str

class DashboardResponse(BaseModel):
    kpis: KpiMetrics
    health_distribution: HealthDistribution
    assets_by_location: List[LocationAssetCount]
    top_faults: List[Dict[str, Any]]
    live_system_status: LiveSystemStatus
    action_center: List[ActionCenterItem]
    high_risk_equipment: List[HighRiskEquipmentItem]
    iot_summary: IotSummary
    pm_summary: PmSummary
    contract_renewal_pipeline: List[RenewalPipelineItem]
    ai_widget: AiWidgetData
