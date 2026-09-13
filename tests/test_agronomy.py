import unittest

from backend.schemas.forecast import AgronomicAdvisoryResponse, ForecastResponse
from backend.services import forecast_service
from src.agronomy.expert_system import evaluate_advisory, get_crop_profile


def context(**overrides):
    value = {
        "reference_date": "2025-06-15T00:00:00Z",
        "crop": "aman_rice",
        "probabilities": {
            "onset_probability": 0.80,
            "false_onset_probability": 0.10,
            "dry_spell_5d_probability": 0.10,
            "severe_break_7d_probability": 0.10,
            "heavy_rain_probability": 0.10,
            "revival_probability": 0.20,
        },
        "statistical_7_30_day_outlook": {
            "7_14d": {
                "dry_spell_probability": 0.10,
                "severe_break_probability": 0.10,
                "dry_spell_applicability": "APPLICABLE",
                "severe_break_applicability": "APPLICABLE",
            }
        },
    }
    value.update(overrides)
    return value


class TestAgronomicExpertSystem(unittest.TestCase):
    def test_supported_crop_is_explicitly_source_backed(self):
        profile = get_crop_profile("aman_rice")
        self.assertEqual(profile.preferred_sowing_start, (6, 10))
        self.assertEqual(profile.preferred_sowing_end, (6, 25))
        self.assertIn("icar.gov.in", profile.source_url)

    def test_missing_crop_context_waits(self):
        result = evaluate_advisory(context(crop=None))
        self.assertEqual(result["action"], "WAIT")
        self.assertEqual(result["rule_id"], "AGRI-WAIT-CROP-CONTEXT-001")

    def test_unknown_crop_is_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_advisory(context(crop="unsupported_crop"))

    def test_outside_sourced_window_waits(self):
        result = evaluate_advisory(context(reference_date="2025-12-15T00:00:00Z"))
        self.assertEqual(result["rule_id"], "AGRI-WAIT-WINDOW-001")

    def test_missing_outlook_applicability_waits(self):
        result = evaluate_advisory(context(statistical_7_30_day_outlook={"7_14d": {}}))
        self.assertEqual(result["rule_id"], "AGRI-WAIT-APPLICABILITY-001")

    def test_missing_current_probability_waits(self):
        probabilities = context()["probabilities"]
        probabilities.pop("onset_probability")
        result = evaluate_advisory(context(probabilities=probabilities))
        self.assertEqual(result["rule_id"], "AGRI-WAIT-APPLICABILITY-002")

    def test_heavy_rain_takes_priority_and_preserves_inputs(self):
        probabilities = context()["probabilities"]
        probabilities.update({"heavy_rain_probability": 0.75, "dry_spell_5d_probability": 0.80})
        result = evaluate_advisory(context(probabilities=probabilities))
        self.assertEqual(result["rule_id"], "AGRI-DRAINAGE-001")
        self.assertEqual(result["risk_factors"]["heavy_rain_probability"], 0.75)

    def test_false_onset_waits(self):
        probabilities = context()["probabilities"]
        probabilities["false_onset_probability"] = 0.40
        result = evaluate_advisory(context(probabilities=probabilities))
        self.assertEqual(result["rule_id"], "AGRI-WAIT-FALSE-ONSET-001")

    def test_insufficient_onset_waits(self):
        probabilities = context()["probabilities"]
        probabilities["onset_probability"] = 0.59
        result = evaluate_advisory(context(probabilities=probabilities))
        self.assertEqual(result["rule_id"], "AGRI-WAIT-ONSET-001")

    def test_dry_or_break_risk_prepares_irrigation(self):
        probabilities = context()["probabilities"]
        probabilities["dry_spell_5d_probability"] = 0.50
        result = evaluate_advisory(context(probabilities=probabilities))
        self.assertEqual(result["action"], "PREPARE_IRRIGATION")
        self.assertEqual(result["rule_id"], "AGRI-IRRIGATION-001")

    def test_extreme_dry_or_break_risk_waits(self):
        probabilities = context()["probabilities"]
        probabilities["dry_spell_5d_probability"] = 0.70
        result = evaluate_advisory(context(probabilities=probabilities))
        self.assertEqual(result["rule_id"], "AGRI-WAIT-DRY-SPELL-001")

    def test_favorable_sowing_decision(self):
        result = evaluate_advisory(context())
        self.assertEqual(result["action"], "SOW")
        self.assertEqual(result["rule_id"], "AGRI-SOW-001")
        self.assertIn("sourced window", " ".join(result["reasons"]))

    def test_deterministic_for_same_context(self):
        self.assertEqual(evaluate_advisory(context()), evaluate_advisory(context()))

    def test_invalid_probability_is_rejected(self):
        probabilities = context()["probabilities"]
        probabilities["onset_probability"] = 1.01
        with self.assertRaises(ValueError):
            evaluate_advisory(context(probabilities=probabilities))

    def test_advisory_input_contract_requires_forecast_context(self):
        with self.assertRaises(ValueError):
            evaluate_advisory({"reference_date": "2025-06-15T00:00:00Z"})

    def test_stage_and_planned_date_are_context_only(self):
        result = evaluate_advisory(context(crop_stage="transplanting", planned_sowing_date="2025-06-15"))
        self.assertEqual(result["action"], "SOW")

    def test_existing_forecast_response_and_advisory_schema(self):
        feature = forecast_service.panchayat_features()[0]
        forecast = forecast_service.to_forecast_response(feature)
        ForecastResponse.model_validate(forecast)
        self.assertEqual(
            forecast["onset_probability"],
            float(feature["properties"]["onset_prob"]),
        )
        advisory = forecast_service.advisory_for_panchayat(
            str(feature["properties"]["panchayat_id"]), "aman_rice"
        )
        AgronomicAdvisoryResponse.model_validate(advisory)


if __name__ == "__main__":
    unittest.main()
