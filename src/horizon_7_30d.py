"""Leakage-safe statistical outlooks for 7--30 day event windows.

This module is intentionally separate from the production six-head pipeline.
It creates new targets and trains new artifacts only under the horizon_7_30d
namespace.  These are statistical outlooks from as-of observations/climate
state, not NWP or subseasonal dynamical forecasts.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
try:
    from sklearn.frozen import FrozenEstimator
except ImportError:  # scikit-learn < 1.6 compatibility
    FrozenEstimator = None
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from xgboost import XGBClassifier

logger = logging.getLogger("varshasentinel.horizon_7_30d")

HORIZON_WINDOWS: Mapping[str, Tuple[int, int]] = {
    "7_14d": (7, 14),
    "15_21d": (15, 21),
    "22_30d": (22, 30),
}
EVENT_SPECS: Mapping[str, Mapping[str, object]] = {
    "dry_spell": {"run_length": 5, "description": "At least five consecutive days below 2.5 mm"},
    "severe_break": {"run_length": 7, "description": "At least seven consecutive days below 2.5 mm"},
    "heavy_rain": {"run_length": 1, "description": "Daily rain at least 64.5 mm or a 3-day total at least 150 mm"},
    "revival": {"run_length": 1, "description": "Active dry spell followed by at least 5 mm and subsequent rain of at least 2.5 mm"},
}
TARGET_COLUMNS = [
    f"target_{event}_{window}"
    for event in EVENT_SPECS
    for window in HORIZON_WINDOWS
]
LABEL_AVAILABLE_COLUMNS = [f"label_available_{window}" for window in HORIZON_WINDOWS]
APPLICABILITY_COLUMNS = [
    f"target_applicable_{event}_{window}"
    for event in EVENT_SPECS
    for window in HORIZON_WINDOWS
]
# These months match the existing monsoon-event definitions in
# generate_monsoon_targets.py. Heavy rain remains an all-year extreme-rain
# target; dry spells, severe breaks, and revival are Kharif/monsoon events.
EVENT_APPLICABILITY_MONTHS: Mapping[str, frozenset[int]] = {
    "dry_spell": frozenset({6, 7, 8, 9, 10}),
    "severe_break": frozenset({6, 7, 8, 9, 10}),
    "heavy_rain": frozenset(range(1, 13)),
    "revival": frozenset({6, 7, 8, 9, 10}),
}
EXISTING_TARGET_COLUMNS = [
    "target_onset_window_14d", "target_false_onset_flag",
    "target_dry_spell_5d_14d", "target_dry_spell_7d_21d",
    "target_heavy_rain_7d", "target_revival_7d",
]
DEFAULT_FEATURE_EXCLUSIONS = {
    "Date", "Target_Crops", "Active_Crop_Cycle", "Zone", "District", "zone_id",
    *EXISTING_TARGET_COLUMNS, *TARGET_COLUMNS, *LABEL_AVAILABLE_COLUMNS,
    *APPLICABILITY_COLUMNS,
}


def _has_run(values: np.ndarray, start: int, end: int, run_length: int, threshold: float = 2.5) -> bool:
    """Return whether a low-rain run starts within [start, end], inclusive."""
    n = len(values)
    for offset in range(start, end + 1):
        if offset + run_length > n:
            continue
        if np.all(values[offset:offset + run_length] < threshold):
            return True
    return False


def _has_heavy_event(values: np.ndarray, start: int, end: int) -> bool:
    """Return whether a heavy event starts in [start, end], using only future rain."""
    n = len(values)
    for offset in range(start, end + 1):
        if offset >= n:
            continue
        if values[offset] >= 64.5:
            return True
        if offset + 3 <= n and values[offset:offset + 3].sum() >= 150.0:
            return True
    return False


def _has_revival_event(values: np.ndarray, current_streak: float, start: int, end: int) -> bool:
    """Return whether an active dry spell revives in the future window."""
    if current_streak < 3:
        return False
    n = len(values)
    for offset in range(start, end + 1):
        if offset + 1 < n and values[offset] >= 5.0 and values[offset + 1] >= 2.5:
            return True
    return False


def _window_has_complete_observations(row_pos: int, n: int, end: int, max_followup: int) -> bool:
    # The target may inspect beyond the window endpoint to complete a run or
    # accumulation, so only label rows with all required observations present.
    # Crucially, this is relative to the actual reference-row position.
    return row_pos + end + max_followup < n


def generate_horizon_targets(df: pd.DataFrame) -> pd.DataFrame:
    """Create isolated 7--30 day target columns without changing *df*.

    Reference date is each row's ``Date``.  A window ``a_b`` means event onset
    occurs on one of reference+``a`` through reference+``b`` calendar rows.
    Dry/severe runs must be fully observed after their onset; heavy 3-day
    events use the onset day plus the next two future days; revival uses the
    event day plus the following day.  Rows without complete observations are
    marked unavailable and targets are NaN, never negative.
    """
    required = {"Date", "District", "Rainfall_Observed_mm", "Dry_Spell_Days_Streak"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns for horizon targets: {sorted(missing)}")

    result = df.copy()
    result["Date"] = pd.to_datetime(result["Date"])
    for column in TARGET_COLUMNS:
        result[column] = pd.Series(pd.NA, index=result.index, dtype="Int8")
    for column in LABEL_AVAILABLE_COLUMNS:
        result[column] = False
    for column in APPLICABILITY_COLUMNS:
        result[column] = False

    result["_horizon_order"] = result.groupby("District").cumcount()
    for _, district_df in result.groupby("District", sort=False):
        indexes = district_df.sort_values("Date").index.to_list()
        rain = district_df.sort_values("Date")["Rainfall_Observed_mm"].to_numpy(dtype=float)
        streaks = district_df.sort_values("Date")["Dry_Spell_Days_Streak"].to_numpy(dtype=float)
        n = len(indexes)
        for row_pos, source_index in enumerate(indexes):
            for window_name, (start, end) in HORIZON_WINDOWS.items():
                # A seven-day run and a 3-day heavy accumulation are the
                # longest follow-up needed by any event definition.
                available = _window_has_complete_observations(row_pos, n, end, 7)
                result.loc[source_index, f"label_available_{window_name}"] = available
                month = pd.Timestamp(district_df.sort_values("Date").iloc[row_pos]["Date"]).month
                if not available:
                    continue
                for event in EVENT_SPECS:
                    applicable = month in EVENT_APPLICABILITY_MONTHS[event]
                    result.loc[source_index, f"target_applicable_{event}_{window_name}"] = applicable
                    if not applicable:
                        continue
                    if event == "dry_spell":
                        value = _has_run(rain, row_pos + start, row_pos + end, 5)
                    elif event == "severe_break":
                        value = _has_run(rain, row_pos + start, row_pos + end, 7)
                    elif event == "heavy_rain":
                        value = _has_heavy_event(rain, row_pos + start, row_pos + end)
                    else:
                        value = _has_revival_event(rain, streaks[row_pos], row_pos + start, row_pos + end)
                    result.loc[source_index, f"target_{event}_{window_name}"] = int(value)

    return result.drop(columns=["_horizon_order"])


def build_feature_schema(df: pd.DataFrame) -> List[str]:
    """Return numeric as-of feature columns, excluding identifiers and targets."""
    features = []
    for column in df.columns:
        if (
            column in DEFAULT_FEATURE_EXCLUSIONS
            or column.startswith("_")
            or "future" in column.lower()
            or "target" in column.lower()
        ):
            continue
        if pd.api.types.is_numeric_dtype(df[column]):
            features.append(column)
    if not features:
        raise ValueError("No numeric leakage-safe feature columns found")
    return features


def temporal_split(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split strictly by reference-date year: train 2020--23, val 2024, test 2025."""
    years = pd.to_datetime(df["Date"]).dt.year
    return df[years <= 2023].copy(), df[years == 2024].copy(), df[years == 2025].copy()


