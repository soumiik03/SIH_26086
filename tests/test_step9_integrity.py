"""Regression checks for Step 9 forecast/data-integrity invariants."""

import json
from pathlib import Path

from backend.services import forecast_service
from src.agronomy.expert_system import evaluate_advisory
from src.spatial_forecast import evaluate_risk_level


ROOT = Path(__file__).resolve().parents[1]


def _advisory_context(probabilities):
    return {
        "reference_date": "2025-06-15T00:00:00Z",
        "crop": "aman_rice",
        "probabilities": probabilities,
        "statistical_7_30_day_outlook": {
            "7_14d": {
                "dry_spell_probability": 0.10,
                "severe_break_probability": 0.10,
                "dry_spell_applicability": "APPLICABLE",
                "severe_break_applicability": "APPLICABLE",
            }
        },
    }


def test_missing_forecast_is_not_low():
    risk, heads, _ = evaluate_risk_level({})
    assert risk == "UNAVAILABLE"
    assert set(heads.values()) == {"UNAVAILABLE"}


def test_missing_advisory_is_not_sow():
    result = evaluate_advisory(_advisory_context({"onset_probability": None}))
    assert result["action"] == "WAIT"
    assert result["rule_id"] == "AGRI-WAIT-APPLICABILITY-002"


def test_api_probability_preserves_decimal_value():
    feature = {
        "properties": {
            "onset_prob": 0.1234, "false_onset_prob": 0.2345,
            "dry_spell_5d_prob": 0.3456, "severe_break_7d_prob": 0.4567,
            "heavy_rain_prob": 0.5678, "revival_prob": 0.6789,
        }
    }
    values = forecast_service._forecast_probabilities(feature["properties"])
    assert values["onset_probability"] == 0.1234
    assert values["heavy_rain_probability"] == 0.5678
    assert values["revival_probability"] == 0.6789


def test_risk_thresholds_are_deterministic_and_not_scaled_twice():
    assert evaluate_risk_level({"heavy_rain": 0.249, "severe_break_7d": 0.1, "dry_spell_5d": 0.1, "false_onset": 0.1})[1]["heavy_rain_risk"] == "LOW"
    assert evaluate_risk_level({"heavy_rain": 0.25, "severe_break_7d": 0.1, "dry_spell_5d": 0.1, "false_onset": 0.1})[1]["heavy_rain_risk"] == "MODERATE"
    assert evaluate_risk_level({"heavy_rain": 0.75, "severe_break_7d": 0.1, "dry_spell_5d": 0.1, "false_onset": 0.1})[1]["heavy_rain_risk"] == "VERY_HIGH"


def test_district_inheritance_is_consistent_without_synthetic_variation():
    artifact = json.loads((ROOT / "data/processed/spatial_forecasts/latest_block_forecast.geojson").read_text())
    by_district = {}
    for feature in artifact["features"]:
        properties = feature["properties"]
        district = properties["district_name"]
        state = tuple(properties.get(key) for key in ("onset_prob", "false_onset_prob", "dry_spell_5d_prob", "severe_break_7d_prob", "heavy_rain_prob", "revival_prob"))
        by_district.setdefault(district, set()).add(state)
        assert properties["downscaling_method"] == "NONE_DISTRICT_INHERITED"
    assert by_district
    assert all(len(states) == 1 for states in by_district.values())
    assert len({next(iter(states)) for states in by_district.values()}) > 1


def test_ids_map_to_their_declared_hierarchy():
    artifact = json.loads((ROOT / "data/processed/spatial_forecasts/latest_panchayat_forecast.geojson").read_text())
    for feature in artifact["features"]:
        p = feature["properties"]
        assert str(p["panchayat_id"]).startswith("gp_")
        assert str(p["block_id"]).startswith("blk_")
        assert p["district_id"]


def test_graph_source_preserves_null_and_renders_all_events():
    source = (ROOT / "frontend/components/TrendChart.tsx").read_text()
    assert "?? 0" not in source
    assert "Revival" in source
    assert "Low modeled probability" in source
    assert "Data unavailable" in source


def test_out_of_season_and_unavailable_are_not_zero_probability():
    source = (ROOT / "frontend/components/probability.tsx").read_text()
    assert "Out of season" in source
    assert "Data unavailable" in source
    assert "?? 0" not in source


def test_map_does_not_use_synthetic_variation_or_unknown_as_low():
    source = (ROOT / "frontend/components/RiskMap.tsx").read_text()
    assert '"UNAVAILABLE"' in source
    assert '"#94a3b8"' in source
    assert '"#22c55e"' in source
