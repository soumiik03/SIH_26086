import unittest
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from src.features.rainfall_provenance import (
    RAINFALL_SOURCE_CATALOG,
    is_available_as_of,
    usable_data_timestamp,
)


class TestStep6RainfallControls(unittest.TestCase):
    def test_source_provenance_catalog_contains_required_metadata(self):
        for source in RAINFALL_SOURCE_CATALOG.values():
            for field in ("provider", "product", "observation_type", "spatial_resolution", "temporal_resolution", "coverage", "units"):
                self.assertIn(field, source)

    def test_repository_rainfall_is_district_representative_not_local(self):
        files = sorted(Path("data/raw/weather").glob("*.csv"))
        self.assertEqual(len(files), 3)
        frame = pd.concat((pd.read_csv(path) for path in files), ignore_index=True)
        self.assertEqual(frame["District"].nunique(), 12)
        self.assertEqual(frame[["District", "Latitude", "Longitude"]].drop_duplicates().shape[0], 12)
        self.assertNotIn("panchayat_id", frame.columns)
        self.assertNotIn("block_id", frame.columns)
        self.assertTrue(frame["Rainfall_Observed_mm"].notna().all())

    def test_availability_rule_is_point_in_time_safe(self):
        observed = datetime(2025, 7, 1, 0, 0)
        available = usable_data_timestamp(observed, timedelta(hours=14))
        self.assertTrue(is_available_as_of(observed, available, datetime(2025, 7, 1, 14, 0)))
        self.assertFalse(is_available_as_of(observed, available, datetime(2025, 7, 1, 13, 59)))

    def test_availability_cannot_precede_observation(self):
        with self.assertRaises(ValueError):
            is_available_as_of(datetime(2025, 7, 1), datetime(2025, 6, 30, 23, 59), datetime(2025, 7, 2))

    def test_no_local_rainfall_artifact_is_claimed(self):
        self.assertFalse(RAINFALL_SOURCE_CATALOG["project_zone_centered_weather"]["local_panchayat_suitability"])

    def test_existing_production_routing_remains_inherited(self):
        metadata = Path("data/processed/spatial_forecasts/forecast_run_metadata.json").read_text(encoding="utf-8")
        self.assertIn("NONE_DISTRICT_INHERITED", metadata)


if __name__ == "__main__":
    unittest.main()
