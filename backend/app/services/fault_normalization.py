import re
from typing import Tuple, Optional, Dict, List

DEFAULT_FAULT_TAXONOMY: Dict[str, Dict[str, Any]] = {
    "OVERHEATING": {
        "name": "Overheating & Thermal Excess",
        "severity": "CRITICAL",
        "keywords": [
            "high temp", "high temperature", "over heating", "overheating",
            "temperature high", "excess heat", "thermal trip", "hot running", "hot coil"
        ]
    },
    "VIBRATION_ANOMALY": {
        "name": "Excessive Mechanical Vibration",
        "severity": "HIGH",
        "keywords": [
            "shaking", "vibration", "vibrating", "bearing noise", "rattling",
            "imbalance", "misalignment", "abnormal rumble"
        ]
    },
    "PRESSURE_DROP": {
        "name": "Hydraulic / Refrigerant Pressure Loss",
        "severity": "HIGH",
        "keywords": [
            "low pressure", "pressure drop", "leakage", "refrigerant low",
            "loss of pressure", "hydraulic leak", "depressurized"
        ]
    },
    "ELECTRICAL_SHORT": {
        "name": "Electrical Trip / Phase Imbalance",
        "severity": "CRITICAL",
        "keywords": [
            "short circuit", "breaker trip", "tripped breaker", "blown fuse",
            "phase loss", "voltage drop", "sparking", "power surge"
        ]
    },
    "FILTER_CLOGGED": {
        "name": "Air / Fluid Filter Restriction",
        "severity": "MEDIUM",
        "keywords": [
            "clogged filter", "dirty filter", "air flow restricted", "intake blocked",
            "filter differential high", "choked filter"
        ]
    },
    "SENSOR_COMMUNICATION_LOSS": {
        "name": "Telemetry / Sensor Disconnect",
        "severity": "LOW",
        "keywords": [
            "sensor offline", "communication error", "no telemetry", "disconnected sensor",
            "signal loss", "iot timeout"
        ]
    },
    "LUBRICATION_FAILURE": {
        "name": "Lubrication Deficiency",
        "severity": "MEDIUM",
        "keywords": [
            "dry bearing", "lubrication low", "oil level low", "grease dried", "dry run"
        ]
    }
}

class FaultNormalizationService:
    """
    Normalizes unstructured, inconsistent technician service call notes
    into a structured taxonomy while keeping raw fault notes intact.
    """

    def __init__(self, taxonomy: Optional[Dict[str, Dict[str, Any]]] = None):
        self.taxonomy = taxonomy or DEFAULT_FAULT_TAXONOMY

    def normalize(self, raw_text: str) -> Tuple[str, str, str]:
        """
        Input: Raw text string from field technician.
        Returns: (fault_code, fault_name, severity)
        """
        if not raw_text:
            return "GENERAL_FAULT", "General Operational Fault", "MEDIUM"

        cleaned = raw_text.lower().strip()

        best_code = "GENERAL_FAULT"
        best_name = "General Operational Fault"
        best_severity = "MEDIUM"

        for code, meta in self.taxonomy.items():
            for kw in meta["keywords"]:
                # Match keyword as whole word or phrase
                pattern = r'\b' + re.escape(kw) + r'\b'
                if re.search(pattern, cleaned) or kw in cleaned:
                    return code, meta["name"], meta["severity"]

        return best_code, best_name, best_severity
