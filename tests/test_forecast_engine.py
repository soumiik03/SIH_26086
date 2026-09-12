"""
VARSHASENTINEL (SIH26086) - Unit Tests for Forecast Engine
===========================================================
Tests model loading, benchmark routing, feature schema validation,
strict missing-feature handling, probability bounds, and all six prediction heads.
"""

import os
import unittest
import pandas as pd
import numpy as np

from src.forecast_engine import ForecastEngine, predict_monsoon_events, ENGINE_VERSION


class TestForecastEngine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = ForecastEngine()
        cls.parquet_path = "data/processed/varshasentinel_master_with_iod.parquet"
        cls.df_sample = pd.read_parquet(cls.parquet_path).head(20)

        # Baseline minimal valid observation for testing
        cls.valid_obs = {
            "District": "Purba_Bardhaman",
            "Date": "2025-06-15",
            "Rainfall_Observed_mm": 12.4,
            "Tmax_C": 34.2,
            "Tmin_C": 25.8,
            "Relative_Humidity_pct": 78.5,
            "Solar_Radiation_MJm2": 21.0,
            "MJO_Phase": 5,
            "MJO_Amplitude": 1.2,
            "Nino34_Anomaly": -0.25,
            "Dry_Spell_Days_Streak": 0,
            "Rolling_Rainfall_7d_mm": 42.0,
            "Rolling_Rainfall_30d_mm": 150.0,
            "rolling_rain_3d_mm": 18.0,
            "rolling_rain_15d_mm": 88.0,
            "Drought_Stress_Index": 0.0,
            "Waterlogging_Risk_Index": 0.08,
            "iod_dmi": 0.42,
            "iod_dmi_lag7": 0.35,
            "iod_dmi_lag14": 0.20
        }

    def test_model_loading_and_benchmark_routing(self):
        """Verify all 6 benchmark models load correctly from their respective benchmark directories."""
        expected_heads = {
            "onset": ("iod_enhanced", "models/iod_enhanced"),
            "false_onset": ("iod_enhanced", "models/iod_enhanced"),
            "revival": ("iod_enhanced", "models/iod_enhanced"),
            "heavy_rain": ("iod_enhanced", "models/iod_enhanced"),
            "dry_spell_5d": ("baseline_v1", "models"),
            "severe_break_7d": ("baseline_v1", "models")
        }

        self.assertEqual(len(self.engine.models), 6, "Engine must load exactly 6 prediction models.")

        for head_key, (exp_version, exp_dir) in expected_heads.items():
            self.assertIn(head_key, self.engine.models, f"Missing model head: {head_key}")
            model = self.engine.models[head_key]
            self.assertTrue(
                hasattr(model, "predict_proba"),
                f"Model for {head_key} must implement predict_proba"
            )

            meta = self.engine.model_metadata[head_key]
            self.assertEqual(meta["model_version"], exp_version)
            normalized_path = meta["model_path"].replace("\\", "/")
            self.assertTrue(
                normalized_path.startswith(exp_dir),
                f"Expected {head_key} to be loaded from {exp_dir}, got {meta['model_path']}"
            )

    def test_feature_schema_validation_and_exact_ordering(self):
        """Verify exact schema column counts and feature ordering for baseline and IOD models."""
        df_base, df_iod = self.engine.prepare_feature_vectors(self.valid_obs)

        # Baseline schema: exactly 26 columns in exact metadata order
        expected_base_cols = self.engine.baseline_feature_metadata["feature_names"]
        self.assertEqual(len(expected_base_cols), 26)
        self.assertEqual(list(df_base.columns), expected_base_cols)

        # IOD schema: exactly 31 columns in exact metadata order
        expected_iod_cols = self.engine.iod_feature_metadata["feature_names"]
        self.assertEqual(len(expected_iod_cols), 31)
        self.assertEqual(list(df_iod.columns), expected_iod_cols)

        # Confirm all 5 IOD features are in the IOD vector
        for iod_col in ["iod_dmi", "iod_positive_flag", "iod_negative_flag", "iod_dmi_lag7", "iod_dmi_lag14"]:
            self.assertIn(iod_col, df_iod.columns)
            self.assertNotIn(iod_col, df_base.columns)

    def test_missing_feature_handling_strict_validation(self):
        """Verify that omitting mandatory features raises ValueError and does NOT invent fake defaults."""
        # Case 1: Missing Tmax_C
        obs_no_tmax = dict(self.valid_obs)
        del obs_no_tmax["Tmax_C"]
        with self.assertRaises(ValueError) as ctx:
            self.engine.predict(obs_no_tmax)
        self.assertIn("Tmax_C", str(ctx.exception))

        # Case 2: Missing Relative_Humidity_pct
        obs_no_rh = dict(self.valid_obs)
        del obs_no_rh["Relative_Humidity_pct"]
        with self.assertRaises(ValueError) as ctx:
            self.engine.predict(obs_no_rh)
        self.assertIn("Relative_Humidity_pct", str(ctx.exception))

        # Case 3: Missing MJO_Phase
        obs_no_mjo = dict(self.valid_obs)
        del obs_no_mjo["MJO_Phase"]
        with self.assertRaises(ValueError) as ctx:
            self.engine.predict(obs_no_mjo)
        self.assertIn("MJO_Phase", str(ctx.exception))

        # Case 4: Missing IOD features for IOD-enhanced heads
        obs_no_iod = dict(self.valid_obs)
        del obs_no_iod["iod_dmi"]
        with self.assertRaises(ValueError) as ctx:
            self.engine.predict(obs_no_iod)
        self.assertIn("iod", str(ctx.exception).lower())

        # Case 5: Unknown District
        obs_bad_dist = dict(self.valid_obs)
        obs_bad_dist["District"] = "NonExistentDistrict"
        with self.assertRaises(ValueError) as ctx:
            self.engine.predict(obs_bad_dist)
        self.assertIn("NonExistentDistrict", str(ctx.exception))

    def test_probability_range_and_percentage_calibration(self):
        """Verify probabilities are strictly in [0, 1] and percentages match 100 * probability."""
        result = self.engine.predict(self.valid_obs)

        probs = result["summary_probabilities"]
        pcts = result["summary_percentages"]

        for head, p in probs.items():
            self.assertIsInstance(p, float)
            self.assertFalse(np.isnan(p), f"Probability for {head} is NaN")
            self.assertGreaterEqual(p, 0.0, f"Probability for {head} is < 0: {p}")
            self.assertLessEqual(p, 1.0, f"Probability for {head} is > 1: {p}")

            pct = pcts[head]
            self.assertIsInstance(pct, float)
            self.assertFalse(np.isnan(pct), f"Percentage for {head} is NaN")
            self.assertGreaterEqual(pct, 0.0, f"Percentage for {head} is < 0: {pct}")
            self.assertLessEqual(pct, 100.0, f"Percentage for {head} is > 100: {pct}")

            # Verify percentage matches probability within rounding margin
            self.assertAlmostEqual(pct, round(p * 100.0, 2), places=2)

    def test_all_six_prediction_heads_in_response(self):
        """Verify response contains all required metadata, disclaimers, and 6 prediction heads."""
        result = predict_monsoon_events(self.valid_obs)

        # Top-level contract
        self.assertEqual(result["engine_version"], ENGINE_VERSION)
        self.assertEqual(result["operational_status"], "EXPERIMENTAL_OBSERVATION_STATE")
        self.assertIn("observation/feature state", result["disclaimer"])
        self.assertIn("not yet an operational 7-30 day dynamical forecast", result["disclaimer"])

        expected_heads = [
            "onset",
            "false_onset",
            "revival",
            "heavy_rain",
            "dry_spell_5d",
            "severe_break_7d"
        ]

        self.assertEqual(sorted(result["summary_probabilities"].keys()), sorted(expected_heads))
        self.assertEqual(sorted(result["summary_percentages"].keys()), sorted(expected_heads))
        self.assertEqual(sorted(result["head_details"].keys()), sorted(expected_heads))

        for head in expected_heads:
            detail = result["head_details"][head]
            self.assertEqual(detail["head_key"], head)
            self.assertIn("description", detail)
            self.assertIn("target_col", detail)
            self.assertIn("model_version", detail)
            self.assertIn("model_path", detail)
            self.assertIn("probability", detail)
            self.assertIn("probability_pct", detail)
            self.assertIn("features_evaluated", detail)

    def test_batch_sample_prediction_on_real_dataset_records(self):
        """Verify end-to-end prediction across 10 sample rows from the enriched 2025 dataset."""
        for idx, row in self.df_sample.head(10).iterrows():
            result = predict_monsoon_events(row)
            self.assertEqual(len(result["summary_probabilities"]), 6)
            for head, p in result["summary_probabilities"].items():
                self.assertTrue(0.0 <= p <= 1.0, f"Row {idx} head {head} probability {p} out of bounds")


if __name__ == "__main__":
    unittest.main()
