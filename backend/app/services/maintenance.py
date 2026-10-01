from datetime import date, timedelta
from typing import List, Dict, Any, Optional

class MaintenanceService:
    """
    Evaluates Preventive Maintenance (PM) schedules, completion history,
    and cadence compliance (checking spacing/intervals between PMs, not just count).
    """

    @staticmethod
    def evaluate_pm_cadence(
        required_frequency_days: int,
        completed_dates: List[date],
        tolerance_percentage: float = 0.20 # allowable deviation e.g. +/- 20%
    ) -> Dict[str, Any]:
        """
        Cadence Compliance Engine.
        Validates whether actual PM events occurred within the required interval cadence.
        E.g. if required every 90 days, intervals must be ~90 days. A gap of 130 days is a violation.
        """
        sorted_dates = sorted(completed_dates)
        if len(sorted_dates) < 2:
            return {
                "cadence_compliance": True if len(sorted_dates) == 1 else False,
                "violation": False if len(sorted_dates) == 1 else True,
                "reason": "Insufficient historical PM records to establish cadence" if len(sorted_dates) == 0 else "Only single PM recorded; cadence established on subsequent visits",
                "actual_intervals_days": [],
                "max_gap_days": 0,
                "evaluation_detail": "Minimum 2 completed PM dates needed for cadence evaluation"
            }

        intervals_days: List[int] = []
        max_allowed_gap = int(required_frequency_days * (1 + tolerance_percentage))
        min_allowed_gap = int(required_frequency_days * (1 - tolerance_percentage))

        violation_found = False
        violation_reasons: List[str] = []

        for i in range(1, len(sorted_dates)):
            gap = (sorted_dates[i] - sorted_dates[i-1]).days
            intervals_days.append(gap)

            if gap > max_allowed_gap:
                violation_found = True
                violation_reasons.append(
                    f"Interval between PM #{i} ({sorted_dates[i-1]}) and PM #{i+1} ({sorted_dates[i]}) was {gap} days (max allowable: {max_allowed_gap} days)"
                )
            elif gap < min_allowed_gap and gap < (required_frequency_days // 2):
                # Unbalanced clustered maintenance (e.g. Day 30 and Day 40 when required is 90)
                violation_reasons.append(
                    f"Clustered maintenance: Interval between PM #{i} and #{i+1} was only {gap} days for a {required_frequency_days}-day schedule"
                )

        max_gap = max(intervals_days) if intervals_days else 0

        if violation_found:
            return {
                "cadence_compliance": False,
                "violation": True,
                "reason": "Required maintenance interval was not maintained: " + "; ".join(violation_reasons),
                "actual_intervals_days": intervals_days,
                "max_gap_days": max_gap,
                "evaluation_detail": f"Target cadence: every {required_frequency_days} days. Max observed interval: {max_gap} days."
            }

        return {
            "cadence_compliance": True,
            "violation": False,
            "reason": None,
            "actual_intervals_days": intervals_days,
            "max_gap_days": max_gap,
            "evaluation_detail": f"All PM visits maintained cadence within {tolerance_percentage*100}% tolerance of {required_frequency_days} days."
        }
