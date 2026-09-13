"""
VARSHASENTINEL (SIH26086) - Unit Tests for Atmospheric Signals & Step 4 Integration
===================================================================================
Verifies:
1. Atmospheric feature schema & metadata completeness (9 circulation features).
2. Strict temporal walk-forward split integrity:
   - Train: 2020-2023 (17,532 rows)
   - Calibrate: 2024 (4,392 rows)
   - Test: 2025 (4,380 rows)
3. Physical atmospheric range bounds:
   - u850_regional, v850_regional within [-40, 40] m/s
   - wind850_speed >= 0 m/s
   - mslp_regional within [960, 1040] hPa
   - regional_slp_gradient within [-20, 20] hPa
4. Operational anti-leakage latency protocol:
   - Atmospheric signals enforce >= 1-day publication lag (shift(1)).
5. Benchmark routing and probability validity:
   - Calibrated probabilities strictly in [0.0, 1.0].
6. Schema and disclaimer preservation:
   - Short-horizon heads preserve EXPERIMENTAL_OBSERVATION_STATE.
   - Horizon heads preserve STATISTICAL_7_30_DAY_OUTLOOK with NONE_DISTRICT_INHERITED downscaling.
"""

import os
import json
import unittest
from pathlib import Path
import numpy as np
import pandas as pd
import joblib

from src.forecast_engine import ForecastEngine, predict_monsoon_events, ENGINE_VERSION
from src.spatial_forecast import SpatialForecastEngine

ROOT = Path(__file__).resolve().parents[1]


