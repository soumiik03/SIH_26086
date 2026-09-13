"""Step 10 regression checks for current-data and model-contract forensics."""

import json
from pathlib import Path

import joblib

from src.features.as_of_feature_builder import AsOfFeatureBuilder
from src.forecast_engine import ForecastEngine


ROOT = Path(__file__).resolve().parents[1]


def test_current_2026_as_of_date_uses_current_sources_without_2025_fallback():
    builder = AsOfFeatureBuilder()
    assert builder.get_common_data_as_of() == "2026-09-08"
    features = builder.build_features_as_of("2026-09-08", "Alipurduar")["Alipurduar"]
    assert features["Date"] == "2026-09-08"
    assert features["Rainfall_Observed_mm"] == 7.18


def test_current_atmospheric_gap_is_unavailable_not_imputed():
    builder = AsOfFeatureBuilder()
    engine = ForecastEngine()
    features = builder.build_features_as_of("2026-09-08", "Alipurduar")["Alipurduar"]
    _, _, atmospheric = engine.prepare_feature_vectors(features, return_atmospheric=True)
    assert atmospheric is None
    assert all(features.get(name) is None for name in engine.atmospheric_feature_metadata["feature_names"] if name.startswith(("u850", "v850", "wind850", "mslp", "regional_slp")))


def test_model_artifact_feature_order_matches_metadata():
    engine = ForecastEngine()
    for metadata in (engine.baseline_feature_metadata, engine.iod_feature_metadata, engine.atmospheric_feature_metadata, engine.horizon_feature_metadata):
        assert metadata["feature_names"]
    for head, model in engine.models.items():
        assert hasattr(model, "predict_proba"), head
    for target, model in engine.horizon_models.items():
        assert hasattr(model, "predict_proba"), target


def test_calibrated_horizon_artifacts_are_single_calibration_wrappers():
    for path in (ROOT / "models/horizon_7_30d").glob("*_calibrated_xgb.joblib"):
        artifact = joblib.load(path)
        assert artifact["calibration_method"] == "platt_sigmoid"
        assert type(artifact["model"]).__name__ == "CalibratedClassifierCV"


def test_current_seasonal_statuses_are_distinct_from_zero():
    builder = AsOfFeatureBuilder()
    engine = ForecastEngine()
    features = builder.build_features_as_of("2026-09-08", "Alipurduar")["Alipurduar"]
    result = engine.predict(features)
    assert result["event_applicability"]["onset"] == "OUT_OF_SEASON"
    assert result["summary_probabilities"]["onset"] is None
    assert result["event_applicability"]["heavy_rain"] == "UNAVAILABLE"
    assert result["summary_probabilities"]["heavy_rain"] is None


def test_horizon_unavailable_is_not_zero():
    builder = AsOfFeatureBuilder()
    engine = ForecastEngine()
    features = builder.build_features_as_of("2026-09-08", "Alipurduar")["Alipurduar"]
    horizons = engine.predict(features)["statistical_7_30_day_outlook"]["horizons"]
    for horizon in horizons.values():
        for event in ("dry_spell", "severe_break", "heavy_rain", "revival"):
            assert horizon[f"{event}_probability"] is None
            assert horizon[f"{event}_applicability"] == "UNAVAILABLE"


def test_production_probabilities_are_bounded():
    builder = AsOfFeatureBuilder()
    engine = ForecastEngine()
    features = builder.build_features_as_of("2026-09-08", "Alipurduar")["Alipurduar"]
    result = engine.predict(features)
    assert all(value is None or 0 <= value <= 1 for value in result["summary_probabilities"].values())
