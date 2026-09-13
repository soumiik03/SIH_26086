"""Inference loader for the isolated Step 11 V2 artifacts.

This module does not replace the V1 engine or change the FastAPI contract.  It
provides a strict, auditable V2 inference path for validation and future
promotion.  Missing features produce ``UNAVAILABLE``; they are never treated
as zero or LOW risk.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import joblib
import numpy as np
import pandas as pd

from .step11_model_rebuild import CORE_EVENTS

# Keep the inference module independent from V1 model files.  These mappings
# match the training schema emitted by step11_model_rebuild.py.
DISTRICT_ORDER = [
    "Alipurduar", "Bankura", "Birbhum_Suri", "Cooch_Behar", "Hooghly",
    "Jalpaiguri", "Jhargram", "Murshidabad", "Nadia", "Purba_Bardhaman",
    "Purulia", "Siliguri_Foothill",
]
ZONE_ORDER = ["gangetic_alluvial", "red_laterite", "terai_teesta"]
DISTRICT_ZONE_MAP = {
    "Purba_Bardhaman": "gangetic_alluvial", "Hooghly": "gangetic_alluvial",
    "Nadia": "gangetic_alluvial", "Murshidabad": "gangetic_alluvial",
    "Purulia": "red_laterite", "Bankura": "red_laterite",
    "Jhargram": "red_laterite", "Birbhum_Suri": "red_laterite",
    "Jalpaiguri": "terai_teesta", "Alipurduar": "terai_teesta",
    "Cooch_Behar": "terai_teesta", "Siliguri_Foothill": "terai_teesta",
}
CORE_MONTHS = {
    "onset": {5, 6, 7}, "false_onset": {5, 6, 7},
    "dry_spell_5d": {6, 7, 8, 9, 10}, "severe_break_7d": {6, 7, 8, 9, 10},
    "heavy_rain": set(range(1, 13)), "revival": {6, 7, 8, 9, 10},
}
HORIZON_MONTHS = {
    "dry_spell": {6, 7, 8, 9, 10}, "severe_break": {6, 7, 8, 9, 10},
    "heavy_rain": set(range(1, 13)), "revival": {6, 7, 8, 9, 10},
}
HORIZONS = ("7_14d", "15_21d", "22_30d")
HORIZON_EVENTS = ("dry_spell", "severe_break", "heavy_rain", "revival")
HORIZON_DISCLAIMER = (
    "Statistical probabilistic outlook based on available climate and observation-state "
    "information; not an NWP/S2S forecast."
)


class ForecastEngineV2:
    """Load and run only the manifest-routed V2 artifacts."""

    def __init__(self, root: str | Path | None = None):
        self.root = Path(root) if root else Path(__file__).resolve().parents[1]
        self.model_dir = self.root / "models" / "v2"
        self.manifest = json.loads((self.model_dir / "manifest.json").read_text(encoding="utf-8"))
        self.routing = self.manifest["routing"]
        self._artifacts: dict[tuple[str, str | None], dict[str, Any]] = {}
        for route in self.routing:
            key = (route["event"], route.get("horizon"))
            path = self.root / route["artifact"]
            artifact = joblib.load(path)
            if list(artifact.get("feature_names", [])) != list(json.loads((path.parent / "metadata.json").read_text(encoding="utf-8"))["feature_names"]):
                raise ValueError(f"Feature schema mismatch in {path}")
            self._artifacts[key] = artifact

    @staticmethod
    def _positive_probability(model: Any, features: pd.DataFrame) -> float:
        classes = list(getattr(model, "classes_", []))
        if 1 not in classes:
            raise ValueError(f"V2 estimator does not expose positive class 1: {classes}")
        value = float(model.predict_proba(features)[:, classes.index(1)][0])
        if not np.isfinite(value):
            raise ValueError("V2 estimator returned a non-finite probability")
        return float(np.clip(value, 0.0, 1.0))

    @staticmethod
    def _prepare(observation: Mapping[str, Any], feature_names: list[str]) -> tuple[pd.DataFrame | None, list[str]]:
        obs = dict(observation)
        missing: list[str] = []
        if obs.get("District") in DISTRICT_ORDER:
            obs["District_Encoded"] = DISTRICT_ORDER.index(str(obs["District"]))
        if obs.get("zone_id") in ZONE_ORDER:
            obs["Zone_Encoded"] = ZONE_ORDER.index(str(obs["zone_id"]))
        elif obs.get("Zone") in ZONE_ORDER:
            obs["Zone_Encoded"] = ZONE_ORDER.index(str(obs["Zone"]))
        elif obs.get("District") in DISTRICT_ZONE_MAP:
            obs["Zone_Encoded"] = ZONE_ORDER.index(DISTRICT_ZONE_MAP[str(obs["District"])])

        if "Date" in obs:
            dt = pd.to_datetime(obs["Date"])
            doy = int(dt.dayofyear)
            obs.setdefault("day_of_year", doy)
            obs.setdefault("doy_sin", float(np.sin(2 * np.pi * doy / 365.25)))
            obs.setdefault("doy_cos", float(np.cos(2 * np.pi * doy / 365.25)))
        if obs.get("Tmax_C") is not None and obs.get("Tmin_C") is not None:
            obs.setdefault("dtr_c", max(0.5, float(obs["Tmax_C"]) - float(obs["Tmin_C"])))
        if obs.get("vpd_kpa") is None and obs.get("Tmax_C") is not None and obs.get("Tmin_C") is not None and obs.get("Relative_Humidity_pct") is not None:
            mean_temp = (float(obs["Tmax_C"]) + float(obs["Tmin_C"])) / 2.0
            saturation = 0.61078 * np.exp((17.27 * mean_temp) / (mean_temp + 237.3))
            obs["vpd_kpa"] = max(0.0, saturation * (1.0 - float(obs["Relative_Humidity_pct"]) / 100.0))
        if obs.get("MJO_Phase") is not None:
            phase = int(obs["MJO_Phase"])
            obs.setdefault("mjo_phase_sin", float(np.sin(2 * np.pi * phase / 8.0)))
            obs.setdefault("mjo_phase_cos", float(np.cos(2 * np.pi * phase / 8.0)))
        if obs.get("iod_dmi") is not None:
            iod = float(obs["iod_dmi"])
            obs.setdefault("iod_positive_flag", int(iod > 0.4))
            obs.setdefault("iod_negative_flag", int(iod < -0.4))
            obs.setdefault("iod_dmi_lag7", iod)
            obs.setdefault("iod_dmi_lag14", iod)

        for name in feature_names:
            value = obs.get(name)
            if value is None or not np.isfinite(float(value)):
                missing.append(name)
        if missing:
            return None, missing
        return pd.DataFrame([{name: obs[name] for name in feature_names}], columns=feature_names), []

    @staticmethod
    def _baseline_probability(artifact: Mapping[str, Any], observation: Mapping[str, Any]) -> float | None:
        district = observation.get("District")
        month = pd.to_datetime(observation.get("Date")).month
        district_rates = artifact.get("baseline_district_month_rates", {})
        month_rates = artifact.get("baseline_month_rates", {})
        value = district_rates.get(f"{district}|{month}", month_rates.get(str(month), artifact.get("baseline_global_rate")))
        return None if value is None or not np.isfinite(float(value)) else float(np.clip(value, 0.0, 1.0))

    def _event(self, event: str, observation: Mapping[str, Any]) -> dict[str, Any]:
        date = pd.to_datetime(observation.get("Date"))
        artifact = self._artifacts[(event, None)]
        applicable = date.month in CORE_MONTHS[event]
        if not applicable:
            return {"probability": None, "probability_pct": None, "applicability": "OUT_OF_SEASON", "model_status": artifact["release_status"]}
        features, missing = self._prepare(observation, artifact["feature_names"])
        if artifact["release_status"] == "BASELINE_PREFERRED":
            probability = self._baseline_probability(artifact, observation)
            if probability is not None:
                return {"probability": round(probability, 6), "probability_pct": round(probability * 100.0, 4), "applicability": "BASELINE_PREFERRED", "model_status": "BASELINE_PREFERRED", "missing_features": []}
        if features is None:
            return {"probability": None, "probability_pct": None, "applicability": "UNAVAILABLE", "model_status": artifact["release_status"], "missing_features": missing}
        raw = self._positive_probability(artifact["model"], features)
        probability = float(np.clip(artifact["calibrator"].predict([raw])[0], 0.0, 1.0))
        return {"probability": round(probability, 6), "probability_pct": round(probability * 100.0, 4), "raw_probability": round(raw, 6), "applicability": "APPLICABLE", "model_status": artifact["release_status"], "missing_features": []}

    def _horizon_event(self, event: str, horizon: str, observation: Mapping[str, Any]) -> dict[str, Any]:
        artifact = self._artifacts[(event, horizon)]
        date = pd.to_datetime(observation.get("Date"))
        applicable = date.month in HORIZON_MONTHS[event]
        if not applicable:
            status = "OUT_OF_SEASON"
        else:
            features, missing = self._prepare(observation, artifact["feature_names"])
            if artifact["release_status"] == "BASELINE_PREFERRED":
                probability = self._baseline_probability(artifact, observation)
                if probability is not None:
                    return {"probability": round(probability, 6), "probability_pct": round(probability * 100.0, 4), "applicability": "BASELINE_PREFERRED", "model_status": "BASELINE_PREFERRED", "missing_features": []}
            if features is None:
                status = "UNAVAILABLE"
            else:
                raw = self._positive_probability(artifact["model"], features)
                probability = float(np.clip(artifact["calibrator"].predict([raw])[0], 0.0, 1.0))
                return {"probability": round(probability, 6), "probability_pct": round(probability * 100.0, 4), "raw_probability": round(raw, 6), "applicability": "APPLICABLE", "model_status": artifact["release_status"], "missing_features": []}
        return {"probability": None, "probability_pct": None, "applicability": status, "model_status": artifact["release_status"], "missing_features": missing if status == "UNAVAILABLE" else []}

    def predict(self, observation: Mapping[str, Any]) -> dict[str, Any]:
        if not observation.get("Date"):
            raise ValueError("V2 inference requires Date")
        events = {event: self._event(event, observation) for event in CORE_EVENTS}
        horizons = {window: {event: self._horizon_event(event, window, observation) for event in HORIZON_EVENTS} for window in HORIZONS}
        return {
            "engine_version": self.manifest["model_version"],
            "reference_date": str(pd.to_datetime(observation["Date"]).date()),
            "operational_status": "EXPERIMENTAL_OBSERVATION_STATE",
            "events": events,
            "statistical_7_30_day_outlook": {
                "forecast_status": "STATISTICAL_7_30_DAY_OUTLOOK",
                "disclaimer": HORIZON_DISCLAIMER,
                "horizons": horizons,
            },
        }
