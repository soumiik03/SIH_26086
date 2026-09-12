"""Cached access to verified VARSHASENTINEL spatial forecast artifacts."""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List

from src.forecast_engine import ENGINE_VERSION
from src.spatial_forecast import OPERATIONAL_DISCLAIMER, OPERATIONAL_STATUS


ROOT = Path(__file__).resolve().parents[2]
SPATIAL_FORECASTS = ROOT / "data" / "processed" / "spatial_forecasts"


def _read_json(filename: str) -> Dict[str, Any]:
    with (SPATIAL_FORECASTS / filename).open("r", encoding="utf-8") as handle:
        return json.load(handle)


@lru_cache(maxsize=None)
def _artifact(filename: str) -> Dict[str, Any]:
    return _read_json(filename)


def _features(filename: str) -> List[Dict[str, Any]]:
    return _artifact(filename).get("features", [])


def panchayat_features() -> List[Dict[str, Any]]:
    return _features("latest_panchayat_forecast.geojson")


def risk_map() -> Dict[str, Any]:
    return _artifact("latest_risk_map.geojson")


def _prop(feature: Dict[str, Any], key: str, default: Any = None) -> Any:
    return feature.get("properties", {}).get(key, default)


def supported_districts() -> List[Dict[str, str]]:
    seen = {}
    for feature in panchayat_features():
        key = str(_prop(feature, "district_name", ""))
        if key:
            seen.setdefault(key, {
                "district_id": str(_prop(feature, "district_id", "")),
                "district_name": key,
                "meteorological_key": _meteorological_key(key),
            })
    return sorted(seen.values(), key=lambda item: item["district_name"])


def _meteorological_key(name: str) -> str:
    return {
        "Birbhum (Suri)": "Birbhum_Suri",
        "Purba Bardhaman": "Purba_Bardhaman",
        "Darjeeling (Siliguri Foothills)": "Siliguri_Foothill",
    }.get(name, name.replace(" ", "_"))


def supported_blocks() -> List[Dict[str, Any]]:
    result = {}
    for feature in _features("latest_block_forecast.geojson"):
        p = feature.get("properties", {})
        result.setdefault(str(p["block_id"]), {
            "block_id": str(p["block_id"]),
            "block_name": str(p["block_name"]),
            "district_id": str(p["district_id"]),
            "district_name": str(p["district_name"]),
            "block_lgd_code": str(p.get("block_lgd_code", "")) or None,
            "centroid_lat": float(p["centroid_lat"]),
            "centroid_lon": float(p["centroid_lon"]),
            "risk_level": str(p["risk_level"]),
        })
    return sorted(result.values(), key=lambda item: (item["district_name"], item["block_name"]))


def find_panchayat(panchayat_id: str) -> Dict[str, Any] | None:
    return next((feature for feature in panchayat_features()
                 if str(_prop(feature, "panchayat_id")) == panchayat_id), None)


def panchayats_for_block(block_id: str) -> List[Dict[str, Any]]:
    return [feature for feature in panchayat_features()
            if str(_prop(feature, "block_id")) == block_id]


def to_panchayat_response(feature: Dict[str, Any]) -> Dict[str, Any]:
    p = feature["properties"]
    geometry = feature.get("geometry")
    return {
        "panchayat_id": str(p["panchayat_id"]),
        "panchayat_name": str(p["panchayat_name"]),
        "block_id": str(p["block_id"]),
        "block_name": str(p["block_name"]),
        "district_id": str(p["district_id"]),
        "district_name": str(p["district_name"]),
        "district_lgd_code": str(p.get("district_lgd_code", "")) or None,
        "block_lgd_code": str(p.get("block_lgd_code", "")) or None,
        "gp_lgd_code": str(p.get("gp_lgd_code", "")) or None,
        "geometry": geometry,
        "geometry_metadata": {
            "geometry_type": geometry.get("type", "") if geometry else "",
            "centroid_lat": float(p["centroid_lat"]),
            "centroid_lon": float(p["centroid_lon"]),
        },
        "support_status": "SUPPORTED_VERIFIED_SAFE_LAYER",
    }


