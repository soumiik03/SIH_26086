import unittest

import pandas as pd

from backend.schemas.backtest import BacktestResponse
from backend.schemas.forecast import Statistical730DayOutlook
from src.backtest.historical_replay import (
    ADVISORY_RULE_VERSION,
    CALIBRATION_YEAR,
    CASE_THRESHOLDS,
    OPERATIONAL_LAGS,
    TARGETS,
    TRAIN_YEARS,
    ReplayConfig,
    _load_test_frame,
    _prediction_frame,
    run_historical_replay,
)
from src.forecast_engine import ForecastEngine


class TestHistoricalReplay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run_historical_replay()

    def test_replay_is_available_from_real_dataset(self):
        self.assertEqual(self.result["status"], "AVAILABLE")
        self.assertEqual(self.result["records_evaluated"], 4380)

    def test_training_period_remains_2020_to_2023(self):
        self.assertEqual(tuple(self.result["methodology"]["training_period"]), TRAIN_YEARS)

    def test_calibration_period_remains_2024(self):
        self.assertEqual(self.result["methodology"]["calibration_period"], CALIBRATION_YEAR)

    def test_replay_period_remains_2025(self):
        self.assertEqual(self.result["methodology"]["replay_period"], 2025)
        self.assertEqual(self.result["evaluation_period"], "2025-01-01/2025-12-31")

    def test_iod_availability_lag_is_recorded(self):
        self.assertEqual(self.result["methodology"]["operational_lags"]["iod_days"], 3)

    def test_atmospheric_availability_lag_is_recorded(self):
        self.assertEqual(self.result["methodology"]["operational_lags"]["atmospheric_days"], 1)

    def test_prediction_frame_excludes_future_targets(self):
        frame = _load_test_frame(ReplayConfig())
        prediction = _prediction_frame(frame, ForecastEngine())
        self.assertFalse(any(column.startswith("target_") for column in prediction.columns))
        self.assertNotIn("label_available_7_14d", prediction.columns)

    def test_prediction_frame_excludes_crop_metadata_from_model_inputs(self):
        frame = _load_test_frame(ReplayConfig())
        prediction = _prediction_frame(frame, ForecastEngine())
        self.assertNotIn("Target_Crops", prediction.columns)
        self.assertNotIn("Active_Crop_Cycle", prediction.columns)

    def test_target_definitions_are_existing_targets(self):
        self.assertEqual(TARGETS["false_onset"], "target_false_onset_flag")
        self.assertEqual(TARGETS["dry_spell_5d"], "target_dry_spell_5d_14d")
        self.assertEqual(TARGETS["severe_break_7d"], "target_dry_spell_7d_21d")

    def test_outcomes_are_not_used_as_forecast_probabilities(self):
        for record in self.result["cases"]:
            self.assertNotEqual(record["forecast"]["probabilities"].get("false_onset"), record["outcome"]["false_onset"])

    def test_probability_values_are_bounded(self):
        for head_metrics in self.result["summary"]["model_evaluation"].values():
            self.assertGreaterEqual(head_metrics["brier_score"], 0.0)
        for case in self.result["cases"]:
            for value in case["forecast"]["probabilities"].values():
                self.assertGreaterEqual(value, 0.0)
                self.assertLessEqual(value, 1.0)

    def test_advisory_actions_are_valid(self):
        self.assertTrue({case["advisory"]["action"] for case in self.result["cases"]}.issubset({"SOW", "WAIT", "PREPARE_IRRIGATION"}))

    def test_advisory_rule_ids_are_present(self):
        for case in self.result["cases"]:
            self.assertTrue(case["advisory"]["rule_id"].startswith("AGRI-"))

    def test_advisory_rule_version_is_recorded(self):
        self.assertEqual(self.result["methodology"]["advisory_rule_version"], ADVISORY_RULE_VERSION)

    def test_statistical_outlook_contract_is_preserved(self):
        for case in self.result["cases"]:
            outlook = case["forecast"]["statistical_7_30_day_outlook"]
            self.assertEqual(outlook["forecast_status"], "STATISTICAL_7_30_DAY_OUTLOOK")
            self.assertEqual(set(outlook) & {"7_14d", "15_21d", "22_30d"}, {"7_14d", "15_21d", "22_30d"})
            Statistical730DayOutlook.model_validate(outlook)

    def test_case_selection_uses_predeclared_thresholds(self):
        self.assertEqual(self.result["methodology"]["target_definitions"], TARGETS)
        for case in self.result["cases"]:
            self.assertIn("selection_method", case)
            self.assertIn("predeclared_threshold", case["selection_method"])

    def test_case_selection_is_not_hardcoded_to_one_date(self):
        dates = [case["reference_date"] for case in self.result["cases"]]
        self.assertEqual(dates, sorted(dates))

    def test_timeline_reveals_outcome_after_prediction(self):
        for case in self.result["cases"]:
            self.assertTrue(case["timeline"]["outcome_revealed_after_prediction"])
            self.assertEqual(case["timeline"]["t0"], ["observations_available", "forecast_generated", "advisory_generated"])

    def test_timeline_uses_real_future_rainfall_rows(self):
        for case in self.result["cases"]:
            for row in case["timeline"]["t_plus_1_to_21d"]:
                self.assertIsInstance(row["rainfall_mm"], float)

    def test_metrics_distinguish_all_model_heads(self):
        self.assertEqual(set(self.result["summary"]["model_evaluation"]), set(TARGETS))

    def test_false_onset_metrics_report_rare_event_count(self):
        metrics = self.result["summary"]["model_evaluation"]["false_onset"]
        self.assertEqual(metrics["eligible_cases"], 4380)
        self.assertEqual(metrics["actual_events"], 11)

    def test_decision_metrics_make_no_counterfactual_claim(self):
        self.assertNotIn("crop_losses_prevented", self.result["summary"]["decision_level"])

    def test_replay_is_deterministic(self):
        second = run_historical_replay()
        self.assertEqual(self.result, second)

    def test_api_schema_is_valid(self):
        BacktestResponse.model_validate(self.result)

    def test_case_thresholds_are_fixed_configuration(self):
        self.assertEqual(CASE_THRESHOLDS["high_false_onset_probability"], 0.40)
        self.assertEqual(CASE_THRESHOLDS["high_dry_spell_probability"], 0.50)


if __name__ == "__main__":
    unittest.main()