def validate_iod_as_of(df: pd.DataFrame, available_date_column: str = "iod_available_date") -> bool:
    """Validate optional BoM release-date metadata against the 3-day lag rule."""
    if available_date_column not in df.columns:
        # The distributed enriched dataset retains the result but not release
        # metadata; integration tests use this function with the metadata.
        return True
    if "iod_period_end_date" not in df.columns:
        raise ValueError("iod_available_date requires iod_period_end_date for an as-of audit")
    dates = pd.to_datetime(df["Date"])
    available = pd.to_datetime(df[available_date_column])
    period_end = pd.to_datetime(df["iod_period_end_date"])
    return bool((available >= period_end + pd.Timedelta(days=3)).all() and (available <= dates).all())


def _safe_metric(fn, y_true, probabilities, default=np.nan):
    try:
        return float(fn(y_true, probabilities))
    except ValueError:
        return default


def evaluate_probabilities(y_true: Sequence[int], probabilities: Sequence[float], threshold: float = 0.5) -> Dict[str, float]:
    y = np.asarray(y_true).astype(int)
    p = np.clip(np.asarray(probabilities, dtype=float), 0.0, 1.0)
    prediction = (p >= threshold).astype(int)
    return {
        "brier_score": float(brier_score_loss(y, p)),
        "roc_auc": _safe_metric(roc_auc_score, y, p),
        "pr_auc": _safe_metric(average_precision_score, y, p),
        "f1": float(f1_score(y, prediction, zero_division=0)),
        "precision": float(precision_score(y, prediction, zero_division=0)),
        "recall": float(recall_score(y, prediction, zero_division=0)),
        "positive_event_rate": float(y.mean()),
    }


