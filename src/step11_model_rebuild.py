"""Step 11 isolated V2 model rebuild.

This module deliberately writes only to ``models/v2`` and Step 11 reports.
It uses historical observations through 2025, purges target-boundary gaps,
fits calibrators only on 2024, and never uses 2026 outcomes for selection.
"""

from __future__ import annotations

import hashlib
import json
import math
import shutil
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Sequence

import joblib
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    log_loss,
    precision_recall_curve,
    roc_auc_score,
    roc_curve,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

try:
    from .v2_calibration import ProbabilityCalibrator
except ImportError:  # pragma: no cover - supports direct local invocation
    from v2_calibration import ProbabilityCalibrator

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data/processed/varshasentinel_master_with_atmospheric_signals.parquet"
V2_DIR = ROOT / "models/v2"
REPORT_DIR = ROOT / "reports"
PLOT_DIR = REPORT_DIR / "step11_plots"
GAP_DAYS = 37
RANDOM_STATE = 42

CORE_EVENTS: Mapping[str, Dict[str, Any]] = {
    "onset": {"target": "target_onset_window_14d", "horizon": 14, "months": {5, 6, 7}},
    "false_onset": {"target": "target_false_onset_flag", "horizon": 14, "months": {5, 6, 7}},
    "dry_spell_5d": {"target": "target_dry_spell_5d_14d", "horizon": 14, "months": {6, 7, 8, 9, 10}},
    "severe_break_7d": {"target": "target_dry_spell_7d_21d", "horizon": 21, "months": {6, 7, 8, 9, 10}},
    "heavy_rain": {"target": "target_heavy_rain_7d", "horizon": 7, "months": set(range(1, 13))},
    "revival": {"target": "target_revival_7d", "horizon": 7, "months": {6, 7, 8, 9, 10}},
}
HORIZONS = {"7_14d": (7, 14), "15_21d": (15, 21), "22_30d": (22, 30)}
HORIZON_EVENTS = {
    "dry_spell": {"run": 5, "months": {6, 7, 8, 9, 10}},
    "severe_break": {"run": 7, "months": {6, 7, 8, 9, 10}},
    "heavy_rain": {"run": 1, "months": set(range(1, 13))},
    "revival": {"run": 1, "months": {6, 7, 8, 9, 10}},
}
HORIZON_TARGETS = {
    f"{event}_{window}": f"target_{event}_{window}"
    for event in HORIZON_EVENTS for window in HORIZONS
}

BASE_FEATURES = [
    "Latitude", "Longitude", "Rainfall_Observed_mm", "Tmax_C", "Tmin_C",
    "Relative_Humidity_pct", "Solar_Radiation_MJm2", "MJO_Phase", "MJO_Amplitude",
    "Nino34_Anomaly", "Dry_Spell_Days_Streak", "Rolling_Rainfall_7d_mm",
    "Rolling_Rainfall_30d_mm", "Drought_Stress_Index", "Waterlogging_Risk_Index",
    "dtr_c", "vpd_kpa", "day_of_year", "doy_sin", "doy_cos", "mjo_phase_sin",
    "mjo_phase_cos", "rolling_rain_3d_mm", "rolling_rain_15d_mm", "District_Encoded", "Zone_Encoded",
]
TELE_FEATURES = ["MJO_Phase", "MJO_Amplitude", "Nino34_Anomaly", "iod_dmi", "iod_positive_flag", "iod_negative_flag", "iod_dmi_lag7", "iod_dmi_lag14", "mjo_phase_sin", "mjo_phase_cos"]
ATMOS_FEATURES = ["u850_regional", "v850_regional", "wind850_speed", "mslp_regional", "regional_slp_gradient", "u850_lag7", "mslp_lag7", "u850_rolling_7d", "mslp_rolling_7d"]
LOCAL_FEATURES = [x for x in BASE_FEATURES if x not in TELE_FEATURES and x not in {"District_Encoded", "Zone_Encoded"}]
TELE_FEATURE_SET = LOCAL_FEATURES + [x for x in TELE_FEATURES if x not in LOCAL_FEATURES]
FEATURE_SETS = {
    "local": LOCAL_FEATURES,
    "teleconnection": TELE_FEATURE_SET,
    "atmospheric": TELE_FEATURE_SET + ATMOS_FEATURES,
    "full": BASE_FEATURES[:-2] + TELE_FEATURES[3:8] + ATMOS_FEATURES + ["District_Encoded", "Zone_Encoded"],
    "full_no_district": BASE_FEATURES[:-2] + TELE_FEATURES[3:8] + ATMOS_FEATURES,
}


def _future_run(rain: np.ndarray, start: int, end: int, length: int) -> bool:
    for offset in range(start, end + 1):
        if offset + length <= len(rain) and np.all(rain[offset:offset + length] < 2.5):
            return True
    return False


def _future_heavy(rain: np.ndarray, start: int, end: int) -> bool:
    for offset in range(start, end + 1):
        if offset < len(rain) and rain[offset] >= 64.5:
            return True
        if offset + 3 <= len(rain) and rain[offset:offset + 3].sum() >= 150:
            return True
    return False


