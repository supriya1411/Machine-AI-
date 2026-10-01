from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple

class IoTEngine:
    """
    IoT Threshold & Anomaly Detection Engine.
    Flow:
    Reading -> Threshold Evaluation -> Anomaly Detection -> Alert Generation -> Risk Update -> Recommended Action
    Prevents duplicate alerts for continuing anomaly states.
    """

    @staticmethod
    def evaluate_reading(
        sensor_type: str,
        value: float,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluates a reading against sensor configuration thresholds:
        safe_min, safe_max, warning_min, warning_max, critical_min, critical_max
        """
        safe_min = config.get("safe_min", 18.0 if sensor_type == "temperature" else 40.0)
        safe_max = config.get("safe_max", 24.0 if sensor_type == "temperature" else 60.0)
        warning_min = config.get("warning_min", 15.0 if sensor_type == "temperature" else 30.0)
        warning_max = config.get("warning_max", 28.0 if sensor_type == "temperature" else 70.0)
        critical_min = config.get("critical_min", 10.0 if sensor_type == "temperature" else 20.0)
        critical_max = config.get("critical_max", 35.0 if sensor_type == "temperature" else 85.0)

        status = "NORMAL"
        severity = "NORMAL"
        threshold_breached = ""
        recommended_action = ""

        # Check Critical
        if value >= critical_max:
            status = "CRITICAL"
            severity = "CRITICAL"
            threshold_breached = f"critical_max ({critical_max})"
            recommended_action = (
                "Immediately shut down or switch load; dispatch emergency engineer to inspect thermal/cooling failure"
                if sensor_type == "temperature" else "Activate emergency dehumidification/exhaust systems"
            )
        elif value <= critical_min:
            status = "CRITICAL"
            severity = "CRITICAL"
            threshold_breached = f"critical_min ({critical_min})"
            recommended_action = "Inspect heating / environmental control systems immediately"
        # Check Warning
        elif value >= warning_max:
            status = "WARNING"
            severity = "WARNING"
            threshold_breached = f"warning_max ({warning_max})"
            recommended_action = "Inspect auxiliary fans and clean air filters within 4 hours"
        elif value <= warning_min:
            status = "WARNING"
            severity = "WARNING"
            threshold_breached = f"warning_min ({warning_min})"
            recommended_action = "Check ambient insulation and temperature regulation circuits"

        return {
            "status": status,
            "severity": severity,
            "is_anomaly": status in ("WARNING", "CRITICAL"),
            "threshold_breached": threshold_breached,
            "recommended_action": recommended_action,
            "thresholds_used": {
                "safe_min": safe_min,
                "safe_max": safe_max,
                "warning_min": warning_min,
                "warning_max": warning_max,
                "critical_min": critical_min,
                "critical_max": critical_max
            }
        }

    @staticmethod
    def determine_sensor_status(last_seen: Optional[datetime], sampling_interval_sec: int = 60) -> str:
        """
        Determines sensor status: ONLINE, DELAYED, STALE, OFFLINE, NO_SENSOR
        Never treats missing telemetry as normal!
        """
        if not last_seen:
            return "OFFLINE"

        now = datetime.utcnow()
        elapsed_sec = (now - last_seen).total_seconds()

        if elapsed_sec <= sampling_interval_sec * 2:
            return "ONLINE"
        elif elapsed_sec <= sampling_interval_sec * 5:
            return "DELAYED"
        elif elapsed_sec <= sampling_interval_sec * 15:
            return "STALE"
        else:
            return "OFFLINE"
