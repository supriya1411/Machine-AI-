from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import io
import csv

class ReportService:
    """
    Service for generating comprehensive enterprise reports and CSV exports:
    - Asset Health
    - Fault Analysis
    - Environmental Monitoring
    - PM Compliance
    - Contract Compliance
    - Renewal Risk
    """

    @staticmethod
    def generate_csv_export(report_type: str, records: List[Dict[str, Any]]) -> str:
        """
        Exports structured records into CSV format.
        """
        if not records:
            return "No records available for export\n"

        output = io.StringIO()
        headers = list(records[0].keys())
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        for row in records:
            writer.writerow({k: (str(v) if v is not None else "") for k, v in row.items()})
        return output.getvalue()
