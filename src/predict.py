"""
VARSHASENTINEL (SIH26086) - Probabilistic Monsoon Inference Engine
==================================================================
Provides real-time, modular, calibrated probabilistic inference for:
- P(onset)
- P(false onset)
- P(dry spell 5d)
- P(dry spell 7d)
- P(heavy rainfall)
- P(revival)

Modular design allows downstream integration of:
- IOD/DMI and EQUINOO teleconnections
- U850 low-level monsoon wind and MSLP pressure gradients
- Block/panchayat spatial downscaling
- Agro-advisory crop risk engines
- FastAPI / Flask endpoints and Dashboards
"""

import os
import json
import logging
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
import joblib

logger = logging.getLogger("varshasentinel.predict")

MODELS_DIR = "models"
MODEL_FILES = {
    "onset": "target_onset_window_14d_xgb.joblib",
    "false_onset": "target_false_onset_flag_xgb.joblib",
    "dry_spell_5d": "target_dry_spell_5d_14d_xgb.joblib",
    "dry_spell_7d": "target_dry_spell_7d_21d_xgb.joblib",
    "heavy_rain": "target_heavy_rain_7d_xgb.joblib",
    "revival": "target_revival_7d_xgb.joblib"
}

DISTRICT_ZONE_MAP = {
    "Purba_Bardhaman": "gangetic_alluvial",
    "Hooghly": "gangetic_alluvial",
    "Nadia": "gangetic_alluvial",
    "Murshidabad": "gangetic_alluvial",
    "Purulia": "red_laterite",
    "Bankura": "red_laterite",
    "Jhargram": "red_laterite",
    "Birbhum_Suri": "red_laterite",
    "Jalpaiguri": "terai_teesta",
    "Alipurduar": "terai_teesta",
    "Cooch_Behar": "terai_teesta",
    "Siliguri_Foothill": "terai_teesta"
}

DISTRICT_COORDS = {
    "Purba_Bardhaman": (23.25, 87.85),
    "Hooghly": (22.88, 87.78),
    "Nadia": (23.40, 88.50),
    "Murshidabad": (24.10, 88.25),
    "Purulia": (23.33, 86.36),
    "Bankura": (23.23, 87.07),
    "Jhargram": (22.45, 86.98),
    "Birbhum_Suri": (23.91, 87.53),
    "Jalpaiguri": (26.54, 88.72),
    "Alipurduar": (26.49, 89.53),
    "Cooch_Behar": (26.32, 89.45),
    "Siliguri_Foothill": (26.71, 88.43)
}


