import unittest
from fastapi.testclient import TestClient
from app.main import app

class TestAurumApiEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_root_endpoint(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "OPERATIONAL")
        self.assertIn("docs", data)

    def test_health_probe(self):
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")

    def test_fault_normalization_endpoint(self):
        response = self.client.post(
            "/api/v1/faults/normalize?raw_text=Compressor%20overheating%20thermal%20trip"
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertEqual(body["data"]["normalized_code"], "OVERHEATING")
        self.assertEqual(body["data"]["assigned_severity"], "CRITICAL")

    def test_ai_query_grounded_response(self):
        payload = {"question": "Which equipment is high risk?"}
        response = self.client.post("/api/v1/ai/query", json=payload)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertIn("answer", body["data"])
        self.assertIn("evidence", body["data"])
        self.assertIn("recommended_actions", body["data"])
        self.assertTrue(body["data"]["grounded_in_db"])

    def test_ai_query_specific_asset(self):
        payload = {"question": "Why is EQ-204 high risk?"}
        response = self.client.post("/api/v1/ai/query", json=payload)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertIn("answer", body["data"])

    def test_action_center_contract_filter(self):
        response = self.client.get("/api/v1/action-center?filter_type=CRITICAL")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["success"])
        self.assertIsInstance(body["data"], list)

if __name__ == "__main__":
    unittest.main()
