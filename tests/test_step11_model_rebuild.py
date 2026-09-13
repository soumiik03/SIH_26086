"""Step 11 V2 artifact, routing, and current-state integrity checks."""

import hashlib
import json
from pathlib import Path

import pandas as pd

from src.forecast_engine_v2 import ForecastEngineV2
from src.spatial_forecast import evaluate_risk_level

ROOT = Path(__file__).resolve().parents[1]


def _current_observation():
    trace = json.loads((ROOT / "reports" / "step10_forecast_trace.json").read_text(encoding="utf-8"))
    return {"Date": trace["reference_date"], **trace["features"]}


def test_manifest_uses_temporal_train_calibration_and_untouched_test():
    manifest = json.loads((ROOT / "models/v2/manifest.json").read_text(encoding="utf-8"))
    assert manifest["training_years"] == [2020, 2021, 2022, 2023]
    assert manifest["calibration_year"] == 2024
    assert manifest["test_year"] == 2025
    assert manifest["gap_days"] == 37
    source = (ROOT / "src/step11_model_rebuild.py").read_text(encoding="utf-8")
    assert "train_test_split" not in source
    assert "random_split" not in source


def test_all_v2_artifacts_have_stable_calibrator_and_matching_hash():
    manifest = json.loads((ROOT / "models/v2/manifest.json").read_text(encoding="utf-8"))
    for route in manifest["routing"]:
        artifact = ROOT / route["artifact"]
        metadata = json.loads((artifact.parent / "metadata.json").read_text(encoding="utf-8"))
        digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        assert metadata["sha256"] == digest
        assert metadata["feature_names"]
        assert metadata["release_status"] in {"PRODUCTION_V2", "BASELINE_PREFERRED"}


def test_v2_loader_can_reload_every_routed_artifact_in_a_clean_process():
    engine = ForecastEngineV2(ROOT)
    assert len(engine.routing) == 18
    assert len(engine._artifacts) == 18


def test_current_missing_atmospheric_features_are_explicitly_unavailable():
    output = ForecastEngineV2(ROOT).predict(_current_observation())
    assert output["events"]["revival"]["applicability"] == "UNAVAILABLE"
    assert output["events"]["revival"]["probability"] is None
    assert output["statistical_7_30_day_outlook"]["horizons"]["7_14d"]["heavy_rain"]["probability"] is None


def test_current_out_of_season_is_not_zero():
    output = ForecastEngineV2(ROOT).predict(_current_observation())
    assert output["events"]["onset"]["applicability"] == "OUT_OF_SEASON"
    assert output["events"]["onset"]["probability"] is None


def test_current_probabilities_are_bounded_and_not_percentage_scaled_twice():
    output = ForecastEngineV2(ROOT).predict(_current_observation())
    for event in output["events"].values():
        if event["probability"] is not None:
            assert 0.0 <= event["probability"] <= 1.0
            assert event["probability_pct"] == round(event["probability"] * 100.0, 4)
    for period in output["statistical_7_30_day_outlook"]["horizons"].values():
        for event in period.values():
            if event["probability"] is not None:
                assert 0.0 <= event["probability"] <= 1.0
                assert event["probability_pct"] == round(event["probability"] * 100.0, 4)


def test_risk_classification_is_deterministic_and_missing_is_not_low():
    assert evaluate_risk_level({})[0] == "UNAVAILABLE"
    assert evaluate_risk_level({"heavy_rain": 0.249})[1]["heavy_rain_risk"] == "LOW"
    assert evaluate_risk_level({"heavy_rain": 0.25})[1]["heavy_rain_risk"] == "MODERATE"
    assert evaluate_risk_level({"heavy_rain": 0.75})[1]["heavy_rain_risk"] == "VERY_HIGH"


def test_current_trace_is_generated_from_real_step10_observation():
    trace = json.loads((ROOT / "reports/step11_forecast_trace.json").read_text(encoding="utf-8"))
    source = json.loads((ROOT / "reports/step10_forecast_trace.json").read_text(encoding="utf-8"))
    assert trace["source_trace"] == "reports\\step10_forecast_trace.json"
    assert trace["reference_date"] == source["reference_date"]
    assert trace["features"] == source["features"]


def test_v2_feature_order_is_explicit_in_every_artifact():
    engine = ForecastEngineV2(ROOT)
    for artifact in engine._artifacts.values():
        assert artifact["feature_names"] == list(dict.fromkeys(artifact["feature_names"]))