def to_panchayat_list_item(feature: Dict[str, Any]) -> Dict[str, Any]:
    p = feature["properties"]
    geometry = feature.get("geometry")
    return {
        "panchayat_id": str(p["panchayat_id"]),
        "panchayat_name": str(p["panchayat_name"]),
        "block_id": str(p["block_id"]),
        "block_name": str(p["block_name"]),
        "district_name": str(p["district_name"]),
        "gp_lgd_code": str(p.get("gp_lgd_code", "")) or None,
        "centroid_lat": float(p["centroid_lat"]),
        "centroid_lon": float(p["centroid_lon"]),
        "geometry": geometry,
    }


def to_forecast_response(feature: Dict[str, Any]) -> Dict[str, Any]:
    p = feature["properties"]
    probabilities = {
        "onset": float(p["onset_prob"]),
        "false_onset": float(p["false_onset_prob"]),
        "dry_spell_5d": float(p["dry_spell_5d_prob"]),
        "severe_break_7d": float(p["severe_break_7d_prob"]),
        "heavy_rain": float(p["heavy_rain_prob"]),
        "revival": float(p["revival_prob"]),
    }
    return {
        "panchayat_id": str(p["panchayat_id"]),
        "panchayat_name": str(p["panchayat_name"]),
        "block_id": str(p["block_id"]),
        "block_name": str(p["block_name"]),
        "district_id": str(p["district_id"]),
        "district_name": str(p["district_name"]),
        "onset_probability": probabilities["onset"],
        "false_onset_probability": probabilities["false_onset"],
        "dry_spell_5d_probability": probabilities["dry_spell_5d"],
        "severe_break_7d_probability": probabilities["severe_break_7d"],
        "heavy_rain_probability": probabilities["heavy_rain"],
        "revival_probability": probabilities["revival"],
        "risk_levels": {
            "overall": p["risk_level"],
            "heavy_rain": p["heavy_rain_risk"],
            "severe_break": p["severe_break_risk"],
            "dry_spell": p["dry_spell_risk"],
            "false_onset": p["false_onset_risk"],
        },
        "advisory": {
            "headline": p["advisory_headline"],
            "recommended_action": p["recommended_action"],
        },
        "model_versions": {
            "engine": str(p.get("model_version", ENGINE_VERSION)),
            "forecast_artifact": str(p.get("model_version", ENGINE_VERSION)),
        },
        "forecast_status": OPERATIONAL_STATUS,
        "timestamp": str(p["data_timestamp"]),
        "disclaimer": OPERATIONAL_DISCLAIMER,
    }


def health() -> Dict[str, Any]:
    available = {
        "onset": (ROOT / "models" / "iod_enhanced" / "target_onset_window_14d_xgb.joblib").is_file(),
        "false_onset": (ROOT / "models" / "iod_enhanced" / "target_false_onset_flag_xgb.joblib").is_file(),
        "revival": (ROOT / "models" / "iod_enhanced" / "target_revival_7d_xgb.joblib").is_file(),
        "heavy_rain": (ROOT / "models" / "iod_enhanced" / "target_heavy_rain_7d_xgb.joblib").is_file(),
        "dry_spell_5d": (ROOT / "models" / "target_dry_spell_5d_14d_xgb.joblib").is_file(),
        "severe_break_7d": (ROOT / "models" / "target_dry_spell_7d_21d_xgb.joblib").is_file(),
    }
    for name in ("latest_block_forecast.geojson", "latest_panchayat_forecast.geojson", "latest_risk_map.geojson"):
        available[f"artifact:{name}"] = (SPATIAL_FORECASTS / name).is_file()
    return {
        "service_status": "ok",
        "engine_version": ENGINE_VERSION,
        "forecast_status": OPERATIONAL_STATUS,
        "model_availability": available,
    }
