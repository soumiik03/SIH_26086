"""Leakage-controlled historical statistical replay.

The replay uses the production model artifacts and the existing 2025 test
rows. Labels are kept out of the prediction frame and are joined only after
probabilities and the agronomic advisory have been produced.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from src.agronomy.expert_system import AdvisoryInput, evaluate_advisory
from src.forecast_engine import ENGINE_VERSION, HORIZON_EVENT_APPLICABILITY_MONTHS, ForecastEngine


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATASET = ROOT / "data" / "processed" / "varshasentinel_master_with_atmospheric_signals.parquet"
REPLAY_YEAR = 2025
TRAIN_YEARS = (2020, 2021, 2022, 2023)
CALIBRATION_YEAR = 2024
MODEL_STATUS = "EXPERIMENTAL_OBSERVATION_STATE"
OUTLOOK_STATUS = "STATISTICAL_7_30_DAY_OUTLOOK"
ADVISORY_RULE_VERSION = "step7-deterministic-v1"
OPERATIONAL_LAGS = {"iod_days": 3, "atmospheric_days": 1}

TARGETS = {
    "onset": "target_onset_window_14d",
    "false_onset": "target_false_onset_flag",
    "dry_spell_5d": "target_dry_spell_5d_14d",
    "severe_break_7d": "target_dry_spell_7d_21d",
    "heavy_rain": "target_heavy_rain_7d",
    "revival": "target_revival_7d",
}
PROBABILITY_HEADS = tuple(TARGETS)
PREDICTION_FORBIDDEN_PREFIXES = ("target_", "label_available_")
CASE_THRESHOLDS = {
    "high_false_onset_probability": 0.40,
    "low_false_onset_probability": 0.10,
    "high_onset_probability": 0.60,
    "high_dry_spell_probability": 0.50,
}


@dataclass(frozen=True)
class ReplayConfig:
    dataset_path: Path = DEFAULT_DATASET
    replay_year: int = REPLAY_YEAR
    crop: str = "aman_rice"


def _as_json_value(value: Any) -> Any:
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, (pd.Timestamp, np.datetime64)):
        return pd.Timestamp(value).date().isoformat()
    return value


def _json_dict(row: Mapping[str, Any]) -> Dict[str, Any]:
    return {str(key): _as_json_value(value) for key, value in row.items()}


def _load_test_frame(config: ReplayConfig) -> pd.DataFrame:
    if not config.dataset_path.is_file():
        raise FileNotFoundError(f"Historical replay dataset not found: {config.dataset_path}")
    df = pd.read_parquet(config.dataset_path).copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values(["Date", "District"]).reset_index(drop=True)
    test = df[df["Date"].dt.year == config.replay_year].copy()
    if test.empty:
        raise ValueError(f"No replay rows found for test year {config.replay_year}")
    missing = [column for column in TARGETS.values() if column not in test.columns]
    if missing:
        raise ValueError(f"Replay target columns missing: {missing}")
    return test


def _prediction_frame(test: pd.DataFrame, engine: ForecastEngine) -> pd.DataFrame:
    """Build exactly the production feature columns, excluding all labels."""
    forbidden = [
        column for column in test.columns
        if column.startswith(PREDICTION_FORBIDDEN_PREFIXES)
        or column in {"Target_Crops", "Active_Crop_Cycle"}
    ]
    feature_columns = set()
    for metadata in (
        engine.baseline_feature_metadata,
        engine.iod_feature_metadata,
        engine.atmospheric_feature_metadata,
        engine.horizon_feature_metadata,
    ):
        feature_columns.update(metadata["feature_names"])
    missing = sorted(feature_columns.difference(test.columns) - {"District_Encoded", "Zone_Encoded"})
    if missing:
        raise ValueError(f"Replay feature state is incomplete: {missing}")

    frame = test.drop(columns=forbidden, errors="ignore").copy()
    districts = engine.baseline_feature_metadata["districts"]
    zones = engine.baseline_feature_metadata["zones"]
    frame["District_Encoded"] = frame["District"].map({name: index for index, name in enumerate(districts)})
    frame["Zone_Encoded"] = frame["zone_id"].map({name: index for index, name in enumerate(zones)})
    if frame[["District_Encoded", "Zone_Encoded"]].isna().any().any():
        raise ValueError("Replay contains a district or zone outside the production feature metadata")
    return frame


def _batch_forecasts(test: pd.DataFrame, engine: ForecastEngine, crop: str = "aman_rice") -> List[Dict[str, Any]]:
    frame = _prediction_frame(test, engine)
    outputs = {head: np.zeros(len(frame), dtype=float) for head in PROBABILITY_HEADS}
    for head, model in engine.models.items():
        metadata = engine.model_metadata[head]
        columns = _schema_columns(engine, metadata["schema_type"])
        probabilities = model.predict_proba(frame.loc[:, columns])[:, 1]
        outputs[head] = np.clip(probabilities.astype(float), 0.0, 1.0)

    horizon_outputs: List[Dict[str, Any]] = []
    horizon_frame = frame.loc[:, engine.horizon_feature_metadata["feature_names"]]
    applicability = {
        event: [date.month in months for date in test["Date"]]
        for event, months in HORIZON_EVENT_APPLICABILITY_MONTHS.items()
    }
    horizon_probabilities: Dict[str, List[float | None]] = {}
    for target_col, model in engine.horizon_models.items():
        metadata = engine.horizon_model_metadata[target_col]
        event = metadata["event"]
        columns = metadata.get("feature_cols", list(horizon_frame.columns))
        mask = np.asarray(applicability[event], dtype=bool)
        values: List[float | None] = [None] * len(test)
        if mask.any():
            predicted = np.clip(model.predict_proba(horizon_frame.loc[mask, columns])[:, 1].astype(float), 0.0, 1.0)
            for position, probability in zip(np.flatnonzero(mask), predicted):
                values[int(position)] = round(float(probability), 4)
        horizon_probabilities[target_col] = values

    for index, reference_date in enumerate(test["Date"]):
        horizons = {"7_14d": {}, "15_21d": {}, "22_30d": {}}
        horizon_versions = {"7_14d": {}, "15_21d": {}, "22_30d": {}}
        for target_col in engine.horizon_models:
            metadata = engine.horizon_model_metadata[target_col]
            event = metadata["event"]
            horizon = metadata["horizon"]
            is_applicable = applicability[event][index]
            horizons[horizon][f"{event}_probability"] = horizon_probabilities[target_col][index]
            horizons[horizon][f"{event}_applicability"] = "APPLICABLE" if is_applicable else "OUT_OF_SEASON"
            horizon_versions[horizon][event] = {
                "target_col": target_col,
                "model_version": metadata["model_version"],
                "artifact_path": metadata["model_path"],
                "calibration_method": metadata["artifact_calibration_method"],
                "features_evaluated": metadata["feature_count"],
            }
        for horizon in horizons:
            horizons[horizon]["forecast_status"] = OUTLOOK_STATUS
            horizons[horizon]["model_versions"] = horizon_versions[horizon]
        horizon_outputs.append({
            "forecast_status": OUTLOOK_STATUS,
            "disclaimer": "This is a statistical probabilistic outlook based on information available at the reference date. It is not an NWP or S2S forecast.",
            "7_14d": horizons["7_14d"],
            "15_21d": horizons["15_21d"],
            "22_30d": horizons["22_30d"],
        })

    records = []
    for index, row in test.reset_index(drop=True).iterrows():
        probabilities = {head: round(float(outputs[head][index]), 4) for head in PROBABILITY_HEADS}
        outlook = horizon_outputs[index]
        advisory_input = AdvisoryInput(
            reference_date=row["Date"],
            crop=crop,
            probabilities={f"{head}_probability": value for head, value in probabilities.items()},
            statistical_7_30_day_outlook=outlook,
            location={"district": row["District"]},
            observations={"rainfall_observed_mm": float(row["Rainfall_Observed_mm"])},
        )
        advisory = evaluate_advisory(advisory_input)
        outcome = {name: int(row[target]) for name, target in TARGETS.items()}
        records.append({
            "reference_date": row["Date"].date().isoformat(),
            "location": {
                "district": str(row["District"]),
                "zone": str(row["zone_id"]),
                "latitude": float(row["Latitude"]),
                "longitude": float(row["Longitude"]),
            },
            "forecast": {
                "status": MODEL_STATUS,
                "engine_version": ENGINE_VERSION,
                "probabilities": probabilities,
                "statistical_7_30_day_outlook": outlook,
            },
            "advisory": {
                "action": advisory["action"],
                "rule_id": advisory["rule_id"],
                "headline": advisory["headline"],
                "reason_keys": advisory["reason_keys"],
                "validity": advisory["validity"],
            },
            "outcome": outcome,
        })
    return records


def _prediction_feature_names(engine: ForecastEngine) -> set[str]:
    names: set[str] = set()
    for metadata in (engine.baseline_feature_metadata, engine.iod_feature_metadata, engine.atmospheric_feature_metadata, engine.horizon_feature_metadata):
        names.update(metadata["feature_names"])
    return names


def _schema_columns(engine: ForecastEngine, schema_type: str) -> List[str]:
    metadata = {
        "baseline": engine.baseline_feature_metadata,
        "iod": engine.iod_feature_metadata,
        "atmospheric": engine.atmospheric_feature_metadata,
    }[schema_type]
    return list(metadata["feature_names"])


def _calibration_bins(y_true: Sequence[int], probabilities: Sequence[float], bins: int = 10) -> List[Dict[str, float]]:
    values = np.asarray(probabilities, dtype=float)
    labels = np.asarray(y_true, dtype=int)
    edges = np.linspace(0.0, 1.0, bins + 1)
    result = []
    for index in range(bins):
        mask = (values >= edges[index]) & (values <= edges[index + 1] if index == bins - 1 else values < edges[index + 1])
        if mask.any():
            result.append({
                "lower": float(edges[index]),
                "upper": float(edges[index + 1]),
                "count": int(mask.sum()),
                "mean_predicted": float(values[mask].mean()),
                "observed_rate": float(labels[mask].mean()),
            })
    return result


def _metrics(records: Sequence[Mapping[str, Any]], head: str) -> Dict[str, Any]:
    probabilities = np.asarray([record["forecast"]["probabilities"][head] for record in records], dtype=float)
    labels = np.asarray([record["outcome"][head] for record in records], dtype=int)
    thresholded = (probabilities >= 0.5).astype(int)
    metrics: Dict[str, Any] = {
        "eligible_cases": int(len(labels)),
        "actual_events": int(labels.sum()),
        "brier_score": float(brier_score_loss(labels, probabilities)),
        "precision": float(precision_score(labels, thresholded, zero_division=0)),
        "recall": float(recall_score(labels, thresholded, zero_division=0)),
        "f1": float(f1_score(labels, thresholded, zero_division=0)),
        "calibration": _calibration_bins(labels, probabilities),
    }
    try:
        metrics["roc_auc"] = float(roc_auc_score(labels, probabilities))
    except ValueError:
        metrics["roc_auc"] = None
    try:
        metrics["pr_auc"] = float(average_precision_score(labels, probabilities))
    except ValueError:
        metrics["pr_auc"] = None
    return metrics


def _case_timeline(record: Mapping[str, Any], frame: pd.DataFrame) -> Dict[str, Any]:
    reference_date = pd.Timestamp(record["reference_date"])
    district = record["location"]["district"]
    future = frame[(frame["District"] == district) & (frame["Date"] > reference_date) & (frame["Date"] <= reference_date + pd.Timedelta(days=21))]
    rainfall = [{"date": row.Date.date().isoformat(), "rainfall_mm": float(row.Rainfall_Observed_mm)} for row in future.itertuples()]
    return {
        "t0": ["observations_available", "forecast_generated", "advisory_generated"],
        "t_plus_1_to_21d": rainfall,
        "outcome_revealed_after_prediction": True,
    }


def _select_cases(records: Sequence[Mapping[str, Any]], frame: pd.DataFrame) -> List[Dict[str, Any]]:
    ordered = sorted(records, key=lambda record: (record["reference_date"], record["location"]["district"]))

    def first_matching(predicate, score):
        candidates = [record for record in ordered if predicate(record)]
        if not candidates:
            return None
        return sorted(candidates, key=lambda record: (-score(record), record["reference_date"], record["location"]["district"]))[0]

    definitions = [
        ("A_HIGH_FALSE_ONSET_ACTUAL", lambda r: r["outcome"]["false_onset"] == 1 and r["forecast"]["probabilities"]["false_onset"] >= CASE_THRESHOLDS["high_false_onset_probability"], lambda r: r["forecast"]["probabilities"]["false_onset"]),
        ("B_LOW_FALSE_ONSET_NO_EVENT", lambda r: r["outcome"]["false_onset"] == 0 and r["forecast"]["probabilities"]["false_onset"] <= CASE_THRESHOLDS["low_false_onset_probability"], lambda r: 1.0 - r["forecast"]["probabilities"]["false_onset"]),
        ("C_HIGH_ONSET_ACTUAL", lambda r: r["outcome"]["onset"] == 1 and r["forecast"]["probabilities"]["onset"] >= CASE_THRESHOLDS["high_onset_probability"], lambda r: r["forecast"]["probabilities"]["onset"]),
        ("D_HIGH_DRY_SPELL_ACTUAL", lambda r: r["outcome"]["dry_spell_5d"] == 1 and r["forecast"]["probabilities"]["dry_spell_5d"] >= CASE_THRESHOLDS["high_dry_spell_probability"], lambda r: r["forecast"]["probabilities"]["dry_spell_5d"]),
    ]
    selected = []
    for case_id, predicate, score in definitions:
        record = first_matching(predicate, score)
        if record is None:
            continue
        result = dict(record)
        result["case_id"] = case_id
        result["timeline"] = _case_timeline(record, frame)
        result["information_available_at_prediction_time"] = "Production feature snapshot for the reference date; future targets and outcome labels were excluded."
        result["selection_method"] = "predeclared_threshold_then_probability_then_date_then_district"
        selected.append(result)
    return selected


def _decision_metrics(records: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    warnings = [record for record in records if record["advisory"]["rule_id"] == "AGRI-WAIT-FALSE-ONSET-001"]
    if not warnings:
        return {"false_onset_wait_records": 0, "warning_followed_by_false_onset_rate": None, "warning_followed_by_dry_spell_rate": None}
    return {
        "false_onset_wait_records": len(warnings),
        "warning_followed_by_false_onset_rate": sum(record["outcome"]["false_onset"] for record in warnings) / len(warnings),
        "warning_followed_by_dry_spell_rate": sum(record["outcome"]["dry_spell_5d"] for record in warnings) / len(warnings),
        "interpretation": "Historical warning followed by the stated target outcome; no crop-loss or counterfactual-prevention claim is made.",
    }


def _metadata(engine: ForecastEngine, config: ReplayConfig) -> Dict[str, Any]:
    return {
        "replay_type": "walk-forward historical statistical replay",
        "model_version": ENGINE_VERSION,
        "model_artifacts": {head: meta["model_path"] for head, meta in engine.model_metadata.items()},
        "horizon_model_artifacts": {target: meta["model_path"] for target, meta in engine.horizon_model_metadata.items()},
        "feature_version": "production feature_metadata.json schemas",
        "training_period": list(TRAIN_YEARS),
        "calibration_period": CALIBRATION_YEAR,
        "replay_period": config.replay_year,
        "source_dataset": str(config.dataset_path),
        "target_definitions": TARGETS,
        "operational_lags": OPERATIONAL_LAGS,
        "advisory_rule_version": ADVISORY_RULE_VERSION,
        "random_seed": None,
        "prediction_excludes": ["future rainfall", "future indices", "future targets", "future labels"],
        "prediction_feature_columns": sorted(_prediction_feature_names(engine)),
    }


@lru_cache(maxsize=2)
def _cached_replay(dataset_path: str, replay_year: int, crop: str) -> Dict[str, Any]:
    config = ReplayConfig(dataset_path=Path(dataset_path), replay_year=replay_year, crop=crop)
    frame = _load_test_frame(config)
    engine = ForecastEngine()
    records = _batch_forecasts(frame, engine, crop=config.crop)
    for record in records:
        record["advisory"]["crop"] = crop
    return {
        "status": "AVAILABLE",
        "evaluation_period": f"{replay_year}-01-01/{replay_year}-12-31",
        "records_evaluated": len(records),
        "cases": _select_cases(records, frame),
        "summary": {
            "model_evaluation": {head: _metrics(records, head) for head in PROBABILITY_HEADS},
            "decision_level": _decision_metrics(records),
            "demonstration_case_count": len(_select_cases(records, frame)),
        },
        "methodology": _metadata(engine, config),
    }


def run_historical_replay(config: ReplayConfig | None = None) -> Dict[str, Any]:
    config = config or ReplayConfig()
    return _cached_replay(str(config.dataset_path), config.replay_year, config.crop)
