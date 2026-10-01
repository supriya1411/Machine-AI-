from datetime import date, timedelta
from typing import Dict, Any, List, Optional

class ContractService:
    """
    Contract Lifecycle, Compliance & Renewal Risk Engine.
    Evaluates AMC/CMC contracts, asset coverage, PM adherence, and risk scoring.
    """

    @staticmethod
    def calculate_renewal_risk(
        end_date: date,
        pm_compliance_score: float, # 0 - 100
        open_faults_count: int,
        unresolved_alerts_count: int,
        service_calls_count: int
    ) -> Dict[str, Any]:
        """
        Calculates renewal risk: LOW, MEDIUM, HIGH, CRITICAL.
        Based on expiry proximity, PM adherence, open tickets, and failure frequency.
        """
        today = date.today()
        days_to_expiry = (end_date - today).days

        risk_score = 0.0
        risk_factors: List[str] = []

        # 1. Expiry Proximity
        if days_to_expiry < 0:
            risk_score += 45.0
            risk_factors.append(f"Contract has EXPIRED ({-days_to_expiry} days overdue)")
        elif days_to_expiry <= 30:
            risk_score += 35.0
            risk_factors.append(f"Contract expiring in {days_to_expiry} days")
        elif days_to_expiry <= 60:
            risk_score += 20.0
            risk_factors.append(f"Contract expiring in {days_to_expiry} days")

        # 2. PM Compliance
        if pm_compliance_score < 75.0:
            risk_score += 30.0
            risk_factors.append(f"Low PM compliance ({pm_compliance_score:.1f}%)")
        elif pm_compliance_score < 90.0:
            risk_score += 15.0
            risk_factors.append(f"Moderate PM compliance gap ({pm_compliance_score:.1f}%)")

        # 3. Open Issues
        if open_faults_count > 0:
            penalty = min(25.0, open_faults_count * 8.0)
            risk_score += penalty
            risk_factors.append(f"{open_faults_count} open service fault(s) under warranty")

        if unresolved_alerts_count > 0:
            risk_score += min(15.0, unresolved_alerts_count * 5.0)
            risk_factors.append(f"{unresolved_alerts_count} active alert(s)")

        # Determine level
        if risk_score >= 60:
            renewal_risk = "CRITICAL"
            strategy = "Immediate vendor negotiation & SLA dispute review required"
        elif risk_score >= 40:
            renewal_risk = "HIGH"
            strategy = "Expedite renewal proposal and audit unresolved maintenance items"
        elif risk_score >= 20:
            renewal_risk = "MEDIUM"
            strategy = "Standard renewal quote request with updated equipment list"
        else:
            renewal_risk = "LOW"
            strategy = "Auto-renewal eligible; schedule routine contract review"

        return {
            "days_to_expiry": max(0, days_to_expiry),
            "renewal_risk": renewal_risk,
            "risk_score": int(min(100, risk_score)),
            "risk_factors": risk_factors if risk_factors else ["Healthy compliance and ample contract validity"],
            "recommended_strategy": strategy
        }