def climatology_baseline(y_train: Sequence[int], y_test: Sequence[int]) -> Dict[str, float]:
    """Constant train prevalence baseline evaluated on the untouched test set."""
    prevalence = float(np.asarray(y_train).mean())
    metrics = evaluate_probabilities(y_test, np.full(len(y_test), prevalence))
    metrics["forecast_probability"] = prevalence
    return metrics


def reliability_bins(y_true: Sequence[int], probabilities: Sequence[float], bins: int = 10) -> List[Dict[str, float]]:
    y = np.asarray(y_true).astype(int)
    p = np.clip(np.asarray(probabilities, dtype=float), 0.0, 1.0)
    edges = np.linspace(0.0, 1.0, bins + 1)
    rows = []
    for i in range(bins):
        mask = (p >= edges[i]) & ((p < edges[i + 1]) if i < bins - 1 else (p <= edges[i + 1]))
        if mask.any():
            rows.append({
                "bin_lower": float(edges[i]), "bin_upper": float(edges[i + 1]),
                "count": int(mask.sum()), "mean_predicted": float(p[mask].mean()),
                "observed_rate": float(y[mask].mean()),
            })
    return rows


def train_horizon_models(
    df: pd.DataFrame,
    model_dir: Path = Path("models/horizon_7_30d"),
    metrics_path: Path = Path("reports/horizon_7_30d_metrics.json"),
) -> List[Dict[str, object]]:
    """Train 12 isolated models and save raw plus validation-calibrated artifacts."""
    model_dir.mkdir(parents=True, exist_ok=True)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    train, validation, test = temporal_split(df)
    feature_cols = build_feature_schema(df)
    metadata = {
        "feature_names": feature_cols,
        "target_columns": TARGET_COLUMNS,
        "horizon_windows_days": {k: list(v) for k, v in HORIZON_WINDOWS.items()},
        "train_years": [2020, 2021, 2022, 2023], "validation_year": 2024, "test_year": 2025,
        "forecast_type": "statistical_observation_climate_state_outlook",
        "iod_publication_lag_days": 3,
        "event_applicability_months": {
            event: sorted(months) for event, months in EVENT_APPLICABILITY_MONTHS.items()
        },
        "label_availability_rule": "reference_row_position + window_end + max_event_followup < series_length",
    }
    (model_dir / "feature_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    all_metrics = []

    for event in EVENT_SPECS:
        for window_name in HORIZON_WINDOWS:
            target = f"target_{event}_{window_name}"
            eligible = df[target].notna() & df[f"label_available_{window_name}"]
            train_e = train.loc[eligible.loc[train.index]]
            val_e = validation.loc[eligible.loc[validation.index]]
            test_e = test.loc[eligible.loc[test.index]]
            if train_e.empty or val_e.empty or test_e.empty:
                raise ValueError(f"No complete temporal data for {target}")
            y_train = train_e[target].astype(int)
            y_val = val_e[target].astype(int)
            y_test = test_e[target].astype(int)
            model = XGBClassifier(
                n_estimators=120, max_depth=5, learning_rate=0.08,
                subsample=0.85, colsample_bytree=0.85,
                scale_pos_weight=min(25.0, max(1.0, (len(y_train) - y_train.sum()) / max(1, y_train.sum()))),
                eval_metric="logloss", random_state=42, n_jobs=1,
            )
            model.fit(train_e[feature_cols], y_train, eval_set=[(val_e[feature_cols], y_val)], verbose=False)
            raw_path = model_dir / f"{target}_raw_xgb.joblib"
            joblib.dump({"model": model, "target_col": target, "feature_cols": feature_cols}, raw_path)

            if FrozenEstimator is not None:
                calibrated = CalibratedClassifierCV(FrozenEstimator(model), method="sigmoid")
            else:
                calibrated = CalibratedClassifierCV(estimator=model, method="sigmoid", cv="prefit")
            calibrated.fit(val_e[feature_cols], y_val)
            calibrated_path = model_dir / f"{target}_calibrated_xgb.joblib"
            joblib.dump({
                "model": calibrated, "base_model_path": str(raw_path), "calibration_method": "platt_sigmoid",
                "target_col": target, "feature_cols": feature_cols,
            }, calibrated_path)

            val_prob = calibrated.predict_proba(val_e[feature_cols])[:, 1]
            test_prob = calibrated.predict_proba(test_e[feature_cols])[:, 1]
            threshold_grid = np.linspace(0.05, 0.95, 91)
            threshold = max(threshold_grid, key=lambda t: f1_score(y_val, (val_prob >= t).astype(int), zero_division=0))
            result = {
                "target": target, "event": event, "horizon": window_name,
                "description": EVENT_SPECS[event]["description"], "n_train": len(y_train),
                "n_validation": len(y_val), "n_test": len(y_test),
                "unavailable": {
                    "train": int((~train[f"label_available_{window_name}"]).sum()),
                    "validation": int((~validation[f"label_available_{window_name}"]).sum()),
                    "test": int((~test[f"label_available_{window_name}"]).sum()),
                },
                "out_of_season": {
                    "train": int((train[target].isna() & train[f"label_available_{window_name}"]).sum()),
                    "validation": int((validation[target].isna() & validation[f"label_available_{window_name}"]).sum()),
                    "test": int((test[target].isna() & test[f"label_available_{window_name}"]).sum()),
                },
                "class_balance": {
                    "train_positive": int(y_train.sum()),
                    "train_negative": int((y_train == 0).sum()),
                    "validation_positive": int(y_val.sum()),
                    "validation_negative": int((y_val == 0).sum()),
                    "test_positive": int(y_test.sum()),
                    "test_negative": int((y_test == 0).sum()),
                },
                "test": evaluate_probabilities(y_test, test_prob, threshold),
                "climatology": climatology_baseline(y_train, y_test),
                "validation_brier": float(brier_score_loss(y_val, val_prob)),
                "decision_threshold_from_validation": float(threshold),
                "calibration": {"method": "platt_sigmoid", "reliability_test": reliability_bins(y_test, test_prob)},
                "artifacts": {"raw": str(raw_path), "calibrated": str(calibrated_path)},
            }
            all_metrics.append(result)

    metrics_path.write_text(json.dumps(all_metrics, indent=2, allow_nan=True), encoding="utf-8")
    return all_metrics


def build_horizon_dataset(input_path: Path, output_path: Path) -> pd.DataFrame:
    """Read the existing IOD-enriched dataset and write a new isolated dataset."""
    source = pd.read_parquet(input_path) if input_path.suffix == ".parquet" else pd.read_csv(input_path)
    result = generate_horizon_targets(source)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.suffix == ".parquet":
        result.to_parquet(output_path, index=False)
    else:
        result.to_csv(output_path, index=False)
    return result


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    root = Path(__file__).resolve().parents[1]
    dataset = build_horizon_dataset(
        root / "data/processed/varshasentinel_master_with_iod.parquet",
        root / "data/processed/horizon_7_30d_dataset.parquet",
    )
    metrics = train_horizon_models(
        dataset, root / "models/horizon_7_30d", root / "reports/horizon_7_30d_metrics.json"
    )
    logger.info("Trained %d calibrated horizon models", len(metrics))


if __name__ == "__main__":
    main()
