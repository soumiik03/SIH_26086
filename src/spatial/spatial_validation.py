"""
VARSHASENTINEL (SIH26086) - Spatial Data Validation Suite
=========================================================
Performs automated topological, schema, and hierarchical verification on
administrative boundary GeoJSONs. Detects:
  - Invalid geometries (self-intersections, unclosed rings, non-polygonal types)
  - Missing identifiers (district_id, block_id, panchayat_id)
  - Duplicate primary keys
  - Broken administrative hierarchies
  - CRS and bounding box inconsistencies
"""

import logging
from typing import Dict, Any, List, Tuple
import shapely.geometry
from shapely.validation import explain_validity

logger = logging.getLogger("varshasentinel.spatial_validation")

# Bounding box for West Bengal state
WB_BBOX = {
    "min_lon": 85.5,
    "max_lon": 90.0,
    "min_lat": 21.5,
    "max_lat": 27.5
}

REQUIRED_SCHEMA_KEYS = [
    "district_id",
    "district_name",
    "block_id",
    "block_name",
    "panchayat_id",
    "panchayat_name"
]


class SpatialValidator:
    """Automated validator for boundary vectors."""

    def __init__(self, bbox: Dict[str, float] = WB_BBOX):
        self.bbox = bbox

    def validate_crs_and_bbox(self, geojson_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validates coordinate bounds and coordinate reference system.
        GeoJSON RFC 7946 strictly mandates WGS 84 (EPSG:4326) in decimal degrees.
        """
        errors = []
        crs = geojson_data.get("crs", {}).get("properties", {}).get("name", "EPSG:4326")
        if "4326" not in crs and "CRS84" not in crs and "WGS" not in crs.upper():
            errors.append(f"CRS mismatch: Expected EPSG:4326 (WGS 84), got '{crs}'")

        features = geojson_data.get("features", [])
        if not features:
            errors.append("FeatureCollection contains 0 features.")
            return False, errors

        out_of_bounds = 0
        for idx, feat in enumerate(features):
            geom_dict = feat.get("geometry")
            if not geom_dict:
                continue
            try:
                geom = shapely.geometry.shape(geom_dict)
                minx, miny, maxx, maxy = geom.bounds
                if (minx < self.bbox["min_lon"] or maxx > self.bbox["max_lon"] or
                        miny < self.bbox["min_lat"] or maxy > self.bbox["max_lat"]):
                    out_of_bounds += 1
            except Exception as e:
                errors.append(f"Feature {idx}: Could not parse coordinates: {e}")

        if out_of_bounds > 0:
            errors.append(
                f"{out_of_bounds} / {len(features)} features fall outside West Bengal bounding box "
                f"({self.bbox['min_lon']}E-{self.bbox['max_lon']}E, {self.bbox['min_lat']}N-{self.bbox['max_lat']}N)"
            )

        return len(errors) == 0, errors

    def validate_geometries(self, features: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """Validates topological integrity using Shapely (OGC standards)."""
        errors = []
        for idx, feat in enumerate(features):
            props = feat.get("properties", {})
            name = props.get("panchayat_name") or props.get("block_name") or f"Feature_{idx}"
            geom_dict = feat.get("geometry")

            if not geom_dict:
                errors.append(f"Feature '{name}' (Index {idx}): Geometry object is null/empty.")
                continue

            geom_type = geom_dict.get("type")
            if geom_type not in ["Polygon", "MultiPolygon"]:
                errors.append(f"Feature '{name}' (Index {idx}): Invalid geometry type '{geom_type}'. Must be Polygon or MultiPolygon.")
                continue

            try:
                geom = shapely.geometry.shape(geom_dict)
                if geom.is_empty:
                    errors.append(f"Feature '{name}' (Index {idx}): Empty geometry.")
                elif not geom.is_valid:
                    reason = explain_validity(geom)
                    errors.append(f"Feature '{name}' (Index {idx}): Invalid geometry -> {reason}")
                elif geom.area <= 0:
                    errors.append(f"Feature '{name}' (Index {idx}): Zero polygon surface area.")
            except Exception as e:
                errors.append(f"Feature '{name}' (Index {idx}): Shapely parsing failed: {e}")

        return len(errors) == 0, errors

    def validate_identifiers(self, features: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """Validates primary keys, missing IDs, and detects duplicates."""
        errors = []
        seen_panchayat_ids = set()

        for idx, feat in enumerate(features):
            props = feat.get("properties", {})
            p_id = props.get("panchayat_id")

            # Check missing keys
            for key in REQUIRED_SCHEMA_KEYS:
                val = props.get(key)
                if val is None or str(val).strip() == "":
                    errors.append(f"Feature (Index {idx}): Missing mandatory property '{key}'.")

            # Check duplicate primary keys
            if p_id:
                if p_id in seen_panchayat_ids:
                    errors.append(f"Duplicate primary key: 'panchayat_id' '{p_id}' appears multiple times.")
                seen_panchayat_ids.add(p_id)

        return len(errors) == 0, errors

    def validate_administrative_hierarchy(self, features: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """
        Validates nested administrative hierarchy:
          District -> Block -> Panchayat
        Detects orphan units or conflicting parent linkages.
        """
        errors = []
        block_to_dist = {}

        for idx, feat in enumerate(features):
            props = feat.get("properties", {})
            d_id = props.get("district_id")
            b_id = props.get("block_id")

            if b_id and d_id:
                if b_id in block_to_dist and block_to_dist[b_id] != d_id:
                    errors.append(
                        f"Hierarchical conflict: Block '{b_id}' is mapped to district '{d_id}' "
                        f"but was previously mapped to district '{block_to_dist[b_id]}'."
                    )
                block_to_dist[b_id] = d_id

        return len(errors) == 0, errors

    def run_full_validation_suite(self, geojson_data: Dict[str, Any]) -> Dict[str, Any]:
        """Runs the entire spatial verification battery."""
        features = geojson_data.get("features", [])
        crs_ok, crs_errs = self.validate_crs_and_bbox(geojson_data)
        geom_ok, geom_errs = self.validate_geometries(features)
        id_ok, id_errs = self.validate_identifiers(features)
        hier_ok, hier_errs = self.validate_administrative_hierarchy(features)

        all_ok = crs_ok and geom_ok and id_ok and hier_ok
        all_errs = crs_errs + geom_errs + id_errs + hier_errs

        summary = {
            "status": "PASSED" if all_ok else "FAILED",
            "total_features": len(features),
            "checks": {
                "crs_and_bounding_box": {"passed": crs_ok, "errors": crs_errs},
                "geometry_validity": {"passed": geom_ok, "errors": geom_errs},
                "schema_and_identifiers": {"passed": id_ok, "errors": id_errs},
                "administrative_hierarchy": {"passed": hier_ok, "errors": hier_errs}
            },
            "error_count": len(all_errs),
            "error_messages": all_errs
        }

        return summary
