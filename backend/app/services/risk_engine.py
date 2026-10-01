from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from app.core.config import settings

class RiskEngine:
    """
    Asset Health + Risk Engine for AURUM Service Intelligence.
    Produces deterministic, explainable multi-factor scoring grounded in operational data.
    Clearly distinguishes heuristic risk, anomaly detection, statistical intervals, and ML readiness.
    """

    CRITICALITY_WEIGHTS = {
        "LOW": 0.6,
        "MEDIUM": 1.0,
        "HIGH": 1.4,
        "CRITICAL": 1.8
    }

    SEVERITY_WEIGHTS = {
        "LOW": 5,
        "MEDIUM": 15,
        "HIGH": 30,
        "CRITICAL": 50
    }

    @classmethod
    def calculate_asset_health_and_risk(
        cls,
        asset_criticality: str,
        service_calls: List[Dict[str, Any]],
        sensor_anomalies: List[Dict[str, Any]],
        active_alerts: List[Dict[str, Any]],
        pm_compliance_flag: bool,
        mtbf_trend: Optional[str] = None, # "IMPROVING", "STABLE", "DEGRADING", "INSUFFICIENT_DATA"
    ) -> Tuple[int, int, str, List[Dict[str, str]], List[str], bool, Optional[str]]:
        """
        Returns:
        (health_score, risk_score, risk_level, factors, recommended_actions, prediction_available, prediction_reason)
        """
        now = datetime.utcnow()
        factors: List[Dict[str, str]] = []
        recommended_actions: List[str] = []

        total_risk_penalty = 0.0

        # 1. Recent Failures Analysis (Failures in last 30 & 90 days)
        failures_last_30_days = [
            call for call in service_calls
            if call.get("date") and (now - call["date"]).days <= 30
        ]
        failures_last_90_days = [
            call for call in service_calls
            if call.get("date") and (now - call["date"]).days <= 90
        ]

        if len(failures_last_30_days) >= 3:
            impact = "CRITICAL" if len(failures_last_30_days) >= 4 else "HIGH"
            penalty = 35.0
            total_risk_penalty += penalty
            factors.append({
                "factor": "Recent failure frequency",
                "value": f"{len(failures_last_30_days)} service interruptions in past 30 days",
                "impact": impact
            })
            recommended_actions.append("Perform root-cause diagnostics on repeated failure subsystem")
        elif len(failures_last_30_days) >= 1:
            total_risk_penalty += 15.0
            factors.append({
                "factor": "Recent failure",
                "value": f"{len(failures_last_30_days)} failure in past 30 days",
                "impact": "MEDIUM"
            })
        elif len(failures_last_90_days) >= 2:
            total_risk_penalty += 10.0
            factors.append({
                "factor": "Quarterly failure history",
                "value": f"{len(failures_last_90_days)} failures in past 90 days",
                "impact": "LOW"
            })

        # 2. Fault Severity Weighting
        has_critical_fault = any(c.get("severity") == "CRITICAL" for c in failures_last_90_days)
        has_high_fault = any(c.get("severity") == "HIGH" for c in failures_last_90_days)
        if has_critical_fault:
            total_risk_penalty += 20.0
            factors.append({
                "factor": "Fault severity profile",
                "value": "History of CRITICAL downtime events",
                "impact": "CRITICAL"
            })
            recommended_actions.append("Verify circuit protection and structural fail-safes")
        elif has_high_fault:
            total_risk_penalty += 10.0
            factors.append({
                "factor": "Fault severity profile",
                "value": "History of HIGH severity faults",
                "impact": "HIGH"
            })

        # 3. Environmental Anomaly Analysis (IoT Breaches)
        unresolved_anomalies = [a for a in sensor_anomalies if a.get("resolved") != "TRUE"]
        critical_anomalies = [a for a in unresolved_anomalies if a.get("severity") == "CRITICAL"]
        if critical_anomalies:
            total_risk_penalty += 25.0
            factors.append({
                "factor": "IoT Environmental Breaches",
                "value": f"{len(critical_anomalies)} critical sensor threshold violations active",
                "impact": "CRITICAL"
            })
            recommended_actions.append("Inspect operating environment and thermal/power supply immediately")
        elif unresolved_anomalies:
            total_risk_penalty += 12.0
            factors.append({
                "factor": "IoT Environmental Warning",
                "value": f"{len(unresolved_anomalies)} active environmental sensor warnings",
                "impact": "MEDIUM"
            })

        # 4. Preventive Maintenance Compliance & Cadence
        if not pm_compliance_flag:
            total_risk_penalty += 18.0
            factors.append({
                "factor": "PM Cadence Violation",
                "value": "Scheduled maintenance interval was violated or missed",
                "impact": "HIGH"
            })
            recommended_actions.append("Schedule immediate preventive maintenance inspection")

        # 5. Active Unresolved Alerts
        crit_alerts = [a for a in active_alerts if a.get("severity") == "CRITICAL" and a.get("status") == "ACTIVE"]
        high_alerts = [a for a in active_alerts if a.get("severity") == "HIGH" and a.get("status") == "ACTIVE"]
        if crit_alerts:
            total_risk_penalty += 20.0
            factors.append({
                "factor": "Unresolved Critical Alerts",
                "value": f"{len(crit_alerts)} active critical alert(s) pending resolution",
                "impact": "CRITICAL"
            })
        elif high_alerts:
            total_risk_penalty += 10.0
            factors.append({
                "factor": "Unresolved High Alerts",
                "value": f"{len(high_alerts)} high alert(s) awaiting engineering sign-off",
                "impact": "HIGH"
            })

        # 6. MTBF Trend
        if mtbf_trend == "DEGRADING":
            total_risk_penalty += 12.0
            factors.append({
                "factor": "MTBF Degradation Trend",
                "value": "Mean Time Between Failures is declining rapidly",
                "impact": "HIGH"
            })
            recommended_actions.append("Conduct comprehensive overhaul due to shortening failure cycles")

        # 7. Criticality Multiplier
        crit_mult = cls.CRITICALITY_WEIGHTS.get(asset_criticality.upper(), 1.0)
        raw_risk = total_risk_penalty * crit_mult

        risk_score = int(min(100, max(0, round(raw_risk))))
        health_score = int(max(0, min(100, 100 - risk_score)))

        # Risk Level Classification
        if risk_score >= 70:
            risk_level = "CRITICAL"
        elif risk_score >= 50:
            risk_level = "HIGH"
        elif risk_score >= 25:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # ML Prediction Availability Gate (Section 4 requirement)
        # We require at least 3 historical failure events to run statistical/ML failure prediction
        if len(service_calls) < 3:
            prediction_available = False
            prediction_reason = "Insufficient historical failure data (minimum 3 service calls required for statistical failure modeling)"
        else:
            prediction_available = True
            prediction_reason = None

        if not recommended_actions:
            recommended_actions.append("Maintain standard scheduled inspection routine")

        return (
            health_score,
            risk_score,
            risk_level,
            factors,
            recommended_actions,
            prediction_available,
            prediction_reason
        )
