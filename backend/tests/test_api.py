import unittest

from fastapi.testclient import TestClient

from backend.main import app
from backend.services import forecast_service as service


class TestVarshaSentinelAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.sample = service.panchayat_features()[0]["properties"]
        cls.panchayat_id = cls.sample["panchayat_id"]
        cls.block_id = cls.sample["block_id"]

    def test_health(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["service_status"], "ok")
        self.assertEqual(body["forecast_status"], "EXPERIMENTAL_OBSERVATION_STATE")
        self.assertTrue(body["model_availability"])

    def test_district_listing(self):
        response = self.client.get("/api/districts")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json())

    def test_block_listing(self):
        response = self.client.get("/api/blocks")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(item["block_id"] == self.block_id for item in response.json()))

    def test_panchayat_lookup(self):
        response = self.client.get(f"/api/panchayats/{self.panchayat_id}")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["support_status"], "SUPPORTED_VERIFIED_SAFE_LAYER")
        self.assertIn("geometry", body)

    def test_invalid_panchayat_parameter(self):
        self.assertEqual(self.client.get("/api/panchayats/not-an-id").status_code, 422)

    def test_missing_or_unsupported_panchayat(self):
        self.assertEqual(self.client.get("/api/panchayats/gp_999999999").status_code, 404)

    def test_forecast_response_and_six_probabilities(self):
        response = self.client.get(f"/api/forecast/{self.panchayat_id}")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        fields = (
            "onset_probability", "false_onset_probability", "dry_spell_5d_probability",
            "severe_break_7d_probability", "heavy_rain_probability", "revival_probability",
        )
        for field in fields:
            self.assertIn(field, body)
            self.assertGreaterEqual(body[field], 0)
            self.assertLessEqual(body[field], 1)
        self.assertEqual(body["forecast_status"], "EXPERIMENTAL_OBSERVATION_STATE")

    def test_risk_map_geojson(self):
        response = self.client.get("/api/risk-map")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["type"], "FeatureCollection")
        self.assertTrue(body["features"])
        self.assertTrue(all(feature["type"] == "Feature" for feature in body["features"]))

    def test_backtest_is_documented_unimplemented(self):
        response = self.client.get("/api/backtest")
        self.assertEqual(response.status_code, 501)
        self.assertIn("not implemented", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()

