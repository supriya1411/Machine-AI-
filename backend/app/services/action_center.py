from datetime import datetime
from typing import List, Dict, Any, Optional

class ActionCenterService:
    """
    Action Center Prioritization Engine.
    Synthesizes active Alerts, Overdue PMs, Expiring Contracts, and High Risk Assets
    into an unified, urgent action list sorted by severity.
    """

    SEVERITY_ORDER = {
        "CRITICAL": 0,
        "HIGH": 1,
        "MEDIUM": 2,
        "LOW": 3
    }

    @classmethod
    def prioritize_actions(
        cls,
        active_alerts: List[Dict[str, Any]],
        overdue_pms: List[Dict[str, Any]],
        expiring_contracts: List[Dict[str, Any]],
        high_risk_assets: List[Dict[str, Any]],
        filter_category: Optional[str] = "ALL"
    ) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []

        # 1. Action Items from Active Alerts
        for alert in active_alerts:
            # Skip resolved
            if alert.get("status") == "RESOLVED":
                continue

            alert_type = alert.get("type", "SYSTEM")
            category_type = "ENVIRONMENTAL" if "IOT" in alert_type or "ENVIRONMENTAL" in alert_type else "ASSET_DEGRADATION"
            if "PM" in alert_type:
                category_type = "OVERDUE_PM"
            elif "CONTRACT" in alert_type:
                category_type = "CONTRACT_EXPIRY"

            cta = "INSPECT"
            if category_type == "OVERDUE_PM":
                cta = "SCHEDULE_PM"
            elif category_type == "CONTRACT_EXPIRY":
                cta = "RENEW_CONTRACT"
            elif alert.get("severity") == "CRITICAL":
                cta = "DISPATCH_ENGINEER"

            items.append({
                "id": f"act-alert-{alert.get('id')}",
                "priority": alert.get("severity", "MEDIUM"),
                "type": category_type,
                "entity_type": "ASSET" if alert.get("asset_id") else ("CONTRACT" if alert.get("contract_id") else "SYSTEM"),
                "entity_id": alert.get("asset_id") or alert.get("contract_id") or alert.get("id"),
                "asset_name": alert.get("asset_name") or alert.get("title"),
                "issue": alert.get("title"),
                "risk_level": alert.get("severity"),
                "reason": alert.get("reason"),
                "recommended_action": alert.get("recommended_action"),
                "cta": cta,
                "created_at": alert.get("created_at") or datetime.utcnow(),
                "metadata": {
                    "alert_id": alert.get("id"),
                    "current_value": alert.get("current_value"),
                    "threshold": alert.get("threshold"),
                    "duration": alert.get("duration")
                }
            })

        # 2. Action Items from Overdue PMs
        for pm in overdue_pms:
            items.append({
                "id": f"act-pm-{pm.get('id')}",
                "priority": "HIGH",
                "type": "OVERDUE_PM",
                "entity_type": "MAINTENANCE",
                "entity_id": pm.get("id"),
                "asset_name": pm.get("asset_name"),
                "issue": f"Preventive Maintenance Overdue ({pm.get('pm_type')})",
                "risk_level": "HIGH",
                "reason": f"PM scheduled for {pm.get('scheduled_date')} has not been executed",
                "recommended_action": "Assign field engineer and generate work order",
                "cta": "SCHEDULE_PM",
                "created_at": datetime.utcnow(),
                "metadata": {
                    "scheduled_date": str(pm.get("scheduled_date")),
                    "pm_type": pm.get("pm_type")
                }
            })

        # 3. Action Items from Expiring Contracts
        for contract in expiring_contracts:
            days = contract.get("days_to_expiry", 0)
            priority = "CRITICAL" if days <= 15 else "HIGH"
            items.append({
                "id": f"act-contract-{contract.get('id')}",
                "priority": priority,
                "type": "CONTRACT_EXPIRY",
                "entity_type": "CONTRACT",
                "entity_id": contract.get("id"),
                "asset_name": f"{contract.get('name')} ({contract.get('customer')})",
                "issue": f"Contract Expiry in {days} Days",
                "risk_level": priority,
                "reason": f"{contract.get('type')} contract expires on {contract.get('end_date')}",
                "recommended_action": contract.get("recommended_strategy", "Begin renewal review"),
                "cta": "RENEW_CONTRACT",
                "created_at": datetime.utcnow(),
                "metadata": {
                    "contract_id": contract.get("contract_id"),
                    "end_date": str(contract.get("end_date")),
                    "value": contract.get("value")
                }
            })

        # Sort by Priority (CRITICAL first, then HIGH, etc.)
        items.sort(key=lambda x: cls.SEVERITY_ORDER.get(x["priority"], 99))

        # Filter if requested
        if filter_category:
            filter_cat = filter_category.upper()
            if filter_cat == "CRITICAL":
                items = [i for i in items if i["priority"] == "CRITICAL"]
            elif filter_cat == "HIGH":
                items = [i for i in items if i["priority"] in ("CRITICAL", "HIGH")]
            elif filter_cat == "PM":
                items = [i for i in items if i["type"] == "OVERDUE_PM"]
            elif filter_cat in ("CONTRACT", "CONTRACTS"):
                items = [i for i in items if i["type"] == "CONTRACT_EXPIRY"]

        return items
