"""
VARSHASENTINEL (SIH26086) - Unit Tests for Spatial Forecast Layer
=================================================================
Tests GeoJSON validity, geometry integrity, EPSG:4326 compliance,
hierarchy preservation, 6-head probability bounds, absence of synthetic
Panchayats, missing GP preservation, deterministic risk classification,
and deterministic agrometeorological advisory mapping.
"""

import os
import json
import ast
import unittest
import pandas as pd
import geopandas as gpd
from shapely.geometry import shape

from src.spatial_forecast import (
    SpatialForecastEngine,
    evaluate_risk_level,
    get_agricultural_advisory,
    OPERATIONAL_STATUS,
    OPERATIONAL_DISCLAIMER,
    STATISTICAL_OUTLOOK_STATUS,
    STATISTICAL_OUTLOOK_HORIZONS,
    STATISTICAL_OUTLOOK_EVENTS,
)
from src.spatial.spatial_validation import WB_BBOX


class TestSpatialForecastLayer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = SpatialForecastEngine()
        cls.output_dir = "data/processed/spatial_forecasts"
        # Run forecast generation to ensure latest files exist
        cls.summary = cls.engine.generate_and_save_all_forecasts(output_dir=cls.output_dir)

        cls.block_geojson = os.path.join(cls.output_dir, "latest_block_forecast.geojson")
        cls.panchayat_geojson = os.path.join(cls.output_dir, "latest_panchayat_forecast.geojson")
        cls.risk_map_geojson = os.path.join(cls.output_dir, "latest_risk_map.geojson")
        cls.missing_gp_csv = "reports/missing_gp_coverage.csv"

        cls.block_gdf = gpd.read_file(cls.block_geojson)
        cls.panchayat_gdf = gpd.read_file(cls.panchayat_geojson)

    def test_geojson_validity_and_crs(self):
        """Verify that all generated files are valid GeoJSON in EPSG:4326."""
        for path in [self.block_geojson, self.panchayat_geojson, self.risk_map_geojson]:
            self.assertTrue(os.path.exists(path), f"File missing: {path}")

            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(data.get("type"), "FeatureCollection", f"Not a FeatureCollection: {path}")
            self.assertGreater(len(data.get("features", [])), 0, f"Empty features in {path}")

            gdf = gpd.read_file(path)
            self.assertEqual(str(gdf.crs).upper(), "EPSG:4326", f"CRS mismatch in {path}: {gdf.crs}")

    def test_geometry_validity_and_bounds(self):
        """Verify all geometries are valid OGC polygons and strictly within West Bengal bbox."""
        for name, gdf in [("Block", self.block_gdf), ("Panchayat", self.panchayat_gdf)]:
            for idx, row in gdf.iterrows():
                geom = row.geometry
                self.assertIsNotNone(geom, f"{name} row {idx} has null geometry")
                self.assertFalse(geom.is_empty, f"{name} row {idx} has empty geometry")
                self.assertTrue(geom.is_valid, f"{name} row {idx} has invalid geometry: {geom}")
                self.assertIn(geom.geom_type, ["Polygon", "MultiPolygon"])

                minx, miny, maxx, maxy = geom.bounds
                self.assertGreaterEqual(minx, WB_BBOX["min_lon"] - 0.1, f"Min lon out of bounds: {minx}")
                self.assertLessEqual(maxx, WB_BBOX["max_lon"] + 0.1, f"Max lon out of bounds: {maxx}")
                self.assertGreaterEqual(miny, WB_BBOX["min_lat"] - 0.1, f"Min lat out of bounds: {miny}")
                self.assertLessEqual(maxy, WB_BBOX["max_lat"] + 0.1, f"Max lat out of bounds: {maxy}")

    def test_required_hierarchy_fields(self):
        """Verify official administrative hierarchy and LGD codes are strictly preserved."""
        required_block_fields = [
            "district_id", "district_name", "district_lgd_code",
            "block_id", "block_name", "block_lgd_code",
            "latitude", "longitude", "centroid_lat", "centroid_lon",
            "aggregation_level", "downscaling_method",
            "risk_level", "risk_color", "advisory_headline", "recommended_action",
            "model_version", "forecast_status", "disclaimer", "data_timestamp"
        ]
        for f in required_block_fields:
            self.assertIn(f, self.block_gdf.columns, f"Missing field {f} in block layer")
            self.assertEqual(self.block_gdf[f].isna().sum(), 0, f"Nulls found in block field {f}")

        required_gp_fields = required_block_fields + [
            "panchayat_id", "panchayat_name", "gp_lgd_code"
        ]
        for f in required_gp_fields:
            self.assertIn(f, self.panchayat_gdf.columns, f"Missing field {f} in panchayat layer")
            self.assertEqual(self.panchayat_gdf[f].isna().sum(), 0, f"Nulls found in panchayat field {f}")

        # Verify hierarchy values
        self.assertEqual(self.block_gdf["aggregation_level"].iloc[0], "BLOCK")
        self.assertEqual(self.panchayat_gdf["aggregation_level"].iloc[0], "PANCHAYAT")

    def test_all_six_probability_fields_and_bounds(self):
        """Verify all six event heads exist and probabilities are in [0.0, 1.0]."""
        prob_heads = [
            "onset_prob",
            "false_onset_prob",
            "dry_spell_5d_prob",
            "severe_break_7d_prob",
            "heavy_rain_prob",
            "revival_prob"
        ]

        downscaled_heads = [
            "onset_downscaled_prob",
            "false_onset_downscaled_prob",
            "dry_spell_5d_downscaled_prob",
            "severe_break_7d_downscaled_prob",
            "heavy_rain_downscaled_prob",
            "revival_downscaled_prob"
        ]

        pct_heads = [
            "onset_prob_pct",
            "false_onset_prob_pct",
            "dry_spell_5d_prob_pct",
            "severe_break_7d_prob_pct",
            "heavy_rain_prob_pct",
            "revival_prob_pct"
        ]

        for gdf in [self.block_gdf, self.panchayat_gdf]:
            for col in prob_heads + downscaled_heads:
                self.assertIn(col, gdf.columns, f"Missing prob column: {col}")
                valid_vals = gdf[col].dropna()
                if len(valid_vals) > 0:
                    self.assertTrue((valid_vals >= 0.0).all(), f"Negative probability in {col}")
                    self.assertTrue((valid_vals <= 1.0).all(), f"Probability > 1.0 in {col}")

            for col in pct_heads:
                self.assertIn(col, gdf.columns, f"Missing pct column: {col}")
                valid_vals = gdf[col].dropna()
                if len(valid_vals) > 0:
                    self.assertTrue((valid_vals >= 0.0).all(), f"Negative pct in {col}")
                    self.assertTrue((valid_vals <= 100.0).all(), f"Pct > 100.0 in {col}")

    def test_separation_of_probability_scales(self):
        """Verify district probabilities, downscaled probabilities, and downscaling metadata are distinct."""
        for gdf in [self.block_gdf, self.panchayat_gdf]:
            self.assertIn("downscaling_method", gdf.columns)
            self.assertIn("aggregation_level", gdf.columns)
            # Verify explicit method tag
            self.assertTrue((gdf["downscaling_method"] == "NONE_DISTRICT_INHERITED").all())

    def test_no_synthetic_panchayats_and_missing_gp_preservation(self):
        """Verify that NO fake/synthetic geometries are generated for the 85 excluded GPs."""
        self.assertTrue(os.path.exists(self.missing_gp_csv))
        missing_df = pd.read_csv(self.missing_gp_csv)
        self.assertEqual(len(missing_df), 85, "Must preserve exactly 85 excluded official GPs.")

        missing_lgd_codes = set(missing_df["gp_lgd_code"].astype(str))
        forecasted_lgd_codes = set(self.panchayat_gdf["gp_lgd_code"].astype(str))

        # Intersection must be empty: NONE of the 85 excluded GPs can be present as polygons
        overlap = missing_lgd_codes.intersection(forecasted_lgd_codes)
        self.assertEqual(
            len(overlap), 0,
            f"Cadastral corruption: {len(overlap)} excluded GPs were fabricated as polygons: {overlap}"
        )

        # Confirm no dummy zero codes
        self.assertNotIn("0", forecasted_lgd_codes)
        self.assertNotIn("", forecasted_lgd_codes)

        # Confirm exact count of safe GPs forecasted
        self.assertEqual(self.panchayat_gdf["gp_lgd_code"].nunique(), 1710)
        self.assertEqual(len(self.block_gdf), 187)

    def test_deterministic_risk_classification(self):
        """Verify deterministic risk mapping logic and color assignment."""
        # Case 1: VERY_HIGH heavy rain
        base = {"heavy_rain": 0.05, "severe_break_7d": 0.05, "dry_spell_5d": 0.05, "false_onset": 0.05, "onset": 0.05, "revival": 0.05}
        risk, head_risks, color = evaluate_risk_level({**base, "heavy_rain": 0.80})
        self.assertEqual(risk, "VERY_HIGH")
        self.assertEqual(head_risks["heavy_rain_risk"], "VERY_HIGH")
        self.assertEqual(color, "#ef4444")

        # Case 2: HIGH severe break
        risk, head_risks, color = evaluate_risk_level({**base, "severe_break_7d": 0.65})
        self.assertEqual(risk, "HIGH")
        self.assertEqual(head_risks["severe_break_risk"], "HIGH")
        self.assertEqual(color, "#f97316")

        # Case 3: MODERATE false onset
        risk, head_risks, color = evaluate_risk_level({**base, "false_onset": 0.30})
        self.assertEqual(risk, "MODERATE")
        self.assertEqual(head_risks["false_onset_risk"], "MODERATE")
        self.assertEqual(color, "#eab308")

        # Case 4: LOW all events
        risk, head_risks, color = evaluate_risk_level({
            "heavy_rain": 0.05, "severe_break_7d": 0.08, "dry_spell_5d": 0.06, "false_onset": 0.02, "onset": 0.03, "revival": 0.04
        })
        self.assertEqual(risk, "LOW")
        self.assertEqual(color, "#22c55e")

        # Check values present in actual GDF
        valid_risk_levels = {"LOW", "MODERATE", "HIGH", "VERY_HIGH", "UNAVAILABLE"}
        self.assertTrue(set(self.block_gdf["risk_level"].unique()).issubset(valid_risk_levels))
        self.assertTrue(set(self.panchayat_gdf["risk_level"].unique()).issubset(valid_risk_levels))

    def test_deterministic_advisory_output(self):
        """Verify deterministic AAS agrometeorological advisory logic."""
        # Heavy rain advisory
        base = {"heavy_rain": 0.05, "severe_break_7d": 0.05, "dry_spell_5d": 0.05, "false_onset": 0.05, "onset": 0.05, "revival": 0.05}
        hl, text = get_agricultural_advisory({**base, "heavy_rain": 0.65})
        self.assertIn("Heavy Rainfall", hl)
        self.assertIn("drainage channels", text)

        # Severe break advisory
        hl, text = get_agricultural_advisory({**base, "severe_break_7d": 0.72})
        self.assertIn("Dry Spell", hl)
        self.assertIn("supplementary irrigation", text)

        # False onset precaution
        hl, text = get_agricultural_advisory({**base, "false_onset": 0.45, "onset": 0.55})
        self.assertIn("False Onset", hl)
        self.assertIn("community nursery", text)

        # Normal seasonal operations
        hl, text = get_agricultural_advisory(base)
        self.assertIn("Normal Seasonal", hl)
        self.assertIn("standard agronomic", text)

        missing_hl, missing_text = get_agricultural_advisory({"heavy_rain": None})
        self.assertEqual(missing_hl, "Agronomic Advisory Unavailable")
        self.assertNotIn("Normal Seasonal", missing_hl)

        # Verify all actual records have non-empty advisories
        self.assertTrue((self.block_gdf["recommended_action"].str.len() > 20).all())
        self.assertTrue((self.panchayat_gdf["recommended_action"].str.len() > 20).all())

    def test_operational_status_and_disclaimer(self):
        """Verify experimental status and non-operational disclaimer are present in all records."""
        for gdf in [self.block_gdf, self.panchayat_gdf]:
            self.assertTrue((gdf["forecast_status"] == OPERATIONAL_STATUS).all())
            self.assertTrue((gdf["disclaimer"] == OPERATIONAL_DISCLAIMER).all())
            self.assertTrue((gdf["forecast_status"] == "EXPERIMENTAL_OBSERVATION_STATE").all())

    def test_statistical_7_30_day_outlook_contract(self):
        """Every block and safe Panchayat carries all horizon/event outlook fields."""
        for gdf in [self.block_gdf, self.panchayat_gdf]:
            for outlook in gdf["statistical_7_30_day_outlook"]:
                if isinstance(outlook, str):
                    outlook = ast.literal_eval(outlook)
                self.assertEqual(outlook["forecast_status"], STATISTICAL_OUTLOOK_STATUS)
                self.assertIn("not an NWP or S2S forecast", outlook["disclaimer"])
                for horizon in STATISTICAL_OUTLOOK_HORIZONS:
                    self.assertIn(horizon, outlook)
                    self.assertEqual(outlook[horizon]["forecast_status"], STATISTICAL_OUTLOOK_STATUS)
                    for event in STATISTICAL_OUTLOOK_EVENTS:
                        self.assertIn(event, outlook[horizon])
                        probability = outlook[horizon][event]
                        if probability is not None:
                            self.assertGreaterEqual(probability, 0.0)
                            self.assertLessEqual(probability, 1.0)
                        applicability = event.removesuffix("_probability") + "_applicability"
                        self.assertIn(applicability, outlook[horizon])
                        self.assertIn(outlook[horizon][applicability], {"APPLICABLE", "OUT_OF_SEASON", "UNAVAILABLE"})

    def test_forecast_metadata_records_outlook_and_coverage(self):
        metadata_path = os.path.join(self.output_dir, "forecast_run_metadata.json")
        with open(metadata_path, "r", encoding="utf-8") as handle:
            metadata = json.load(handle)
        outlook = metadata["statistical_7_30_day_outlook"]
        self.assertEqual(outlook["forecast_status"], STATISTICAL_OUTLOOK_STATUS)
        self.assertEqual(outlook["horizons"], list(STATISTICAL_OUTLOOK_HORIZONS))
        self.assertEqual(outlook["downscaling_method"], "NONE_DISTRICT_INHERITED")
        self.assertEqual(metadata["blocks_forecasted"], 187)
        self.assertEqual(metadata["safe_panchayats_forecasted"], 1710)
        self.assertEqual(metadata["official_gps_intentionally_excluded"], 85)


if __name__ == "__main__":
    unittest.main()
