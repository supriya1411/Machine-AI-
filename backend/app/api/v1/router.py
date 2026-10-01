from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    users,
    sites,
    assets,
    service_calls,
    faults,
    fault_analytics,
    iot,
    maintenance,
    work_orders,
    contracts,
    alerts,
    action_center,
    dashboard,
    reports,
    ai_assistant,
    documents,
    audit_logs,
    health
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health & Observability"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & RBAC"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(action_center.router, prefix="/action-center", tags=["Action Center"])
api_router.include_router(assets.router, prefix="/assets", tags=["Assets & Health/Risk"])
api_router.include_router(iot.router, prefix="/iot", tags=["IoT & Telemetry Engine"])
api_router.include_router(faults.router, prefix="/faults", tags=["Fault Categories & Normalization"])
api_router.include_router(fault_analytics.router, prefix="/fault-analytics", tags=["Fault Analytics & MTBF"])
api_router.include_router(service_calls.router, prefix="/service-calls", tags=["Service Calls"])
api_router.include_router(maintenance.router, prefix="/maintenance", tags=["Preventive Maintenance & Cadence"])
api_router.include_router(work_orders.router, prefix="/work-orders", tags=["Work Orders"])
api_router.include_router(contracts.router, prefix="/contracts", tags=["AMC/CMC Contracts & Renewal Risk"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts & Severity"])
api_router.include_router(ai_assistant.router, prefix="/ai", tags=["AI Grounded Assistant"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports & Analytics"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents & Service Records"])
api_router.include_router(sites.router, prefix="/sites", tags=["Sites & Locations"])
api_router.include_router(users.router, prefix="/users", tags=["Users & Roles"])
api_router.include_router(audit_logs.router, prefix="/audit-logs", tags=["Audit Logs"])
