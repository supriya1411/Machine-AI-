import unittest
from datetime import datetime, date, timedelta
from app.services.risk_engine import RiskEngine
from app.services.fault_normalization import FaultNormalizationService
from app.services.mtbf import MtbfService
from app.services.iot_engine import IoTEngine
from app.services.maintenance import MaintenanceService
from app.services.contracts import ContractService
from app.services.action_center import ActionCenterService

class TestAurumIntelligenceEngines(unittest.TestCase):

    def test_risk_engine_calculation(self):
        """
        Verify multi-factor explainable risk engine:
        - Criticality weighting
        - Penalties for recent failures, anomalies, overdue PM
        - Bounded between 0 and 100
        - Explanatory factors and recommended actions generated
        """
        now = datetime.utcnow()
        service_calls = [
            {"date": now - timedelta(days=5), "severity": "CRITICAL"},
            {"date": now - timedelta(days=12), "severity": "HIGH"}
        ]
        anomalies = [
            {"severity": "CRITICAL", "resolved": "FALSE"}
        ]
        active_alerts = [
            {"severity": "CRITICAL", "status": "ACTIVE"}
        ]

        health, risk, level, factors, actions, pred_avail, reason = RiskEngine.calculate_asset_health_and_risk(
            asset_criticality="CRITICAL",
            service_calls=service_calls,
            sensor_anomalies=anomalies,
            active_alerts=active_alerts,
            pm_compliance_flag=False,
            mtbf_trend="DEGRADING"
        )

        self.assertGreaterEqual(risk, 60.0)
        self.assertLessEqual(health, 40.0)
        self.assertIn(level, ["HIGH", "CRITICAL"])
        self.assertTrue(len(factors) >= 3)
        self.assertTrue(len(actions) >= 1)
        self.assertTrue(pred_avail)

    def test_fault_normalization(self):
        """
        Test that inconsistent technician language is mapped to canonical codes
        while preserving original context.
        """
        normalizer = FaultNormalizationService()

        # Overheating variations
        code1, name1, sev1 = normalizer.normalize("High temp on compressor")
        self.assertEqual(code1, "OVERHEATING")
        self.assertEqual(sev1, "CRITICAL")

        code2, name2, sev2 = normalizer.normalize("Compressor boiling hot and tripped thermal fuse")
        self.assertEqual(code2, "OVERHEATING")

        # Vibration variations
        code3, name3, sev3 = normalizer.normalize("Motor shaft shaking violently with resonance")
        self.assertEqual(code3, "VIBRATION_ANOMALY")
        self.assertEqual(sev3, "HIGH")

        # Pressure drop
        code4, _, _ = normalizer.normalize("Sudden refrigerant suction pressure drop to 1.8 bar")
        self.assertEqual(code4, "PRESSURE_DROP")

    def test_mtbf_statistical_calculation(self):
        """
        Verify MTBF = sum of intervals / count of intervals.
        Verify insufficient data handling (< 2 failures).
        """
        # Case 1: Insufficient data (1 failure)
        res_single = MtbfService.calculate_mtbf_for_dates([datetime(2026, 1, 1)])
        self.assertFalse(res_single["has_sufficient_data"])
        self.assertIsNone(res_single["mtbf_hours"])
        self.assertIn("Requires at least 2 historical failure events", res_single["reason"])

        # Case 2: Sufficient data (3 failures)
        # Interval 1: 10 days = 240 hours
        # Interval 2: 20 days = 480 hours
        # Average: 360 hours
        dates = [
            datetime(2026, 1, 1, 0, 0),
            datetime(2026, 1, 11, 0, 0),
            datetime(2026, 1, 31, 0, 0)
        ]
        res_multi = MtbfService.calculate_mtbf_for_dates(dates)
        self.assertTrue(res_multi["has_sufficient_data"])
        self.assertAlmostEqual(res_multi["mtbf_hours"], 360.0, places=1)
        self.assertEqual(len(res_multi["failure_intervals_hours"]), 2)

    def test_iot_threshold_engine(self):
        """
        Test IoT threshold evaluation for temperature:
        - Normal within safe range (18-24)
        - Warning above safe max (26)
        - Critical above critical max (36)
        """
        config = {
            "safe_min": 18.0,
            "safe_max": 24.0,
            "warning_min": 15.0,
            "warning_max": 28.0,
            "critical_min": 10.0,
            "critical_max": 35.0
        }

        # Safe
        eval_safe = IoTEngine.evaluate_reading("temperature", 21.5, config)
        self.assertEqual(eval_safe["status"], "NORMAL")
        self.assertFalse(eval_safe["is_anomaly"])

        # Warning
        eval_warn = IoTEngine.evaluate_reading("temperature", 29.0, config)
        self.assertEqual(eval_warn["status"], "WARNING")
        self.assertTrue(eval_warn["is_anomaly"])
        self.assertEqual(eval_warn["severity"], "WARNING")

        # Critical
        eval_crit = IoTEngine.evaluate_reading("temperature", 36.5, config)
        self.assertEqual(eval_crit["status"], "CRITICAL")
        self.assertTrue(eval_crit["is_anomaly"])
        self.assertEqual(eval_crit["severity"], "CRITICAL")

    def test_maintenance_cadence_evaluation(self):
        """
        Verify strict PM interval/cadence evaluation (Section 11 requirement):
        Required frequency: 90 days.
        Dates: Day 0, Day 30, Day 40, Day 170.
        Expected: cadence_compliance == False, violation == True.
        """
        base = date(2026, 1, 1)
        completed_dates = [
            base,
            base + timedelta(days=30),
            base + timedelta(days=40),
            base + timedelta(days=170)
        ]

        result = MaintenanceService.evaluate_pm_cadence(
            required_frequency_days=90,
            completed_dates=completed_dates
        )

        self.assertFalse(result["cadence_compliance"])
        self.assertTrue(result["violation"])
        self.assertIn("Required maintenance interval was not maintained", result["reason"])
        self.assertEqual(result["actual_intervals_days"], [30, 10, 130])
        self.assertEqual(result["max_gap_days"], 130)

        # Test compliant regular cadence: 88 days, 92 days
        compliant_dates = [
            base,
            base + timedelta(days=88),
            base + timedelta(days=180)
        ]
        result_ok = MaintenanceService.evaluate_pm_cadence(
            required_frequency_days=90,
            completed_dates=compliant_dates
        )
        self.assertTrue(result_ok["cadence_compliance"])
        self.assertFalse(result_ok["violation"])

    def test_contract_renewal_risk(self):
        """
        Verify contract renewal risk calculation:
        - Expiry in < 15 days -> CRITICAL
        - Expiry in < 30 days -> HIGH
        - Low PM compliance score (< 80) -> Elevates risk
        """
        today = date.today()

        # Imminent expiry
        res_imminent = ContractService.calculate_renewal_risk(
            end_date=today + timedelta(days=10),
            pm_compliance_score=95.0,
            open_faults_count=0,
            unresolved_alerts_count=0,
            service_calls_count=2
        )
        self.assertEqual(res_imminent["renewal_risk"], "CRITICAL")

        # Expiring in 25 days with degraded compliance
        res_near = ContractService.calculate_renewal_risk(
            end_date=today + timedelta(days=25),
            pm_compliance_score=72.0,
            open_faults_count=2,
            unresolved_alerts_count=1,
            service_calls_count=6
        )
        self.assertEqual(res_near["renewal_risk"], "HIGH")

    def test_action_center_prioritization(self):
        """
        Verify Action Center sorts items by severity (CRITICAL before HIGH).
        """
        alerts = [
            {"id": "1", "severity": "MEDIUM", "status": "ACTIVE", "title": "Filter dirty"},
            {"id": "2", "severity": "CRITICAL", "status": "ACTIVE", "title": "Overheating shutoff"}
        ]
        pms = [
            {"id": "3", "pm_type": "Annual", "scheduled_date": "2026-01-01", "asset_name": "Chiller"}
        ]
        contracts = []
        high_risk = []

        actions = ActionCenterService.prioritize_actions(
            active_alerts=alerts,
            overdue_pms=pms,
            expiring_contracts=contracts,
            high_risk_assets=high_risk
        )

        self.assertGreater(len(actions), 0)
        self.assertEqual(actions[0]["priority"], "CRITICAL")
        self.assertEqual(actions[0]["cta"], "DISPATCH_ENGINEER")

if __name__ == "__main__":
    unittest.main()