class VarshaSentinelPredictor:
    def __init__(self, models_dir: str = MODELS_DIR):
        self.models_dir = models_dir
        self.models = {}
        self.metadata = None
        self._load_models()

    def _load_models(self):
        meta_path = os.path.join(self.models_dir, "feature_metadata.json")
        if os.path.exists(meta_path):
            with open(meta_path, "r") as f:
                self.metadata = json.load(f)

        for key, fname in MODEL_FILES.items():
            path = os.path.join(self.models_dir, fname)
            if os.path.exists(path):
                self.models[key] = joblib.load(path)
            else:
                logger.warning(f"Model file {path} not found.")

    def _engineer_features(self, district: str, prediction_date: str, raw_features: Dict[str, Any]) -> pd.DataFrame:
        dt = pd.to_datetime(prediction_date)
        doy = dt.dayofyear

        # Get coordinates
        lat, lon = DISTRICT_COORDS.get(district, (23.5, 87.5))
        zone = DISTRICT_ZONE_MAP.get(district, "gangetic_alluvial")

        # Surface variables
        tmax = float(raw_features.get("Tmax_C", 32.0))
        tmin = float(raw_features.get("Tmin_C", 24.0))
        rf = float(raw_features.get("Rainfall_Observed_mm", 0.0))
        rh = float(raw_features.get("Relative_Humidity_pct", 75.0))
        solar = float(raw_features.get("Solar_Radiation_MJm2", 18.0))

        # Clamping
        if tmax < tmin:
            tmax, tmin = max(tmax, tmin) + 0.5, min(tmax, tmin)
        dtr = max(0.5, tmax - tmin)

        # VPD
        t_mean = (tmax + tmin) / 2.0
        e_sat = 0.61078 * np.exp((17.27 * t_mean) / (t_mean + 237.3))
        e_act = e_sat * (rh / 100.0)
        vpd = max(0.0, e_sat - e_act)

        # Encodings
        doy_sin = np.sin(2 * np.pi * doy / 365.25)
        doy_cos = np.cos(2 * np.pi * doy / 365.25)

        mjo_phase = int(raw_features.get("MJO_Phase", 4))
        mjo_amp = float(raw_features.get("MJO_Amplitude", 1.0))
        mjo_sin = np.sin(2 * np.pi * mjo_phase / 8.0)
        mjo_cos = np.cos(2 * np.pi * mjo_phase / 8.0)

        nino34 = float(raw_features.get("Nino34_Anomaly", 0.0))
        dry_streak = int(raw_features.get("Dry_Spell_Days_Streak", 0 if rf >= 2.5 else 1))

        roll_3d = float(raw_features.get("rolling_rain_3d_mm", rf))
        roll_7d = float(raw_features.get("Rolling_Rainfall_7d_mm", rf))
        roll_15d = float(raw_features.get("rolling_rain_15d_mm", rf))
        roll_30d = float(raw_features.get("Rolling_Rainfall_30d_mm", rf))

        drought_idx = float(raw_features.get("Drought_Stress_Index", 0.0 if zone != "red_laterite" else 0.5))
        waterlog_idx = float(raw_features.get("Waterlogging_Risk_Index", 0.0 if zone != "terai_teesta" else 0.3))

        # Categorical indices from metadata
        dist_list = self.metadata.get("districts", list(DISTRICT_COORDS.keys())) if self.metadata else list(DISTRICT_COORDS.keys())
        zone_list = self.metadata.get("zones", ["gangetic_alluvial", "red_laterite", "terai_teesta"]) if self.metadata else ["gangetic_alluvial", "red_laterite", "terai_teesta"]

        dist_enc = dist_list.index(district) if district in dist_list else 0
        zone_enc = zone_list.index(zone) if zone in zone_list else 0

        # Construct vector aligned with feature_metadata.json
        row = {
            "Latitude": lat,
            "Longitude": lon,
            "Rainfall_Observed_mm": rf,
            "Tmax_C": tmax,
            "Tmin_C": tmin,
            "Relative_Humidity_pct": rh,
            "Solar_Radiation_MJm2": solar,
            "MJO_Phase": mjo_phase,
            "MJO_Amplitude": mjo_amp,
            "Nino34_Anomaly": nino34,
            "Dry_Spell_Days_Streak": dry_streak,
            "Rolling_Rainfall_7d_mm": roll_7d,
            "Rolling_Rainfall_30d_mm": roll_30d,
            "Drought_Stress_Index": drought_idx,
            "Waterlogging_Risk_Index": waterlog_idx,
            "dtr_c": dtr,
            "vpd_kpa": vpd,
            "day_of_year": doy,
            "doy_sin": doy_sin,
            "doy_cos": doy_cos,
            "mjo_phase_sin": mjo_sin,
            "mjo_phase_cos": mjo_cos,
            "rolling_rain_3d_mm": roll_3d,
            "rolling_rain_15d_mm": roll_15d,
            "District_Encoded": dist_enc,
            "Zone_Encoded": zone_enc
        }

        feature_df = pd.DataFrame([row])
        # Ensure column order
        if self.metadata and "feature_names" in self.metadata:
            cols = self.metadata["feature_names"]
            feature_df = feature_df[cols]

        return feature_df

    def predict(self, district: str, prediction_date: str, weather_features: Dict[str, Any]) -> Dict[str, float]:
        """
        Computes calibrated probability outputs for the 6 core monsoon events.
        """
        X = self._engineer_features(district, prediction_date, weather_features)
        predictions = {}

        for key, model_info in self.models.items():
            model = model_info["model"]
            try:
                prob = float(model.predict_proba(X)[0, 1])
                prob = round(prob, 4)
            except Exception as e:
                logger.error(f"Error predicting {key}: {e}")
                prob = 0.0

            if key == "onset":
                predictions["onset_probability"] = prob
            elif key == "false_onset":
                predictions["false_onset_probability"] = prob
            elif key == "dry_spell_5d":
                predictions["dry_spell_5d_probability"] = prob
            elif key == "dry_spell_7d":
                predictions["dry_spell_7d_probability"] = prob
            elif key == "heavy_rain":
                predictions["heavy_rain_probability"] = prob
            elif key == "revival":
                predictions["revival_probability"] = prob

        return predictions


# Top-level standalone function required by specification
_GLOBAL_PREDICTOR: Optional[VarshaSentinelPredictor] = None


def predict_monsoon_events(district: str, prediction_date: str, weather_features: Dict[str, Any]) -> Dict[str, float]:
    """
    Standard entrypoint for VARSHASENTINEL prediction.
    Accepts:
      - district (str): e.g. "Purba_Bardhaman", "Purulia", "Jalpaiguri"
      - prediction_date (str): "YYYY-MM-DD"
      - weather_features (dict): Current surface and teleconnection variables
    Returns:
      dict with calibrated event probabilities.
    """
    global _GLOBAL_PREDICTOR
    if _GLOBAL_PREDICTOR is None:
        _GLOBAL_PREDICTOR = VarshaSentinelPredictor()
    return _GLOBAL_PREDICTOR.predict(district, prediction_date, weather_features)


if __name__ == "__main__":
    import pprint
    predictor = VarshaSentinelPredictor()
    sample_weather = {
        "Rainfall_Observed_mm": 12.5,
        "Tmax_C": 33.4,
        "Tmin_C": 26.2,
        "Relative_Humidity_pct": 82.0,
        "Solar_Radiation_MJm2": 21.0,
        "MJO_Phase": 5,
        "MJO_Amplitude": 1.4,
        "Nino34_Anomaly": -0.4,
        "Dry_Spell_Days_Streak": 0,
        "Rolling_Rainfall_7d_mm": 45.0,
        "Rolling_Rainfall_30d_mm": 180.0
    }
    res = predictor.predict("Purba_Bardhaman", "2025-06-12", sample_weather)
    print("Test Sample Prediction Output:")
    pprint.pprint(res)
