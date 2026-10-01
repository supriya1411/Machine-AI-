from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime

from app.db.session import get_db
from app.models.asset import Asset
from app.models.site import Site
from app.models.contract import Contract
from app.models.maintenance import Maintenance
from app.models.service_call import ServiceCall
from app.schemas.common import ApiResponse
from app.services.reports import ReportService

router = APIRouter()

@router.get("/summary", summary="Generate Structured Analytics Summary Report")
async def get_report_summary(
    report_type: str = Query(..., description="ASSET_HEALTH, FAULT_ANALYSIS, ENVIRONMENTAL, PM_COMPLIANCE, CONTRACT_COMPLIANCE, RENEWAL_RISK"),
    db: AsyncSession = Depends(get_db)
):
    rep_type = report_type.upper()

    if rep_type == "ASSET_HEALTH":
        res = await db.execute(select(Asset, Site.name.label("site_name")).outerjoin(Site, Asset.site_id == Site.id))
        rows = res.all()
        records = [{
            "asset_id": a.asset_id,
            "name": a.name,
            "category": a.category,
            "site": s_name or "N/A",
            "health_score": a.health_score,
            "risk_score": a.risk_score,
            "risk_level": a.risk_level,
            "status": a.status
        } for a, s_name in rows]

        return ApiResponse(success=True, data={
            "report_type": rep_type,
            "total_assets": len(records),
            "generated_at": datetime.utcnow().isoformat(),
            "records": records[:50]
        })

    elif rep_type == "CONTRACT_COMPLIANCE" or rep_type == "RENEWAL_RISK":
        res = await db.execute(select(Contract))
        contracts = res.scalars().all()
        records = [{
            "contract_id": c.contract_id,
            "name": c.name,
            "customer": c.customer,
            "type": c.type,
            "value": c.value,
            "compliance_score": c.compliance_score,
            "renewal_risk": c.renewal_risk,
            "end_date": str(c.end_date)
        } for c in contracts]

        return ApiResponse(success=True, data={
            "report_type": rep_type,
            "total_contracts": len(records),
            "generated_at": datetime.utcnow().isoformat(),
            "records": records
        })

    else:
        # PM or Fault summary
        res = await db.execute(select(Maintenance).limit(50))
        pms = res.scalars().all()
        records = [{
            "id": p.id,
            "asset_id": p.asset_id,
            "pm_type": p.pm_type,
            "scheduled_date": str(p.scheduled_date),
            "status": p.status
        } for p in pms]

        return ApiResponse(success=True, data={
            "report_type": rep_type,
            "total_records": len(records),
            "generated_at": datetime.utcnow().isoformat(),
            "records": records
        })

@router.get("/export/csv", summary="Export Operational Dataset to CSV Format")
async def export_csv(
    report_type: str = Query(..., description="ASSET_HEALTH, FAULT_ANALYSIS, PM_COMPLIANCE, CONTRACTS"),
    db: AsyncSession = Depends(get_db)
):
    rep_type = report_type.upper()
    records = []

    if rep_type == "ASSET_HEALTH":
        res = await db.execute(select(Asset, Site.name.label("site_name")).outerjoin(Site, Asset.site_id == Site.id))
        rows = res.all()
        records = [{
            "Asset ID": a.asset_id,
            "Asset Name": a.name,
            "Category": a.category,
            "Site Location": s_name or "N/A",
            "Health Score": a.health_score,
            "Risk Score": a.risk_score,
            "Risk Level": a.risk_level,
            "Criticality": a.criticality,
            "Status": a.status
        } for a, s_name in rows]

    elif rep_type in ("CONTRACTS", "RENEWAL_RISK"):
        res = await db.execute(select(Contract))
        contracts = res.scalars().all()
        records = [{
            "Contract ID": c.contract_id,
            "Name": c.name,
            "Customer": c.customer,
            "Type": c.type,
            "Value ($)": c.value,
            "Start Date": str(c.start_date),
            "End Date": str(c.end_date),
            "Compliance Score (%)": c.compliance_score,
            "Renewal Risk": c.renewal_risk
        } for c in contracts]

    elif rep_type == "FAULT_ANALYSIS":
        res = await db.execute(select(ServiceCall, Asset.name.label("asset_name")).join(Asset, ServiceCall.asset_id == Asset.id))
        rows = res.all()
        records = [{
            "Date": str(sc.date),
            "Asset": a_name,
            "Raw Fault Text": sc.raw_fault,
            "Normalized Code": sc.fault_code,
            "Severity": sc.severity,
            "Downtime Hours": sc.downtime,
            "Resolution Notes": sc.resolution
        } for sc, a_name in rows]

    else:
        res = await db.execute(select(Maintenance, Asset.name.label("asset_name")).join(Asset, Maintenance.asset_id == Asset.id))
        rows = res.all()
        records = [{
            "Asset": a_name,
            "PM Type": pm.pm_type,
            "Scheduled Date": str(pm.scheduled_date),
            "Completed Date": str(pm.completed_date) if pm.completed_date else "N/A",
            "Status": pm.status
        } for pm, a_name in rows]

    csv_content = ReportService.generate_csv_export(rep_type, records)

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="aurum_{rep_type.lower()}_{datetime.utcnow().strftime("%Y%m%d")}.csv"'}
    )
