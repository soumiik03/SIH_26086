"""
VARSHASENTINEL (SIH26086) - Unit Tests for IOD Feature Integration
===================================================================
Tests point-in-time leakage prevention, feature validity, dataset preservation,
and model artifact isolation.
"""

import os
import json
import unittest
import pandas as pd
import numpy as np


class TestIODIntegration(unittest.TestCase):

    def setUp(self):
        self.csv_path = "data/processed/varshasentinel_master_with_iod.csv"
        self.parquet_path = "data/processed/varshasentinel_master_with_iod.parquet"
        self.raw_bom_path = "data/raw/climate_indices/bom_iod_weekly_raw.txt"
        self.baseline_csv_path = "data/processed/varshasentinel_master_dataset.csv"
        self.iod_models_dir = "models/iod_enhanced"
        self.baseline_models_dir = "models"

    def test_enriched_dataset_existence_and_shape(self):
        """Verify enriched dataset exists with exactly 26,304 rows and required columns."""
        self.assertTrue(os.path.exists(self.csv_path), f"File {self.csv_path} does not exist.")
        self.assertTrue(os.path.exists(self.parquet_path), f"File {self.parquet_path} does not exist.")

        df = pd.read_parquet(self.parquet_path)
        self.assertEqual(len(df), 26304, f"Expected 26,304 rows, got {len(df)}")
        self.assertEqual(df["District"].nunique(), 12, f"Expected 12 districts, got {df['District'].nunique()}")

        required_iod_cols = [
            "iod_dmi", "iod_positive_flag", "iod_negative_flag",
            "iod_dmi_lag7", "iod_dmi_lag14"
        ]
        for col in required_iod_cols:
            self.assertIn(col, df.columns, f"Missing required IOD column: {col}")
            null_count = df[col].isna().sum()
            self.assertEqual(null_count, 0, f"Found {null_count} nulls in {col}!")

    def test_point_in_time_publication_lag_integrity(self):
        """Verify that every date in the dataset strictly obeys the 3-day publication lag rule."""
        df = pd.read_parquet(self.parquet_path)
        df["Date"] = pd.to_datetime(df["Date"])

        bom_df = pd.read_csv(self.raw_bom_path, header=None, names=["start_int", "end_int", "iod_dmi"])
        bom_df["period_end_date"] = pd.to_datetime(bom_df["end_int"].astype(str), format="%Y%m%d")
        bom_df["available_date"] = bom_df["period_end_date"] + pd.Timedelta(days=3)
        bom_df = bom_df.sort_values("available_date").reset_index(drop=True)

        # Merge raw BoM dates to verify
        merged = pd.merge_asof(
            df[["Date", "iod_dmi"]].drop_duplicates(subset=["Date"]).sort_values("Date"),
            bom_df[["available_date", "period_end_date", "iod_dmi"]],
            left_on="Date",
            right_on="available_date",
            direction="backward",
            suffixes=("", "_raw")
        )

        # Assert no lookahead: available_date <= Date and period_end_date + 3d <= Date
        leakage_count = (merged["available_date"] > merged["Date"]).sum()
        self.assertEqual(leakage_count, 0, f"Found {leakage_count} lookahead leakage violations!")

        # Assert exact value matching
        val_diff = (merged["iod_dmi"] - merged["iod_dmi_raw"]).abs().max()
        self.assertLess(val_diff, 1e-6, f"IOD values do not match raw BoM records: max diff {val_diff}")

    def test_baseline_dataset_and_models_preserved(self):
        """Verify that original master dataset and baseline models were NOT overwritten."""
        self.assertTrue(os.path.exists(self.baseline_csv_path))
        base_df = pd.read_csv(self.baseline_csv_path)
        self.assertEqual(len(base_df), 26304)
        self.assertNotIn("iod_dmi", base_df.columns, "Original master dataset was modified!")

        # Verify baseline models exist in models/
        self.assertTrue(os.path.exists(os.path.join(self.baseline_models_dir, "evaluation_metrics.json")))
        with open(os.path.join(self.baseline_models_dir, "evaluation_metrics.json"), "r") as f:
            base_metrics = json.load(f)
        self.assertEqual(len(base_metrics), 6)

    def test_iod_models_isolated_and_valid(self):
        """Verify that all 6 IOD-enhanced models exist in models/iod_enhanced/ with valid metrics."""
        self.assertTrue(os.path.exists(self.iod_models_dir))
        metrics_path = os.path.join(self.iod_models_dir, "evaluation_metrics.json")
        self.assertTrue(os.path.exists(metrics_path))

        with open(metrics_path, "r") as f:
            iod_metrics = json.load(f)
        self.assertEqual(len(iod_metrics), 6)

        for m in iod_metrics:
            self.assertIn("target", m)
            self.assertIn("test_brier", m)
            self.assertIn("test_roc_auc", m)
            self.assertIn("test_pr_auc", m)
            self.assertIn("test_f1", m)
            model_file = os.path.join(self.iod_models_dir, f"{m['target']}_xgb.joblib")
            self.assertTrue(os.path.exists(model_file), f"Missing model file: {model_file}")


if __name__ == "__main__":
    unittest.main()