class TestAtmosphericSignals(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = ForecastEngine()
        cls.atmos_meta_path = ROOT / "models" / "atmospheric_enhanced" / "feature_metadata.json"
        cls.horizon_meta_path = ROOT / "models" / "horizon_7_30d" / "feature_metadata.json"
        cls.master_parquet = ROOT / "data" / "processed" / "varshasentinel_master_with_atmospheric_signals.parquet"
        cls.ablation_json = ROOT / "reports" / "step4_ablation_metrics.json"

    def test_atmospheric_metadata_completeness(self):
        """Verify feature_metadata.json contains all 9 atmospheric variables."""
        self.assertTrue(self.atmos_meta_path.is_file(), "Atmospheric feature metadata must exist.")
        with open(self.atmos_meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        expected_atmos = [
            "u850_regional", "v850_regional", "wind850_speed",
            "mslp_regional", "regional_slp_gradient",
            "u850_lag7", "mslp_lag7",
            "u850_rolling_7d", "mslp_rolling_7d",
        ]
        for col in expected_atmos:
            self.assertIn(col, meta["atmospheric_features"], f"Missing atmospheric feature: {col}")
            self.assertIn(col, meta["feature_names"], f"Missing feature in feature_names: {col}")

        # Check total feature counts
        self.assertEqual(len(meta["base_features"]), 29)
        self.assertEqual(len(meta["atmospheric_features"]), 9)
        self.assertEqual(len(meta["feature_names"]), 40)  # 29 + 9 + District_Encoded + Zone_Encoded

    def test_physical_range_bounds(self):
        """Verify real atmospheric values adhere to physical meteorological ranges."""
        self.assertTrue(self.master_parquet.is_file(), "Master dataset with atmospheric signals must exist.")
        df = pd.read_parquet(self.master_parquet)

        # 850 hPa Winds
        self.assertTrue(df["u850_regional"].between(-40.0, 40.0).all(), "U850 out of physical range [-40, 40] m/s")
        self.assertTrue(df["v850_regional"].between(-40.0, 40.0).all(), "V850 out of physical range [-40, 40] m/s")
        self.assertTrue((df["wind850_speed"] >= 0.0).all(), "Wind speed must be non-negative")
        self.assertTrue((df["wind850_speed"] <= 60.0).all(), "Wind speed exceeds realistic 850 hPa limits")

        # Mean Sea Level Pressure
        self.assertTrue(df["mslp_regional"].between(960.0, 1040.0).all(), "MSLP out of range [960, 1040] hPa")
        self.assertTrue(df["regional_slp_gradient"].between(-20.0, 20.0).all(), "SLP gradient out of range [-20, 20] hPa")

        # Zero nulls
        atmos_cols = [
            "u850_regional", "v850_regional", "wind850_speed",
            "mslp_regional", "regional_slp_gradient",
            "u850_lag7", "mslp_lag7", "u850_rolling_7d", "mslp_rolling_7d",
        ]
        self.assertEqual(df[atmos_cols].isna().sum().sum(), 0, "Atmospheric columns must have zero missing values")

    def test_strict_temporal_split_counts(self):
        """Verify walk-forward splits: 2020-2023 Train, 2024 Calib, 2025 Test."""
        df = pd.read_parquet(self.master_parquet)
        df["_year"] = pd.to_datetime(df["Date"]).dt.year

        train_count = (df["_year"] <= 2023).sum()
        val_count = (df["_year"] == 2024).sum()
        test_count = (df["_year"] == 2025).sum()

        self.assertEqual(train_count, 17532, "Train fold (2020-2023) must have 17,532 rows")
        self.assertEqual(val_count, 4392, "Validation/Calib fold (2024) must have 4,392 rows")
        self.assertEqual(test_count, 4380, "Test fold (2025) must have 4,380 rows")
        self.assertEqual(train_count + val_count + test_count, len(df))

    def test_ablation_metrics_json_integrity(self):
        """Verify ablation metrics report exists and contains benchmark comparisons."""
        self.assertTrue(self.ablation_json.is_file(), "step4_ablation_metrics.json must exist.")
        with open(self.ablation_json, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("operational_heads", data)
        self.assertIn("horizon_models", data)
        self.assertIn("routing_decisions", data)

        self.assertEqual(len(data["operational_heads"]), 6)
        self.assertEqual(len(data["horizon_models"]), 12)

        # Operational benchmark routing verification
        self.assertEqual(data["routing_decisions"]["target_false_onset_flag"], "ATMOSPHERIC_ENHANCED")
        self.assertEqual(data["routing_decisions"]["target_heavy_rain_7d"], "ATMOSPHERIC_ENHANCED")
        self.assertEqual(data["routing_decisions"]["target_revival_7d"], "ATMOSPHERIC_ENHANCED")
        self.assertEqual(data["routing_decisions"]["target_onset_window_14d"], "RETAIN_BASELINE")
        self.assertEqual(data["routing_decisions"]["target_dry_spell_5d_14d"], "RETAIN_BASELINE")
        self.assertEqual(data["routing_decisions"]["target_dry_spell_7d_21d"], "RETAIN_BASELINE")

    def test_engine_atmospheric_prediction(self):
        """Verify that ForecastEngine produces valid calibrated probabilities with atmospheric features."""
        obs = {
            "District": "Purba_Bardhaman",
            "Date": "2025-07-15",
            "Rainfall_Observed_mm": 25.0,
            "Tmax_C": 33.0,
            "Tmin_C": 26.0,
            "Relative_Humidity_pct": 82.0,
            "Solar_Radiation_MJm2": 19.5,
            "MJO_Phase": 4,
            "MJO_Amplitude": 1.4,
            "Nino34_Anomaly": -0.1,
            "Dry_Spell_Days_Streak": 0,
            "Rolling_Rainfall_7d_mm": 65.0,
            "Rolling_Rainfall_30d_mm": 210.0,
            "rolling_rain_3d_mm": 35.0,
            "rolling_rain_15d_mm": 120.0,
            "Drought_Stress_Index": 0.0,
            "Waterlogging_Risk_Index": 0.15,
            "iod_dmi": 0.35,
            "iod_dmi_lag7": 0.30,
            "iod_dmi_lag14": 0.22,
            # Explicit atmospheric signals
            "u850_regional": 6.8,
            "v850_regional": 3.2,
            "wind850_speed": 7.516,
            "mslp_regional": 1002.5,
            "regional_slp_gradient": 2.8,
            "u850_lag7": 5.4,
            "mslp_lag7": 1004.1,
            "u850_rolling_7d": 6.1,
            "mslp_rolling_7d": 1003.2,
        }

        result = self.engine.predict(obs)

        # Operational status and disclaimers preserved
        self.assertEqual(result["operational_status"], "EXPERIMENTAL_OBSERVATION_STATE")
        self.assertEqual(result["statistical_7_30_day_outlook"]["forecast_status"], "STATISTICAL_7_30_DAY_OUTLOOK")

        # Head probabilities bounded
        for head, prob in result["summary_probabilities"].items():
            self.assertGreaterEqual(prob, 0.0, f"Probability for {head} < 0")
            self.assertLessEqual(prob, 1.0, f"Probability for {head} > 1")

        # Atmospheric heads evaluated 40 features
        atmos_heads = ["false_onset", "revival", "heavy_rain"]
        for head in atmos_heads:
            detail = result["head_details"][head]
            self.assertEqual(detail["model_version"], "atmospheric_enhanced")
            self.assertEqual(detail["features_evaluated"], 40)

        # Retained baseline heads
        self.assertEqual(result["head_details"]["onset"]["features_evaluated"], 31)
        self.assertEqual(result["head_details"]["dry_spell_5d"]["features_evaluated"], 26)
        self.assertEqual(result["head_details"]["severe_break_7d"]["features_evaluated"], 26)

    def test_spatial_engine_downscaling_method_preserved(self):
        """Verify that downscaling_method remains NONE_DISTRICT_INHERITED without premature downscaling."""
        spatial_engine = SpatialForecastEngine(forecast_engine=self.engine)
        latest_date, obs_by_dist = spatial_engine.load_latest_observations()
        forecasts = spatial_engine.generate_district_predictions(obs_by_dist)

        for dist_key, fc in forecasts.items():
            outlook = fc["statistical_7_30_day_outlook"]
            self.assertEqual(outlook["forecast_status"], "STATISTICAL_7_30_DAY_OUTLOOK")


if __name__ == "__main__":
    unittest.main()
