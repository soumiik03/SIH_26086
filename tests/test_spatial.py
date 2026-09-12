"""
VARSHASENTINEL (SIH26086) - Unit Tests for Spatial Validation
=============================================================
Tests topological verification, schema validation, hierarchy integrity,
and coordinate bounds checking.
"""

import unittest
from src.spatial.spatial_validation import SpatialValidator
from src.spatial.spatial_loader import SpatialDataLoader, DISTRICT_CENTROIDS


class TestSpatialValidation(unittest.TestCase):

    def setUp(self):
        self.validator = SpatialValidator()
        self.loader = SpatialDataLoader()

    def test_district_centroids_coverage(self):
        """Verify the 12 authentic district centroids exist and have valid coordinates."""
        centroids = self.loader.get_district_centroids()
        self.assertEqual(len(centroids), 12)
        for name, data in centroids.items():
            lat = data["latitude"]
            lon = data["longitude"]
            self.assertTrue(21.5 <= lat <= 27.5, f"Latitude {lat} out of range for {name}")
            self.assertTrue(85.5 <= lon <= 90.0, f"Longitude {lon} out of range for {name}")
            self.assertIn(data["zone_id"], ["gangetic_alluvial", "red_laterite", "terai_teesta"])

    def test_invalid_geometry_detection(self):
        """Verify self-intersecting 'bow-tie' polygon geometry is flagged as invalid."""
        # Self-intersecting polygon (0,0) -> (2,2) -> (2,0) -> (0,2) -> (0,0)
        invalid_geom = {
            "type": "Polygon",
            "coordinates": [[[87.0, 23.0], [88.0, 24.0], [88.0, 23.0], [87.0, 24.0], [87.0, 23.0]]]
        }
        features = [{
            "type": "Feature",
            "properties": {"panchayat_id": "gp_1", "panchayat_name": "Test GP"},
            "geometry": invalid_geom
        }]
        passed, errors = self.validator.validate_geometries(features)
        self.assertFalse(passed)
        self.assertTrue(any("Self-intersection" in e or "Invalid geometry" in e for e in errors))

    def test_missing_ids_detection(self):
        """Verify missing mandatory identifiers are caught."""
        features = [{
            "type": "Feature",
            "properties": {
                "district_id": "wb_purba_bardhaman",
                "district_name": "Purba Bardhaman",
                # missing block_id, block_name, panchayat_id, panchayat_name
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[87.1, 23.1], [87.2, 23.1], [87.2, 23.2], [87.1, 23.2], [87.1, 23.1]]]
            }
        }]
        passed, errors = self.validator.validate_identifiers(features)
        self.assertFalse(passed)
        self.assertTrue(any("Missing mandatory property 'block_id'" in e for e in errors))

    def test_duplicate_panchayat_ids(self):
        """Verify duplicate panchayat primary keys are flagged."""
        features = [
            {
                "type": "Feature",
                "properties": {
                    "district_id": "wb_purba_bardhaman",
                    "district_name": "Purba Bardhaman",
                    "block_id": "blk_1",
                    "block_name": "Burdwan I",
                    "panchayat_id": "gp_dupe_101",
                    "panchayat_name": "Belkash"
                },
                "geometry": None
            },
            {
                "type": "Feature",
                "properties": {
                    "district_id": "wb_purba_bardhaman",
                    "district_name": "Purba Bardhaman",
                    "block_id": "blk_1",
                    "block_name": "Burdwan I",
                    "panchayat_id": "gp_dupe_101", # DUPLICATE
                    "panchayat_name": "Rayna"
                },
                "geometry": None
            }
        ]
        passed, errors = self.validator.validate_identifiers(features)
        self.assertFalse(passed)
        self.assertTrue(any("appears multiple times" in e for e in errors))

    def test_broken_hierarchy_conflict(self):
        """Verify a block mapped to two conflicting parent districts is flagged."""
        features = [
            {
                "type": "Feature",
                "properties": {
                    "district_id": "wb_bankura",
                    "block_id": "blk_khatra",
                    "panchayat_id": "gp_1",
                },
                "geometry": None
            },
            {
                "type": "Feature",
                "properties": {
                    "district_id": "wb_purulia", # CONFLICTING PARENT DISTRICT FOR SAME BLOCK
                    "block_id": "blk_khatra",
                    "panchayat_id": "gp_2",
                },
                "geometry": None
            }
        ]
        passed, errors = self.validator.validate_administrative_hierarchy(features)
        self.assertFalse(passed)
        self.assertTrue(any("Hierarchical conflict" in e for e in errors))

    def test_crs_and_bbox_out_of_bounds(self):
        """Verify coordinate out of West Bengal bounding box is flagged."""
        geojson_data = {
            "type": "FeatureCollection",
            "crs": {"properties": {"name": "EPSG:4326"}},
            "features": [{
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    # Coordinates in Rajasthan (around 73E, 26N), far outside West Bengal
                    "coordinates": [[[73.0, 26.0], [74.0, 26.0], [74.0, 27.0], [73.0, 27.0], [73.0, 26.0]]]
                }
            }]
        }
        passed, errors = self.validator.validate_crs_and_bbox(geojson_data)
        self.assertFalse(passed)
        self.assertTrue(any("outside West Bengal bounding box" in e for e in errors))

    def test_downscaling_calculation(self):
        """Verify downscaling function responds correctly to topographic wetness and elevation."""
        district_probs = {
            "heavy_rain": 0.30,
            "dry_spell_5d": 0.40
        }
        # Lowland flood-prone valley block (lower elevation, high wetness index)
        lowland_covariates = {
            "elevation_mean_m": 12.0,
            "district_mean_elevation_m": 35.0,
            "delta_twi": 1.2
        }
        downscaled = self.loader.downscale_district_forecast("wb_purba_bardhaman", district_probs, lowland_covariates)
        # Heavy rain risk should increase in low-lying wet zones
        self.assertGreater(downscaled["heavy_rain_downscaled"], district_probs["heavy_rain"])
        # Dry spell risk should decrease in low-lying wet zones
        self.assertLess(downscaled["dry_spell_5d_downscaled"], district_probs["dry_spell_5d"])

    def test_derived_blocks_integrity(self):
        """Verify that every derived CD Block in west_bengal_blocks.geojson has non-null Subdis_LGD and valid geometry."""
        import os
        import geopandas as gpd
        geojson_path = "data/spatial/derived/west_bengal_blocks.geojson"
        self.assertTrue(os.path.exists(geojson_path), f"File {geojson_path} does not exist.")
        
        gdf = gpd.read_file(geojson_path)
        self.assertEqual(len(gdf), 353, f"Expected 353 CD Blocks, got {len(gdf)}")
        self.assertEqual(str(gdf.crs), "EPSG:4326", f"Expected EPSG:4326, got {gdf.crs}")
        
        # 1. Non-null Subdis_LGD
        null_lgd_count = gdf["Subdis_LGD"].isna().sum() + (gdf["Subdis_LGD"].astype(str).str.strip() == "").sum()
        self.assertEqual(null_lgd_count, 0, f"Found {null_lgd_count} blocks with null or empty Subdis_LGD.")
        
        # 2. Non-null Sub_dist (block name)
        null_name_count = gdf["Sub_dist"].isna().sum() + (gdf["Sub_dist"].astype(str).str.strip() == "").sum()
        self.assertEqual(null_name_count, 0, f"Found {null_name_count} blocks with null or empty Sub_dist.")
        
        # 3. Valid non-null geometry
        null_geom_count = gdf["geometry"].isna().sum() + gdf["geometry"].is_empty.sum()
        self.assertEqual(null_geom_count, 0, f"Found {null_geom_count} blocks with null or empty geometry.")
        
        invalid_geom_count = (~gdf.is_valid).sum()
        self.assertEqual(invalid_geom_count, 0, f"Found {invalid_geom_count} invalid geometries in derived blocks.")

    def test_safe_panchayats_layer_integrity(self):
        """Verify that the official safe Gram Panchayat layer meets all integrity constraints."""
        import os
        import geopandas as gpd
        
        geojson_path = "data/spatial/derived/west_bengal_panchayats_safe.geojson"
        gpkg_path = "data/spatial/derived/west_bengal_panchayats_safe.gpkg"
        
        self.assertTrue(os.path.exists(geojson_path), f"GeoJSON not found at {geojson_path}")
        self.assertTrue(os.path.exists(gpkg_path), f"GPKG not found at {gpkg_path}")
        
        gdf = gpd.read_file(geojson_path)
        
        # 1. Total feature count
        self.assertEqual(len(gdf), 3321, f"Expected 3,321 features, got {len(gdf)}")
        
        # 2. CRS
        self.assertEqual(str(gdf.crs), "EPSG:4326", f"Expected EPSG:4326, got {gdf.crs}")
        
        # 3. Geometry validity
        invalid_count = (~gdf.is_valid).sum()
        self.assertEqual(invalid_count, 0, f"Found {invalid_count} invalid geometries in safe panchayats.")
        
        # 4. Empty geometries
        empty_count = (gdf["geometry"].isna() | gdf["geometry"].is_empty).sum()
        self.assertEqual(empty_count, 0, f"Found {empty_count} empty geometries in safe panchayats.")
        
        # 5. Mandatory attributes
        required_cols = [
            "district_lgd_code", "district_name", "block_lgd_code",
            "block_name", "gp_lgd_code", "gp_name", "village_count"
        ]
        for col in required_cols:
            self.assertIn(col, gdf.columns, f"Missing required column: {col}")
            
        # 6. Genuine GP coverage
        real_gps = gdf[gdf["gp_lgd_code"] != "0"]
        unique_gps = real_gps["gp_lgd_code"].nunique()
        self.assertEqual(unique_gps, 3254, f"Expected 3,254 unique genuine GPs, got {unique_gps}")
        self.assertEqual(real_gps["district_lgd_code"].nunique(), 22, "Expected 22 districts covered")
        self.assertEqual(real_gps["block_lgd_code"].nunique(), 340, "Expected 340 blocks covered")

    def test_missing_gp_coverage_audit(self):
        """Verify that the 85 missing GPs are rigorously accounted for and classified."""
        import os
        import pandas as pd
        csv_path = "reports/missing_gp_coverage.csv"
        md_path = "reports/missing_gp_coverage_audit.md"
        self.assertTrue(os.path.exists(csv_path), f"Missing GP CSV not found at {csv_path}")
        self.assertTrue(os.path.exists(md_path), f"Missing GP Markdown report not found at {md_path}")
        
        df = pd.read_csv(csv_path)
        self.assertEqual(len(df), 85, f"Expected 85 missing GPs, got {len(df)}")
        
        valid_classes = {"FULLY_EXCLUDED_MULTI_GP", "ADMINISTRATIVE_MISMATCH", "NO_SURVEY_GEOMETRY", "OTHER"}
        found_classes = set(df["classification"].unique())
        self.assertTrue(found_classes.issubset(valid_classes), f"Unexpected classes: {found_classes - valid_classes}")
        
        # Verify 0 safe villages inside missing GPs
        self.assertEqual(df["has_any_safe_villages"].sum(), 0, "Found safe villages inside missing GPs!")


if __name__ == "__main__":
    unittest.main()

