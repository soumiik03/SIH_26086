import json
import unittest
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from src.horizon_7_30d import (
    HORIZON_WINDOWS,
    TARGET_COLUMNS,
    build_feature_schema,
    generate_horizon_targets,
    temporal_split,
    validate_iod_as_of,
)


def synthetic_rows(rainfall, streak=None, start="2025-06-01"):
    n = len(rainfall)
    return pd.DataFrame({
        "Date": pd.date_range(start, periods=n, freq="D"),
        "District": ["Test"] * n,
        "Rainfall_Observed_mm": rainfall,
        "Dry_Spell_Days_Streak": streak or [0] * n,
        "as_of_feature": np.arange(n, dtype=float),
        "future_rain_feature": np.arange(n, dtype=float),
    })


class TestHorizonTargets(unittest.TestCase):
    def test_window_correctness(self):
        rain = [10.0] * 40
        rain[7:12] = [0.0] * 5
        rain[15:22] = [0.0] * 7
        rain[22] = 70.0
        df = generate_horizon_targets(synthetic_rows(rain, [3] + [0] * 39))
        row = df.iloc[0]
        self.assertEqual(row["target_dry_spell_7_14d"], 1)
        self.assertEqual(row["target_severe_break_15_21d"], 1)
        self.assertEqual(row["target_heavy_rain_22_30d"], 1)

    def test_future_feature_columns_are_not_in_schema(self):
        df = generate_horizon_targets(synthetic_rows([0.0] * 45))
        features = build_feature_schema(df)
        self.assertNotIn("future_rain_feature", features)  # test fixture marks it as disallowed below
        self.assertTrue(all(not c.startswith("target_") for c in features))

    def test_target_columns_are_isolated_and_labels_are_bounded(self):
        df = generate_horizon_targets(synthetic_rows([0.0] * 45))
        self.assertTrue(set(TARGET_COLUMNS).issubset(df.columns))
        for column in TARGET_COLUMNS:
            values = df[column].dropna().unique().tolist()
            self.assertTrue(set(values).issubset({0, 1}))

    def test_incomplete_tail_is_unavailable_not_negative(self):
        df = generate_horizon_targets(synthetic_rows([0.0] * 20))
        self.assertFalse(bool(df.iloc[0]["label_available_22_30d"]))
        self.assertTrue(pd.isna(df.iloc[0]["target_dry_spell_22_30d"]))

    def test_final_reference_rows_are_unavailable(self):
        df = generate_horizon_targets(synthetic_rows([0.0] * 45))
        for row_pos in (42, 43, 44):
            row = df.iloc[row_pos]
            self.assertFalse(bool(row["label_available_7_14d"]))
            self.assertFalse(bool(row["label_available_15_21d"]))
            self.assertFalse(bool(row["label_available_22_30d"]))
            self.assertTrue(pd.isna(row["target_dry_spell_7_14d"]))
            self.assertTrue(pd.isna(row["target_severe_break_22_30d"]))

    def test_out_of_season_targets_are_unavailable_but_future_labels_are_available(self):
        df = generate_horizon_targets(synthetic_rows([0.0] * 60, start="2025-12-01"))
        row = df.iloc[0]
        self.assertTrue(bool(row["label_available_7_14d"]))
        self.assertFalse(bool(row["target_applicable_dry_spell_7_14d"]))
        self.assertFalse(bool(row["target_applicable_severe_break_7_14d"]))
        self.assertTrue(pd.isna(row["target_dry_spell_7_14d"]))
        self.assertTrue(pd.isna(row["target_severe_break_7_14d"]))
        self.assertTrue(bool(row["target_applicable_heavy_rain_7_14d"]))
        self.assertEqual(row["target_heavy_rain_7_14d"], 0)

    def test_temporal_split(self):
        rows = []
        for year in (2020, 2023, 2024, 2025):
            rows.append({"Date": f"{year}-06-01", "District": "Test"})
        train, val, test = temporal_split(pd.DataFrame(rows))
        self.assertEqual(set(pd.to_datetime(train.Date).dt.year), {2020, 2023})
        self.assertEqual(set(pd.to_datetime(val.Date).dt.year), {2024})
        self.assertEqual(set(pd.to_datetime(test.Date).dt.year), {2025})

    def test_iod_as_of_three_day_lag(self):
        df = pd.DataFrame({
            "Date": ["2025-06-05", "2025-06-06"],
            "iod_period_end_date": ["2025-06-01", "2025-06-01"],
            "iod_available_date": ["2025-06-04", "2025-06-04"],
        })
        self.assertTrue(validate_iod_as_of(df))
        df.loc[1, "iod_available_date"] = "2025-06-07"
        self.assertFalse(validate_iod_as_of(df))

    def test_artifact_isolation_contract(self):
        self.assertEqual(HORIZON_WINDOWS["7_14d"], (7, 14))
        self.assertEqual(HORIZON_WINDOWS["15_21d"], (15, 21))
        self.assertEqual(HORIZON_WINDOWS["22_30d"], (22, 30))
        self.assertNotEqual(Path("models/horizon_7_30d").resolve(), Path("models").resolve())

    def test_trained_artifact_loading_and_probability_bounds(self):
        model_dir = Path("models/horizon_7_30d")
        metadata = json.loads((model_dir / "feature_metadata.json").read_text(encoding="utf-8"))
        ds_path = (
            Path("data/processed/horizon_7_30d_with_atmospheric.parquet")
            if Path("data/processed/horizon_7_30d_with_atmospheric.parquet").exists()
            else Path("data/processed/horizon_7_30d_dataset.parquet")
        )
        dataset = pd.read_parquet(ds_path)
        sample = dataset.loc[dataset["label_available_7_14d"]].iloc[:3]
        for target in TARGET_COLUMNS:
            artifact = joblib.load(model_dir / f"{target}_calibrated_xgb.joblib")
            self.assertEqual(artifact["target_col"], target)
            features = artifact.get("feature_cols", metadata["feature_names"])
            probabilities = artifact["model"].predict_proba(sample[features])[:, 1]
            self.assertTrue(np.all((probabilities >= 0) & (probabilities <= 1)))


if __name__ == "__main__":
    unittest.main()