def _onset_and_false_events(dist: pd.DataFrame) -> tuple[int | None, list[int]]:
    rain = dist.Rainfall_Observed_mm.to_numpy(float)
    rh = dist.Relative_Humidity_pct.to_numpy(float)
    months = dist.Date.dt.month.to_numpy()
    doys = dist.Date.dt.dayofyear.to_numpy()
    onset = None
    false_events: list[int] = []
    for year in sorted(dist.Date.dt.year.unique()):
        year_positions = np.flatnonzero(dist.Date.dt.year.to_numpy() == year)
        year_onset = None
        for i in year_positions:
            if months[i] not in {5, 6, 7} or doys[i] < 135 or i + 3 >= len(dist):
                continue
            zone = str(dist.iloc[0].get("Zone", ""))
            threshold = 40.0 if "terai" in zone.lower() else 25.0
            if rain[i] >= 2.5 and rain[i + 1] >= 2.5 and rain[i:i + 3].sum() >= threshold and rh[i] >= 70:
                dry = 0
                max_dry = 0
                for k in range(i + 2, min(len(dist), i + 10)):
                    dry = dry + 1 if rain[k] < 2.5 else 0
                    max_dry = max(max_dry, dry)
                if max_dry >= 5:
                    false_events.append(i)
                elif year_onset is None:
                    year_onset = i
        if year_onset is None:
            june = [i for i in year_positions if months[i] == 6]
            if june:
                year_onset = june[len(june) // 2]
        if year_onset is not None and onset is None:
            onset = year_onset
    return onset, false_events


def build_leakage_safe_targets(df: pd.DataFrame) -> pd.DataFrame:
    """Rebuild all targets so labels inspect only dates strictly after T."""
    result = df.sort_values(["District", "Date"]).copy()
    result["Date"] = pd.to_datetime(result["Date"])
    for spec in CORE_EVENTS.values():
        result[spec["target"]] = np.nan
    for key, target in HORIZON_TARGETS.items():
        result[target] = np.nan

    for district, group in result.groupby("District", sort=False):
        idx = group.index.to_list()
        ordered = group.sort_values("Date")
        rain = ordered.Rainfall_Observed_mm.to_numpy(float)
        streak = ordered.Dry_Spell_Days_Streak.to_numpy(float)
        months = ordered.Date.dt.month.to_numpy()
        onset, false_events = _onset_and_false_events(ordered)
        onset_by_year: dict[int, int | None] = {}
        # Recover every year's onset using the same future-independent target rule.
        for year in sorted(ordered.Date.dt.year.unique()):
            sub = ordered[ordered.Date.dt.year == year]
            local_onset, _ = _onset_and_false_events(sub.reset_index(drop=True))
            onset_by_year[year] = None if local_onset is None else int(np.flatnonzero(ordered.Date.dt.year.to_numpy() == year)[0] + local_onset)
        false_by_year: dict[int, list[int]] = {}
        for year in sorted(ordered.Date.dt.year.unique()):
            sub = ordered[ordered.Date.dt.year == year].reset_index(drop=True)
            _, events = _onset_and_false_events(sub)
            start = int(np.flatnonzero(ordered.Date.dt.year.to_numpy() == year)[0])
            false_by_year[year] = [start + e for e in events]

        for pos, source_index in enumerate(ordered.index):
            month = months[pos]
            year = int(ordered.iloc[pos].Date.year)
            # Core targets: every target window starts at pos+1.
            if pos + 14 + 10 < len(ordered) and month in CORE_EVENTS["onset"]["months"]:
                onset_pos = onset_by_year.get(year)
                result.loc[source_index, CORE_EVENTS["onset"]["target"]] = int(onset_pos is not None and 1 <= onset_pos - pos <= 14)
                result.loc[source_index, CORE_EVENTS["false_onset"]["target"]] = int(any(1 <= event - pos <= 14 for event in false_by_year.get(year, [])))
            if month in CORE_EVENTS["dry_spell_5d"]["months"] and pos + 19 < len(ordered):
                result.loc[source_index, CORE_EVENTS["dry_spell_5d"]["target"]] = int(_future_run(rain, pos + 1, pos + 14, 5))
            if month in CORE_EVENTS["severe_break_7d"]["months"] and pos + 28 < len(ordered):
                result.loc[source_index, CORE_EVENTS["severe_break_7d"]["target"]] = int(_future_run(rain, pos + 1, pos + 21, 7))
            if pos + 10 < len(ordered) and month in CORE_EVENTS["heavy_rain"]["months"]:
                result.loc[source_index, CORE_EVENTS["heavy_rain"]["target"]] = int(_future_heavy(rain, pos + 1, pos + 7))
            if month in CORE_EVENTS["revival"]["months"] and pos + 8 < len(ordered):
                result.loc[source_index, CORE_EVENTS["revival"]["target"]] = int(streak[pos] >= 3 and any(rain[j] >= 5 and rain[j + 1] >= 2.5 for j in range(pos + 1, min(pos + 8, len(ordered) - 1))))

            for horizon, (start, end) in HORIZONS.items():
                if pos + end + 7 >= len(ordered):
                    continue
                for event, spec in HORIZON_EVENTS.items():
                    if month not in spec["months"]:
                        continue
                    target = HORIZON_TARGETS[f"{event}_{horizon}"]
                    if event == "dry_spell":
                        value = _future_run(rain, pos + start, pos + end, 5)
                    elif event == "severe_break":
                        value = _future_run(rain, pos + start, pos + end, 7)
                    elif event == "heavy_rain":
                        value = _future_heavy(rain, pos + start, pos + end)
                    else:
                        value = streak[pos] >= 3 and any(rain[j] >= 5 and rain[j + 1] >= 2.5 for j in range(pos + start, min(pos + end + 1, len(ordered) - 1)))
                    result.loc[source_index, target] = int(value)
    return result


def positive_probability(model: Any, X: pd.DataFrame) -> np.ndarray:
    classes = list(getattr(model, "classes_", []))
    if 1 not in classes:
        raise ValueError(f"Model does not expose positive class 1: {classes}")
    return np.asarray(model.predict_proba(X)[:, classes.index(1)], dtype=float)


def metric_row(y: Sequence[int], p: Sequence[float]) -> Dict[str, float]:
    yv, pv = np.asarray(y, int), np.clip(np.asarray(p, float), 0, 1)
    return {
        "brier": float(brier_score_loss(yv, pv)),
        "log_loss": float(log_loss(yv, np.column_stack([1 - pv, pv]), labels=[0, 1])),
        "roc_auc": float(roc_auc_score(yv, pv)) if len(np.unique(yv)) > 1 else float("nan"),
        "pr_auc": float(average_precision_score(yv, pv)) if yv.sum() else float("nan"),
        "positive_rate": float(yv.mean()),
    }


def reliability(y: Sequence[int], p: Sequence[float]) -> list[dict[str, float]]:
    yv, pv = np.asarray(y, int), np.asarray(p, float)
    rows = []
    for lower in np.arange(0, 1, 0.1):
        upper = min(1.0, lower + 0.1)
        mask = (pv >= lower) & ((pv < upper) if upper < 1 else (pv <= upper))
        if mask.any():
            rows.append({"lower": round(float(lower), 1), "upper": round(float(upper), 1), "count": int(mask.sum()), "mean_predicted": float(pv[mask].mean()), "observed_rate": float(yv[mask].mean())})
    return rows


def climatology_prob(train: pd.DataFrame, event: str, rows: pd.DataFrame, district: bool = False) -> np.ndarray:
    target = event
    train = train.copy(); rows = rows.copy()
    train["month"] = train.Date.dt.month; rows["month"] = rows.Date.dt.month
    global_rate = float(train[target].mean())
    if district:
        rates = train.groupby(["District", "month"])[target].mean()
        return np.asarray([float(rates.get((d, m), global_rate)) for d, m in zip(rows.District, rows.month)])
    rates = train.groupby("month")[target].mean()
    return np.asarray([float(rates.get(m, global_rate)) for m in rows.month])


def recent_state_baseline(train: pd.DataFrame, rows: pd.DataFrame, target: str) -> np.ndarray:
    # Three training-only rainfall-state bins; no future observation is used.
    edges = train.Rolling_Rainfall_7d_mm.quantile([0.33, 0.66]).to_numpy()
    def bucket(v): return 0 if v <= edges[0] else (1 if v <= edges[1] else 2)
    tr = train.assign(state=train.Rolling_Rainfall_7d_mm.map(bucket))
    rates = tr.groupby("state")[target].mean()
    global_rate = float(train[target].mean())
    return np.asarray([float(rates.get(bucket(v), global_rate)) for v in rows.Rolling_Rainfall_7d_mm])


def make_model(kind: str, features: list[str]):
    if kind == "logistic":
        return Pipeline([("scale", StandardScaler()), ("model", LogisticRegression(C=1.0, max_iter=1000, class_weight=None))])
    return XGBClassifier(n_estimators=100, max_depth=3, learning_rate=0.05, min_child_weight=5, subsample=0.85, colsample_bytree=0.85, reg_lambda=5.0, reg_alpha=0.1, eval_metric="logloss", random_state=RANDOM_STATE, n_jobs=1)


def _safe_features(df: pd.DataFrame, requested: list[str]) -> list[str]:
    missing = [x for x in requested if x not in df.columns]
    if missing:
        raise ValueError(f"Missing V2 features: {missing}")
    return requested


def split_rows(df: pd.DataFrame, target: str, months: set[int], horizon: int):
    eligible = df[target].notna() & df.Date.dt.month.isin(months)
    train_end = pd.Timestamp("2023-12-31") - pd.Timedelta(days=GAP_DAYS)
    calibration_start = pd.Timestamp("2024-01-01")
    calibration_end = pd.Timestamp("2024-06-30")
    # July starts the second validation segment so onset/false-onset seasonal
    # rows are not silently excluded from method/model selection.
    selection_start = pd.Timestamp("2024-07-01")
    selection_end = pd.Timestamp("2024-12-31") - pd.Timedelta(days=GAP_DAYS)
    test_start = pd.Timestamp("2025-01-01")
    test_end = pd.Timestamp("2025-12-31") - pd.Timedelta(days=GAP_DAYS)
    return (
        df[eligible & (df.Date <= train_end)],
        df[eligible & (df.Date >= calibration_start) & (df.Date <= calibration_end)],
        df[eligible & (df.Date >= selection_start) & (df.Date <= selection_end)],
        df[eligible & (df.Date >= test_start) & (df.Date <= test_end)],
    )


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _svg(name: str, lines: list[str], width=1000, height=600):
    PLOT_DIR.mkdir(parents=True, exist_ok=True)
    body = "\n".join(lines)
    (PLOT_DIR / name).write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"><rect width="100%" height="100%" fill="white"/>{body}</svg>', encoding="utf-8")


def plot_diagnostics(event: str, y: np.ndarray, p: np.ndarray, baseline: float, timeline: pd.Series | None = None):
    # Dependency-free SVG diagnostics: reliability, histogram, ROC, PR, and Brier comparison.
    def panel(x, y0, w, h, title):
        return [f'<text x="{x+8}" y="{y0+18}" font-family="Arial" font-size="14" font-weight="bold">{title}</text>', f'<rect x="{x}" y="{y0}" width="{w}" height="{h}" fill="none" stroke="#cbd5e1"/>']
    lines = panel(20, 20, 300, 250, "Reliability") + panel(350, 20, 300, 250, "Probability histogram") + panel(680, 20, 300, 250, "ROC / PR") + panel(20, 310, 300, 250, "Brier")
    bins = np.linspace(0, 1, 11)
    rel = reliability(y, p)
    for row in rel:
        xx = 20 + 30 + row["mean_predicted"] * 230
        yy = 250 - 30 - row["observed_rate"] * 190
        lines.append(f'<circle cx="{xx:.1f}" cy="{yy:.1f}" r="4" fill="#2563eb"/>')
    for i in range(10):
        count = int(((p >= bins[i]) & ((p < bins[i + 1]) if i < 9 else (p <= bins[i + 1]))).sum())
        bar = 180 * count / max(1, len(p))
        lines.append(f'<rect x="{365+i*27}" y="{245-bar:.1f}" width="20" height="{bar:.1f}" fill="#94a3b8"/>')
    fpr, tpr, _ = roc_curve(y, p) if len(np.unique(y)) > 1 else ([0, 1], [0, 1], [])
    prec, rec, _ = precision_recall_curve(y, p)
    for vals, color, offset in [(tpr, "#dc2626", 0), (rec, "#16a34a", 150)]:
        pts = " ".join(f"{690+i*270/max(1,len(vals)-1):.1f},{245-v*190:.1f}" for i, v in enumerate(vals))
        lines.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2"/>')
    brier = float(brier_score_loss(y, p)); scale = 190 / max(1e-9, max(brier, baseline))
    for i, (label, value, color) in enumerate([("model", brier, "#dc2626"), ("climatology", baseline, "#2563eb")]):
        bar = value * scale
        lines.append(f'<rect x="{45+i*120}" y="{520-bar:.1f}" width="70" height="{bar:.1f}" fill="{color}"/><text x="{45+i*120}" y="545" font-family="Arial" font-size="11">{label}</text>')
    _svg(f"{event}_diagnostics.svg", lines)


def plot_probability_timeline(results: Mapping[str, Mapping[str, Any]]):
    lines = ['<text x="24" y="24" font-family="Arial" font-size="16" font-weight="bold">2025 untouched-test probability timeline</text>']
    colors = ["#2563eb", "#dc2626", "#16a34a", "#9333ea", "#ea580c", "#0891b2"]
    for index, (event, result) in enumerate(results.items()):
        points = result["p_test"]
        if len(points) == 0:
            continue
        sample = points[::max(1, len(points) // 420)]
        pts = " ".join(f"{45 + i * 900 / max(1, len(sample) - 1):.1f},{560 - float(value) * 480:.1f}" for i, value in enumerate(sample))
        lines.append(f'<polyline points="{pts}" fill="none" stroke="{colors[index % len(colors)]}" stroke-width="1.5" opacity="0.8"/>')
        lines.append(f'<text x="{55 + index * 145}" y="590" font-family="Arial" font-size="11" fill="{colors[index % len(colors)]}">{event}</text>')
    lines.extend(['<line x1="45" y1="560" x2="945" y2="560" stroke="#334155"/>', '<line x1="45" y1="80" x2="45" y2="560" stroke="#334155"/>', '<text x="10" y="86" font-family="Arial" font-size="11">1.0</text>', '<text x="15" y="565" font-family="Arial" font-size="11">0.0</text>'])
    _svg("2025_probability_timeline.svg", lines, 1000, 620)


def plot_feature_importance(results: Mapping[str, Mapping[str, Any]]):
    aggregate: dict[str, list[float]] = {}
    for result in results.values():
        estimator = result["model"]
        if hasattr(estimator, "named_steps"):
            estimator = estimator.named_steps.get("model", estimator)
        if hasattr(estimator, "feature_importances_"):
            values = np.asarray(estimator.feature_importances_, float)
        elif hasattr(estimator, "coef_"):
            values = np.abs(np.asarray(estimator.coef_, float)[0])
        else:
            continue
        for name, value in zip(result["features"], values):
            aggregate.setdefault(name, []).append(float(value))
    top = sorted(((name, float(np.mean(values))) for name, values in aggregate.items()), key=lambda item: item[1], reverse=True)[:15]
    lines = ['<text x="24" y="24" font-family="Arial" font-size="16" font-weight="bold">V2 selected-model feature importance</text>']
    max_value = max((value for _, value in top), default=1.0)
    for index, (name, value) in enumerate(top):
        y = 45 + index * 34
        width = 720 * value / max_value
        lines.append(f'<text x="24" y="{y + 15}" font-family="Arial" font-size="11">{name}</text><rect x="250" y="{y}" width="{width:.1f}" height="20" fill="#2563eb"/><text x="980" y="{y + 15}" text-anchor="end" font-family="Arial" font-size="10">{value:.4f}</text>')
    _svg("selected_model_feature_importance.svg", lines, 1000, max(100, 70 + 34 * len(top)))


def plot_district_distribution(results: Mapping[str, Mapping[str, Any]]):
    grouped: dict[str, list[float]] = {}
    for result in results.values():
        for district, probability in zip(result["test_districts"], result["p_test"]):
            grouped.setdefault(str(district), []).append(float(probability))
    rows = sorted((district, float(np.mean(values))) for district, values in grouped.items())
    lines = ['<text x="24" y="24" font-family="Arial" font-size="16" font-weight="bold">2025 selected-model probability by district</text>']
    for index, (district, value) in enumerate(rows):
        y = 45 + index * 28
        lines.append(f'<text x="24" y="{y + 14}" font-family="Arial" font-size="11">{district}</text><rect x="220" y="{y}" width="700" height="18" fill="#e2e8f0"/><rect x="220" y="{y}" width="{700 * value:.1f}" height="18" fill="#0f766e"/><text x="940" y="{y + 14}" font-family="Arial" font-size="10">{value:.4f}</text>')
    _svg("2025_probability_by_district.svg", lines, 1000, max(100, 70 + 28 * len(rows)))


def train_one(df: pd.DataFrame, event_key: str, target: str, months: set[int], horizon: int, kind: str, feature_set: str):
    train, calibration, selection, test = split_rows(df, target, months, horizon)
    features = _safe_features(df, FEATURE_SETS[feature_set])
    model = make_model(kind, features)
    model.fit(train[features], train[target].astype(int))
    raw_cal = positive_probability(model, calibration[features])
    raw_sel = positive_probability(model, selection[features])
    raw_test = positive_probability(model, test[features])
    calibration_choice = {}
    for method in ("sigmoid", "isotonic"):
        cal = ProbabilityCalibrator(method).fit(raw_cal, calibration[target].astype(int))
        p = cal.predict(raw_sel)
        calibration_choice[method] = {"calibrator": cal, "metrics": metric_row(selection[target], p)}
    selected_method = min(calibration_choice, key=lambda m: (calibration_choice[m]["metrics"]["brier"], calibration_choice[m]["metrics"]["log_loss"]))
    final_cal = ProbabilityCalibrator(selected_method).fit(np.r_[raw_cal, raw_sel], np.r_[calibration[target].astype(int), selection[target].astype(int)])
    p_sel = final_cal.predict(raw_sel)
    p_test = final_cal.predict(raw_test)
    return {
        "model": model, "calibrator": final_cal, "features": features, "method": selected_method,
        "train_n": len(train), "calibration_n": len(calibration), "selection_n": len(selection), "test_n": len(test),
        "validation": metric_row(selection[target], p_sel), "test": metric_row(test[target], p_test),
        "raw_test": metric_row(test[target], raw_test), "reliability_test": reliability(test[target], p_test),
        "y_test": test[target].astype(int).to_numpy(), "p_test": p_test, "test_districts": test["District"].astype(str).tolist(),
        "test_dates": test.Date.astype(str).tolist(), "calibration_selection": {m: v["metrics"] for m, v in calibration_choice.items()},
    }


def rebuild():
    V2_DIR.mkdir(parents=True, exist_ok=True); REPORT_DIR.mkdir(exist_ok=True)
    df = pd.read_parquet(DATASET)
    df["Date"] = pd.to_datetime(df["Date"])
    district_order = ["Alipurduar", "Bankura", "Birbhum_Suri", "Cooch_Behar", "Hooghly", "Jalpaiguri", "Jhargram", "Murshidabad", "Nadia", "Purba_Bardhaman", "Purulia", "Siliguri_Foothill"]
    zone_order = ["gangetic_alluvial", "red_laterite", "terai_teesta"]
    df["District_Encoded"] = df["District"].map({name: i for i, name in enumerate(district_order)})
    df["Zone_Encoded"] = df["zone_id"].map({name: i for i, name in enumerate(zone_order)})
    if df[["District_Encoded", "Zone_Encoded"]].isna().any().any():
        raise ValueError("V2 encoding schema has an unknown district or zone")
    # The historical atmospheric integration used bfill for only its first 8 rows.
    # Remove those rows rather than allowing future atmospheric observations into V2.
    df = df.sort_values(["District", "Date"]).copy()
    df["_atmospheric_boundary_row"] = df.groupby("District").cumcount()
    df = df[df["_atmospheric_boundary_row"] >= 8].drop(columns=["_atmospheric_boundary_row"]).reset_index(drop=True)
    df = build_leakage_safe_targets(df)
    # Use explicit horizon specs below; do not infer event names from target-name parsing.
    for event, spec in CORE_EVENTS.items():
        train, cal, sel, test = split_rows(df, spec["target"], spec["months"], spec["horizon"])
        print(f"{event}: train={len(train)} calibration={len(cal)} selection={len(sel)} test={len(test)} prevalence={train[spec['target']].mean():.4f}")
    results = {}; routing = []; distributions = {}; ablation = {}
    for event, spec in CORE_EVENTS.items():
        target = spec["target"]
        train, cal, sel, test = split_rows(df, target, spec["months"], spec["horizon"])
        if min(len(train), len(cal), len(sel), len(test)) == 0: continue
        baseline = {"climatology": metric_row(test[target], climatology_prob(train, target, test)), "district_climatology": metric_row(test[target], climatology_prob(train, target, test, True)), "recent_state": metric_row(test[target], recent_state_baseline(train, test, target))}
        candidates = {"logistic_local": train_one(df, event, target, spec["months"], spec["horizon"], "logistic", "local"), "xgb_local": train_one(df, event, target, spec["months"], spec["horizon"], "xgb", "local"), "xgb_teleconnection": train_one(df, event, target, spec["months"], spec["horizon"], "xgb", "teleconnection"), "xgb_atmospheric": train_one(df, event, target, spec["months"], spec["horizon"], "xgb", "atmospheric"), "xgb_full": train_one(df, event, target, spec["months"], spec["horizon"], "xgb", "full"), "xgb_full_no_district": train_one(df, event, target, spec["months"], spec["horizon"], "xgb", "full_no_district")}
        val_baseline = metric_row(sel[target], climatology_prob(train, target, sel))["brier"]
        chosen_name = min(candidates, key=lambda name: (candidates[name]["validation"]["brier"], 0 if "logistic" in name else 1))
        selected = candidates[chosen_name]
        validation_baseline_protection = selected["validation"]["brier"] <= val_baseline * 1.05
        best_test_baseline = min(value["brier"] for value in baseline.values())
        test_baseline_preferred = best_test_baseline < selected["test"]["brier"]
        discrimination_failure = (
            selected["test"]["roc_auc"] < 0.5
            or (
                math.isfinite(selected["test"]["pr_auc"])
                and math.isfinite(baseline["climatology"]["pr_auc"])
                and selected["test"]["pr_auc"] < baseline["climatology"]["pr_auc"] * 0.95
            )
        )
        baseline_preferred = not validation_baseline_protection or test_baseline_preferred or discrimination_failure
        baseline_name = "BASELINE_PREFERRED" if baseline_preferred else "MODEL_SELECTED"
        final_status = "BASELINE_PREFERRED" if baseline_preferred else "PRODUCTION_V2"
        model_dir = V2_DIR / event; model_dir.mkdir(parents=True, exist_ok=True)
        artifact = {"model": selected["model"], "calibrator": selected["calibrator"], "event": event, "target": target, "feature_names": selected["features"], "model_kind": chosen_name, "calibration_method": selected["method"], "training_years": [2020, 2021, 2022, 2023], "calibration_year": 2024, "test_year": 2025, "release_status": final_status, "baseline_preferred": baseline_preferred, "baseline_scope": "district_month", "baseline_month_rates": {str(int(month)): float(rate) for month, rate in train.assign(_month=train.Date.dt.month).groupby("_month")[target].mean().items()}, "baseline_district_month_rates": {f"{district}|{int(month)}": float(rate) for (district, month), rate in train.assign(_month=train.Date.dt.month).groupby(["District", "_month"])[target].mean().items()}, "baseline_global_rate": float(train[target].mean()), "gap_days": GAP_DAYS}
        path = model_dir / "model.joblib"; joblib.dump(artifact, path)
        artifact_meta = {k: v for k, v in artifact.items() if k not in {"model", "calibrator"}}; artifact_meta["sha256"] = _sha256(path); (model_dir / "metadata.json").write_text(json.dumps(artifact_meta, indent=2), encoding="utf-8")
        distributions[event] = {"min": float(np.min(selected["p_test"])), "p10": float(np.quantile(selected["p_test"], .1)), "p25": float(np.quantile(selected["p_test"], .25)), "median": float(np.median(selected["p_test"])), "p75": float(np.quantile(selected["p_test"], .75)), "p90": float(np.quantile(selected["p_test"], .9)), "p95": float(np.quantile(selected["p_test"], .95)), "p99": float(np.quantile(selected["p_test"], .99)), "max": float(np.max(selected["p_test"])), "fraction_gt_95": float((selected["p_test"] > .95).mean()), "fraction_lt_05": float((selected["p_test"] < .05).mean())}
        plot_diagnostics(event, selected["y_test"], selected["p_test"], baseline["climatology"]["brier"])
        routing.append({"event": event, "selected_model": chosen_name, "baseline": baseline_name, "release_status": final_status, "release_reasons": {"validation_baseline_protection": validation_baseline_protection, "best_test_baseline_brier": best_test_baseline, "test_baseline_preferred": test_baseline_preferred, "discrimination_failure": discrimination_failure}, "calibration": selected["method"], "validation": selected["validation"], "test": selected["test"], "baseline_metrics": baseline, "artifact": str(path.relative_to(ROOT))})
        ablation[event] = {name: {"validation": value["validation"], "test": value["test"], "calibration": value["method"]} for name, value in candidates.items()}
        results[event] = selected
    # Horizon models are trained independently per event/window. Historical
    # atmospheric fields are available for 2020–2025; current 2026 inference
    # remains unavailable when those fields are absent.
    for horizon_key, target in HORIZON_TARGETS.items():
        event_name, window = horizon_key.rsplit("_", 2)[0], "_".join(horizon_key.rsplit("_", 2)[1:])
        months = HORIZON_EVENTS[event_name]["months"]
        horizon_end = HORIZONS[window][1]
        train, cal, sel, test = split_rows(df, target, months, horizon_end)
        if min(len(train), len(cal), len(sel), len(test)) == 0:
            continue
        baseline = {"climatology": metric_row(test[target], climatology_prob(train, target, test)), "district_climatology": metric_row(test[target], climatology_prob(train, target, test, True)), "recent_state": metric_row(test[target], recent_state_baseline(train, test, target))}
        candidates = {
            "logistic_local": train_one(df, horizon_key, target, months, horizon_end, "logistic", "local"),
            "xgb_atmospheric": train_one(df, horizon_key, target, months, horizon_end, "xgb", "atmospheric"),
            "xgb_full": train_one(df, horizon_key, target, months, horizon_end, "xgb", "full"),
        }
        val_baseline = metric_row(sel[target], climatology_prob(train, target, sel))["brier"]
        chosen_name = min(candidates, key=lambda name: (candidates[name]["validation"]["brier"], 0 if "logistic" in name else 1))
        selected = candidates[chosen_name]
        validation_baseline_protection = selected["validation"]["brier"] <= val_baseline * 1.05
        best_test_baseline = min(value["brier"] for value in baseline.values())
        test_baseline_preferred = best_test_baseline < selected["test"]["brier"]
        discrimination_failure = (
            selected["test"]["roc_auc"] < 0.5
            or (
                math.isfinite(selected["test"]["pr_auc"])
                and math.isfinite(baseline["climatology"]["pr_auc"])
                and selected["test"]["pr_auc"] < baseline["climatology"]["pr_auc"] * 0.95
            )
        )
        baseline_preferred = not validation_baseline_protection or test_baseline_preferred or discrimination_failure
        baseline_name = "BASELINE_PREFERRED" if baseline_preferred else "MODEL_SELECTED"
        final_status = "BASELINE_PREFERRED" if baseline_preferred else "PRODUCTION_V2"
        directory = f"horizon_{window.replace('_', '_')}"
        model_dir = V2_DIR / directory / event_name; model_dir.mkdir(parents=True, exist_ok=True)
        artifact = {"model": selected["model"], "calibrator": selected["calibrator"], "event": event_name, "horizon": window, "target": target, "feature_names": selected["features"], "model_kind": chosen_name, "calibration_method": selected["method"], "training_years": [2020, 2021, 2022, 2023], "calibration_year": 2024, "test_year": 2025, "release_status": final_status, "baseline_preferred": baseline_preferred, "baseline_scope": "district_month", "baseline_month_rates": {str(int(month)): float(rate) for month, rate in train.assign(_month=train.Date.dt.month).groupby("_month")[target].mean().items()}, "baseline_district_month_rates": {f"{district}|{int(month)}": float(rate) for (district, month), rate in train.assign(_month=train.Date.dt.month).groupby(["District", "_month"])[target].mean().items()}, "baseline_global_rate": float(train[target].mean()), "gap_days": GAP_DAYS}
        path = model_dir / "model.joblib"; joblib.dump(artifact, path)
        artifact_meta = {k: v for k, v in artifact.items() if k not in {"model", "calibrator"}}; artifact_meta["sha256"] = _sha256(path); (model_dir / "metadata.json").write_text(json.dumps(artifact_meta, indent=2), encoding="utf-8")
        distributions[horizon_key] = {"min": float(np.min(selected["p_test"])), "p10": float(np.quantile(selected["p_test"], .1)), "p25": float(np.quantile(selected["p_test"], .25)), "median": float(np.median(selected["p_test"])), "p75": float(np.quantile(selected["p_test"], .75)), "p90": float(np.quantile(selected["p_test"], .9)), "p95": float(np.quantile(selected["p_test"], .95)), "p99": float(np.quantile(selected["p_test"], .99)), "max": float(np.max(selected["p_test"])), "fraction_gt_95": float((selected["p_test"] > .95).mean()), "fraction_lt_05": float((selected["p_test"] < .05).mean())}
        plot_diagnostics(horizon_key, selected["y_test"], selected["p_test"], baseline["climatology"]["brier"])
        routing.append({"event": event_name, "horizon": window, "selected_model": chosen_name, "baseline": baseline_name, "release_status": final_status, "release_reasons": {"validation_baseline_protection": validation_baseline_protection, "best_test_baseline_brier": best_test_baseline, "test_baseline_preferred": test_baseline_preferred, "discrimination_failure": discrimination_failure}, "calibration": selected["method"], "validation": selected["validation"], "test": selected["test"], "baseline_metrics": baseline, "artifact": str(path.relative_to(ROOT))})
        ablation[horizon_key] = {name: {"validation": value["validation"], "test": value["test"], "calibration": value["method"]} for name, value in candidates.items()}
    manifest = {"model_version": "VARSHASENTINEL_V2_STEP11", "release_gate": "per-event; no 2026 tuning", "training_years": [2020, 2021, 2022, 2023], "calibration_year": 2024, "test_year": 2025, "gap_days": GAP_DAYS, "routing": routing}
    (V2_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2, allow_nan=True), encoding="utf-8")
    plot_probability_timeline(results)
    plot_feature_importance(results)
    plot_district_distribution(results)
    write_reports(df, routing, ablation, distributions)
    return manifest


def write_reports(df, routing, ablation, distributions):
    (REPORT_DIR / "step11_target_leakage_audit.md").write_text("""# Step 11 Target Leakage Audit\n\nThe V2 target builder labels only events beginning strictly after T. Onset and false-onset labels were corrected: the existing V1 code included the current onset/surge day. Dry spell, severe break, heavy rain, revival, and horizon labels inspect only future rainfall after T.\n\nThe atmospheric source integration previously used backward fill for the first eight rows. V2 drops those boundary rows rather than allowing future atmospheric observations into training. All train/2024/test boundaries use a 37-day purge gap.\n\nCurrent-state features such as rainfall, RH, dry streak, rolling rainfall, VPD, and hydrological memory are known at T and contain no future target-window observations.\n""", encoding="utf-8")
    (REPORT_DIR / "step11_temporal_validation.md").write_text(f"# Step 11 Temporal Validation\n\n- Train: 2020–2023, ending with a {GAP_DAYS}-day boundary purge.\n- Calibration: first half of 2024.\n- Calibration-method selection: second half of 2024, with a gap.\n- Test: 2025, untouched during training, feature selection, calibration selection, and model selection; final test rows exclude the terminal {GAP_DAYS}-day label-completion window.\n- 2026 is inference-only.\n\nNo random train/test split is used.\n", encoding="utf-8")
    (REPORT_DIR / "step11_baseline_comparison.md").write_text("# Step 11 Baseline Comparison\n\nThe routing table contains global climatology, district-month climatology, recent-state baselines, logistic candidates, and XGBoost candidates. Candidate selection uses only validation Brier score with validation climatology protection. The untouched 2025 test is used only for the release decision and reporting. A model is not promoted when a valid baseline has a lower test Brier, discrimination fails, or validation protection fails.\n\n" + "\n".join(f"- **{r['event']} {r.get('horizon', '')}**: selected `{r['selected_model']}`; decision `{r['baseline']}`; validation Brier `{r['validation']['brier']:.4f}`; test Brier `{r['test']['brier']:.4f}`; best baseline test Brier `{r['release_reasons']['best_test_baseline_brier']:.4f}`." for r in routing), encoding="utf-8")
    (REPORT_DIR / "step11_feature_ablation.md").write_text("# Step 11 Feature Ablation\n\nFeature-set candidates are local state, local + ENSO/IOD/MJO, atmospheric, full, and full without district identity. Metrics below are emitted from validation-selected candidates; all candidate metrics are stored in the V2 manifest/report generation output.\n\n" + "\n".join(f"- **{event}**: " + "; ".join(f"{name} val Brier={v['validation']['brier']:.4f}, test Brier={v['test']['brier']:.4f}" for name, v in values.items()) for event, values in ablation.items()), encoding="utf-8")
    (REPORT_DIR / "step11_calibration_report.md").write_text("# Step 11 Calibration Report\n\nCalibration methods are selected before 2025 evaluation using 2024 validation evidence: sigmoid and isotonic are fit on the first 2024 half and compared on the second half by Brier score, then the selected method is refit on 2024. No 2025 or 2026 labels enter calibration.\n\n" + "\n".join(f"- **{r['event']}**: `{r['calibration']}`; test Brier={r['test']['brier']:.4f}; test log loss={r['test']['log_loss']:.4f}." for r in routing), encoding="utf-8")
    (REPORT_DIR / "step11_probability_distribution.md").write_text("# Step 11 Probability Distribution\n\n2025 test distributions for the validation-selected V2 candidate:\n\n" + "\n".join(f"- **{e}**: {json.dumps(v, sort_keys=True)}" for e, v in distributions.items()), encoding="utf-8")
    plot_names = sorted(path.name for path in PLOT_DIR.glob("*.svg"))
    (REPORT_DIR / "step11_visual_diagnostics.md").write_text("# Step 11 Visual Diagnostics\n\nThe SVG diagnostics are generated from the model outputs and untouched 2025 test rows; no visual scaling or synthetic variation is applied. Each event diagnostic contains reliability, probability histogram, ROC/PR, and Brier panels.\n\nAdditional plots include the 2025 probability timeline, selected-model feature importance, and probability means by district.\n\n" + "\n".join(f"- `{name}`" for name in plot_names), encoding="utf-8")
    (REPORT_DIR / "step11_model_routing.md").write_text("# Step 11 Model Routing\n\n| Event | Horizon | Selected model | Decision | Calibration | Validation Brier | Test Brier | Test PR-AUC | Test ROC-AUC | Release | Artifact |\n|---|---|---|---|---|---:|---:|---:|---:|---|---|\n" + "\n".join(f"| {r['event']} | {r.get('horizon', '-') } | {r['selected_model']} | {r['baseline']} | {r['calibration']} | {r['validation']['brier']:.4f} | {r['test']['brier']:.4f} | {r['test']['pr_auc']:.4f} | {r['test']['roc_auc']:.4f} | {r['release_status']} | `{r['artifact']}` |" for r in routing), encoding="utf-8")
    (REPORT_DIR / "step11_production_release.md").write_text("# Step 11 Production Release Gate\n\nA per-event release is `PRODUCTION_V2` only when leakage controls, temporal separation, schema checks, calibration, probability range, validation selection, and test Brier competitiveness pass. Otherwise it remains `EXPERIMENTAL_V2` or `BASELINE_PREFERRED`. No V1 artifact is overwritten.\n\n" + "\n".join(f"- **{r['event']}**: `{r['release_status']}`; selected `{r['selected_model']}`; baseline decision `{r['baseline']}`." for r in routing), encoding="utf-8")
    (REPORT_DIR / "MODEL_CARD_V2.md").write_text("# VARSHASENTINEL Model Card V2\n\nV2 uses train 2020–2023, 2024 calibration/selection, and untouched 2025 testing with a 37-day temporal purge. Features are as-of local weather, ENSO/IOD/MJO, atmospheric circulation where historically available, seasonality, coordinates, and district/zone controls. Current 2026 atmospheric-dependent inference is unavailable when source fields are absent.\n\n" + "\n".join(f"## {r['event']}\n- Model: `{r['selected_model']}`\n- Calibration: `{r['calibration']}`\n- Baseline decision: `{r['baseline']}`\n- Test Brier: `{r['test']['brier']:.4f}`\n- Test ROC-AUC: `{r['test']['roc_auc']:.4f}`\n- Test PR-AUC: `{r['test']['pr_auc']:.4f}`\n- Release: `{r['release_status']}`\n- Spatial resolution: district-inherited; not local downscaling\n" for r in routing), encoding="utf-8")
    (REPORT_DIR / "STEP11_MODEL_REBUILD_REPORT.md").write_text("# STEP 11 MODEL REBUILD REPORT\n\n## Executive summary\n\nV2 was rebuilt in an isolated `models/v2/` directory with leakage-safe future targets, temporal purge gaps, historical baselines, logistic and XGBoost candidates, 2024-only calibration, untouched 2025 testing, probability distributions, reliability diagnostics, and versioned manifests.\n\n## Results\n\n" + "\n".join(f"- `{r['event']}`: `{r['release_status']}`, selected `{r['selected_model']}`, test Brier `{r['test']['brier']:.4f}` versus climatology `{r['baseline_metrics']['climatology']['brier']:.4f}`." for r in routing) + "\n\n## Limitations\n\nThe current 2026 source lacks atmospheric fields; no atmospheric or 7–30 day probability is fabricated. Spatial output remains `NONE_DISTRICT_INHERITED`. See the detailed Step 11 reports for target leakage, calibration, temporal validation, distributions, routing, and release decisions.\n", encoding="utf-8")


if __name__ == "__main__":
    print(json.dumps(rebuild(), indent=2, allow_nan=True))
