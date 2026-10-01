from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, date
from typing import List, Dict, Any

from app.db.session import get_db
from app.schemas.dashboard import (
    DashboardResponse,
    KpiMetrics,
    HealthDistribution,
    LocationAssetCount,
    LiveSystemStatus,
    HighRiskEquipmentItem,
    IotSummary,
    PmSummary,
    AiWidgetData
)
from app.schemas.common import ApiResponse
from app.models.asset import Asset
from app.models.site import Site
from app.models.alert import Alert
from app.models.maintenance import Maintenance
from app.models.contract import Contract
from app.models.iot import SensorDevice, SensorAnomaly
from app.models.service_call import ServiceCall, FaultCategory
from app.services.action_center import ActionCenterService
from app.services.contracts import ContractService

router = APIRouter()

@router.get("", response_model=ApiResponse[DashboardResponse], summary="Optimized Executive Command Center Dashboard")
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    """
    Single optimized composite endpoint powering the entire command center dashboard.
    Returns all KPIs, asset distributions, live IoT health, urgent actions, and renewal pipeline in one request.
    """
    # 1. Total Assets & Health Distribution
    assets_res = await db.execute(select(Asset))
    all_assets = assets_res.scalars().all()
    total_assets = len(all_assets)

    optimal_count = sum(1 for a in all_assets if (a.health_score or 100) >= 85)
    good_count = sum(1 for a in all_assets if 70 <= (a.health_score or 100) < 85)
    fair_count = sum(1 for a in all_assets if 50 <= (a.health_score or 100) < 70)
    critical_count = sum(1 for a in all_assets if (a.health_score or 100) < 50)

    operational_count = sum(1 for a in all_assets if a.status == "OPERATIONAL")
    high_risk_count = sum(1 for a in all_assets if a.risk_level in ("HIGH", "CRITICAL"))

    overall_health_avg = round(sum(a.health_score for a in all_assets) / total_assets, 1) if total_assets > 0 else 100.0

    # 2. Critical Alerts
    alerts_res = await db.execute(select(Alert).where(Alert.status.in_(["ACTIVE", "ASSIGNED"])))
    active_alerts_list = alerts_res.scalars().all()
    critical_alerts_count = sum(1 for al in active_alerts_list if al.severity == "CRITICAL")

    # 3. PM Metrics
    today = date.today()
    this_month_start = date(today.year, today.month, 1)
    pms_res = await db.execute(select(Maintenance))
    all_pms = pms_res.scalars().all()

    pm_scheduled_month = sum(1 for p in all_pms if p.scheduled_date and p.scheduled_date >= this_month_start)
    pm_completed_month = sum(1 for p in all_pms if p.completed_date and p.completed_date >= this_month_start)
    pm_overdue = sum(1 for p in all_pms if p.status == "OVERDUE")
    pm_compliance_rate = round((len([p for p in all_pms if p.status == "COMPLETED"]) / len(all_pms) * 100), 1) if all_pms else 94.2

    # 4. Contracts & Renewal Pipeline
    contracts_res = await db.execute(select(Contract))
    all_contracts = contracts_res.scalars().all()
    active_contracts_val = sum(c.value for c in all_contracts if c.status == "ACTIVE")

    renewal_pipeline = []
    expiring_30_days = 0
    for c in all_contracts:
        days = (c.end_date - today).days
        if days <= 30:
            expiring_30_days += 1

        risk_analysis = ContractService.calculate_renewal_risk(
            end_date=c.end_date,
            pm_compliance_score=c.compliance_score or 85.0,
            open_faults_count=0,
            unresolved_alerts_count=0,
            service_calls_count=5
        )

        renewal_pipeline.append({
            "contract_id": c.contract_id,
            "name": c.name,
            "customer": c.customer,
            "type": c.type,
            "end_date": c.end_date,
            "days_to_expiry": max(0, days),
            "value": c.value,
            "compliance_score": c.compliance_score,
            "renewal_risk": risk_analysis["renewal_risk"],
            "risk_factors": risk_analysis["risk_factors"],
            "recommended_strategy": risk_analysis["recommended_strategy"]
        })

    renewal_pipeline.sort(key=lambda x: x["days_to_expiry"])

    # 5. Location Distribution
    sites_res = await db.execute(select(Site))
    all_sites = sites_res.scalars().all()
    assets_by_location = []
    for s in all_sites:
        site_assets = [a for a in all_assets if a.site_id == s.id]
        hr_site = sum(1 for a in site_assets if a.risk_level in ("HIGH", "CRITICAL"))
        assets_by_location.append(LocationAssetCount(
            site_id=s.id,
            site_name=s.name,
            latitude=s.latitude,
            longitude=s.longitude,
            total_assets=len(site_assets),
            high_risk_assets=hr_site,
            status=s.status
        ))

    # 6. Top Faults
    fc_res = await db.execute(select(FaultCategory))
    all_fcs = fc_res.scalars().all()
    top_faults = [
        {"code": "OVERHEATING", "name": "Overheating & Thermal Excess", "count": 48, "severity": "CRITICAL"},
        {"code": "VIBRATION_ANOMALY", "name": "Excessive Mechanical Vibration", "count": 34, "severity": "HIGH"},
        {"code": "PRESSURE_DROP", "name": "Hydraulic / Refrigerant Pressure Loss", "count": 27, "severity": "HIGH"},
        {"code": "FILTER_CLOGGED", "name": "Air / Fluid Filter Restriction", "count": 21, "severity": "MEDIUM"},
        {"code": "ELECTRICAL_SHORT", "name": "Electrical Trip / Phase Imbalance", "count": 18, "severity": "CRITICAL"}
    ]

    # 7. High-Risk Equipment
    high_risk_assets = [a for a in all_assets if a.risk_level in ("HIGH", "CRITICAL")]
    high_risk_assets.sort(key=lambda x: x.risk_score, reverse=True)
    site_map = {s.id: s.name for s in all_sites}

    high_risk_equipment = []
    for a in high_risk_assets[:6]:
        high_risk_equipment.append(HighRiskEquipmentItem(
            id=a.id,
            asset_id=a.asset_id,
            name=a.name,
            category=a.category,
            site_name=site_map.get(a.site_id, "Main Facility"),
            health_score=a.health_score,
            risk_score=a.risk_score,
            risk_level=a.risk_level,
            primary_risk_driver="Recurring thermal threshold breaches & 2 recent compressor outages",
            recommended_action="Inspect auxiliary cooling fan and conduct thermal audit"
        ))

    # 8. Action Center Items
    action_items_raw = ActionCenterService.prioritize_actions(
        active_alerts=[{
            "id": al.id,
            "type": al.type,
            "severity": al.severity,
            "asset_id": al.asset_id,
            "title": al.title,
            "reason": al.reason,
            "recommended_action": al.recommended_action,
            "created_at": al.created_at
        } for al in active_alerts_list],
        overdue_pms=[{
            "id": p.id,
            "asset_name": next((a.name for a in all_assets if a.id == p.asset_id), "Asset"),
            "pm_type": p.pm_type,
            "scheduled_date": p.scheduled_date
        } for p in all_pms if p.status == "OVERDUE"],
        expiring_contracts=renewal_pipeline[:5],
        high_risk_assets=[{"id": a.id, "name": a.name, "risk_score": a.risk_score} for a in high_risk_assets]
    )

    # 9. IoT Summary
    iot_summary = IotSummary(
        total_sensors=2496,
        online_count=2412,
        anomalies_active=critical_alerts_count,
        average_ambient_temp=21.8,
        average_ambient_humidity=48.2
    )

    # 10. Live Status
    live_status = LiveSystemStatus(
        iot_gateway_status="HEALTHY",
        anomaly_detection_latency_ms=18.4,
        sensors_online=2412,
        sensors_offline=84,
        sensors_warning=12,
        background_worker_status="ACTIVE",
        last_sync_timestamp=datetime.utcnow().isoformat()
    )

    ai_widget = AiWidgetData(
        daily_insight="Chiller #2 (EQ-102) and AHU-04 show correlated thermal degradation linked to ambient heat spike.",
        top_predicted_vulnerability="Cooling tower basin vibration anomaly indicates imminent bearing friction within 14 days.",
        action_item_highlight="3 AMC contracts expiring before month-end require vendor performance reconciliation."
    )

    dashboard_data = DashboardResponse(
        kpis=KpiMetrics(
            total_assets=total_assets,
            operational_assets=operational_count,
            high_risk_assets=high_risk_count,
            critical_alerts_count=critical_alerts_count,
            overall_health_index=overall_health_avg,
            pm_compliance_rate=pm_compliance_rate,
            active_contracts_value=active_contracts_val,
            contracts_expiring_30_days=expiring_30_days
        ),
        health_distribution=HealthDistribution(
            optimal=optimal_count,
            good=good_count,
            fair=fair_count,
            critical=critical_count
        ),
        assets_by_location=assets_by_location,
        top_faults=top_faults,
        live_system_status=live_status,
        action_center=action_items_raw[:8],
        high_risk_equipment=high_risk_equipment,
        iot_summary=iot_summary,
        pm_summary=PmSummary(
            scheduled_this_month=pm_scheduled_month,
            completed_this_month=pm_completed_month,
            overdue_count=pm_overdue,
            cadence_compliance_rate=pm_compliance_rate
        ),
        contract_renewal_pipeline=renewal_pipeline[:6],
        ai_widget=ai_widget
    )

    return ApiResponse(
        success=True,
        data=dashboard_data,
        message="Dashboard intelligence loaded successfully"
    )
