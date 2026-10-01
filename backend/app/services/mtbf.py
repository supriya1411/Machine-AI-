from datetime import datetime
from typing import List, Dict, Any, Optional

class MtbfService:
    """
    Computes rigorous Mean Time Between Failures (MTBF) and interval statistics.
    Prevents generating fake ML numbers when data is insufficient.
    """

    @staticmethod
    def calculate_mtbf_for_dates(failure_dates: List[datetime]) -> Dict[str, Any]:
        """
        Calculates MTBF = total failure interval time / number of intervals.
        Requires at least 2 failure timestamps to form at least 1 interval.
        """
        sorted_dates = sorted(failure_dates)
        count = len(sorted_dates)

        if count < 2:
            return {
                "has_sufficient_data": False,
                "total_failures": count,
                "intervals_count": 0,
                "failure_intervals_hours": [],
                "mtbf_hours": None,
                "average_failure_interval_hours": None,
                "trend": "INSUFFICIENT_DATA",
                "reason": "At least 2 documented failure events required to calculate MTBF interval"
            }

        intervals_hours: List[float] = []
        for i in range(1, count):
            diff = (sorted_dates[i] - sorted_dates[i-1]).total_seconds() / 3600.0
            intervals_hours.append(round(diff, 2))

        total_interval_time = sum(intervals_hours)
        number_of_intervals = len(intervals_hours)
        mtbf = round(total_interval_time / number_of_intervals, 2)

        # Trend analysis (if 3 or more intervals)
        trend = "STABLE"
        if len(intervals_hours) >= 3:
            first_half = sum(intervals_hours[:len(intervals_hours)//2]) / (len(intervals_hours)//2)
            second_half = sum(intervals_hours[len(intervals_hours)//2:]) / (len(intervals_hours) - len(intervals_hours)//2)
            if second_half < first_half * 0.8:
                trend = "DEGRADING" # intervals are getting shorter (failing more often)
            elif second_half > first_half * 1.2:
                trend = "IMPROVING" # intervals are getting longer

        return {
            "has_sufficient_data": True,
            "total_failures": count,
            "intervals_count": number_of_intervals,
            "failure_intervals_hours": intervals_hours,
            "mtbf_hours": mtbf,
            "average_failure_interval_hours": mtbf,
            "trend": trend,
            "reason": None
        }
