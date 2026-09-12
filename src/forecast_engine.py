"""
VARSHASENTINEL (SIH26086) - Probabilistic Monsoon Forecast Engine
==================================================================
Modular prediction engine serving calibrated probabilistic forecasts for six
core monsoon phenomena in West Bengal.

Model Selection (Ensemble Best-of-Breed based on out-of-sample 2025 benchmark):
  - Monsoon Onset (14-Day Window)       -> models/iod_enhanced/ (PR-AUC +0.0232, Brier -0.0062)
  - False Onset Surge Failure           -> models/iod_enhanced/ (ROC-AUC +0.0116, Brier -0.0018)
  - Dry Spell Revival (7-Day Lead)      -> models/iod_enhanced/ (Brier -0.0055, ROC-AUC +0.0046)
  - Heavy Rainfall Hazard (7-Day Lead)  -> models/iod_enhanced/ (Brier -0.0035, Precision +0.0363)
  - 5-Day Dry Spell / Break             -> models/ (baseline, avoids validation-fold overfitting)
  - 7-Day Severe Break (21-Day Lead)    -> models/ (baseline, sharper Brier calibration)

DISCLAIMER:
  This engine currently operates from the available observation / feature state.
  It is not yet an operational 7-30 day dynamical forecast.
"""

import os
import json
import logging
from typing import Dict, Any, Union, Optional
import numpy as np
import pandas as pd
import joblib

logger = logging.getLogger("varshasentinel.forecast_engine")

BASELINE_MODELS_DIR = "models"
IOD_MODELS_DIR = "models/iod_enhanced"
ENGINE_VERSION = "VARSHASENTINEL_FORECAST_ENGINE_v1.1"

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


class ForecastEngine:
    """
    Calibrated probabilistic inference engine for the 6 core VARSHASENTINEL monsoon events.
    Loads models without modification and enforces strict schema alignment per head.
    """

    def __init__(
        self,
        baseline_dir: str = BASELINE_MODELS_DIR,
        iod_dir: str = IOD_MODELS_DIR
    ):
        self.baseline_dir = baseline_dir
        self.iod_dir = iod_dir
        self.models: Dict[str, Any] = {}
        self.model_metadata: Dict[str, Dict[str, Any]] = {}
        self.baseline_feature_metadata: Optional[Dict[str, Any]] = None
        self.iod_feature_metadata: Optional[Dict[str, Any]] = None

        self._load_feature_schemas()
        self._load_benchmark_models()

    def _load_feature_schemas(self):
        """Loads and parses feature metadata for baseline and IOD models."""
        base_meta_path = os.path.join(self.baseline_dir, "feature_metadata.json")
        if not os.path.exists(base_meta_path):
            raise FileNotFoundError(f"Baseline feature metadata not found at: {base_meta_path}")
        with open(base_meta_path, "r", encoding="utf-8") as f:
            self.baseline_feature_metadata = json.load(f)

        iod_meta_path = os.path.join(self.iod_dir, "feature_metadata.json")
        if not os.path.exists(iod_meta_path):
            raise FileNotFoundError(f"IOD feature metadata not found at: {iod_meta_path}")
        with open(iod_meta_path, "r", encoding="utf-8") as f:
            self.iod_feature_metadata = json.load(f)

        logger.info(f"Loaded baseline schema ({len(self.baseline_feature_metadata['feature_names'])} features) and IOD schema ({len(self.iod_feature_metadata['feature_names'])} features).")

    def _load_benchmark_models(self):
        """Loads the six models selected by the out-of-sample 2025 benchmark."""
        head_configs = {
            "onset": {
                "target_col": "target_onset_window_14d",
                "description": "Monsoon Onset (14-Day Window)",
                "source_dir": self.iod_dir,
                "version": "iod_enhanced",
                "schema": "iod"
            },
            "false_onset": {
                "target_col": "target_false_onset_flag",
                "description": "False Onset Surge Failure",
                "source_dir": self.iod_dir,
                "version": "iod_enhanced",
                "schema": "iod"
            },
            "revival": {
                "target_col": "target_revival_7d",
                "description": "Dry Spell Revival (7-Day Lead)",
                "source_dir": self.iod_dir,
                "version": "iod_enhanced",
                "schema": "iod"
            },
            "heavy_rain": {
                "target_col": "target_heavy_rain_7d",
                "description": "Heavy Rainfall / Flood Hazard (7-Day Lead)",
                "source_dir": self.iod_dir,
                "version": "iod_enhanced",
                "schema": "iod"
            },
            "dry_spell_5d": {
                "target_col": "target_dry_spell_5d_14d",
                "description": "5-Day Dry Spell / Break (14-Day Lead)",
                "source_dir": self.baseline_dir,
                "version": "baseline_v1",
                "schema": "baseline"
            },
            "severe_break_7d": {
                "target_col": "target_dry_spell_7d_21d",
                "description": "7-Day Severe Break (21-Day Lead)",
                "source_dir": self.baseline_dir,
                "version": "baseline_v1",
                "schema": "baseline"
            }
        }

        for head_key, cfg in head_configs.items():
            filename = f"{cfg['target_col']}_xgb.joblib"
            path = os.path.join(cfg["source_dir"], filename)
            if not os.path.exists(path):
                raise FileNotFoundError(f"Model artifact not found for {head_key} at: {path}")

            loaded_obj = joblib.load(path)
            # Baseline models are stored as a dict with {'model': estimator, ...}
            # IOD models are stored directly as the calibrated estimator
            if isinstance(loaded_obj, dict) and "model" in loaded_obj:
                estimator = loaded_obj["model"]
            else:
                estimator = loaded_obj

            self.models[head_key] = estimator
            self.model_metadata[head_key] = {
                "head_key": head_key,
                "description": cfg["description"],
                "target_col": cfg["target_col"],
                "model_version": cfg["version"],
                "model_path": path,
                "schema_type": cfg["schema"],
                "feature_count": 31 if cfg["schema"] == "iod" else 26
            }
            logger.info(f"Loaded head '{head_key}' [{cfg['version']}] from {path}")

    def prepare_feature_vectors(self, observation: Dict[str, Any]):
        """
        Validates the incoming observation, computes any derived variables if missing,
        and constructs the exact feature matrices required by baseline and IOD models.
        """
        if not isinstance(observation, dict):
            raise TypeError(f"Observation must be a dictionary, got {type(observation)}")

        obs = dict(observation)

        # 1. District and Zone Encoding
        dist_classes = self.baseline_feature_metadata["districts"]
        zone_classes = self.baseline_feature_metadata["zones"]

        district = obs.get("District")
        zone = obs.get("zone_id") or obs.get("Zone")

        if district is not None:
            if district not in dist_classes:
                raise ValueError(f"Unknown District '{district}'. Expected one of: {dist_classes}")
            obs["District_Encoded"] = dist_classes.index(district)
            # Auto-assign coordinates if missing
            if "Latitude" not in obs or "Longitude" not in obs:
                coords = DISTRICT_COORDS.get(district, (23.5, 87.5))
                obs.setdefault("Latitude", coords[0])
                obs.setdefault("Longitude", coords[1])
            # Auto-assign zone if missing
            if zone is None:
                zone = DISTRICT_ZONE_MAP.get(district, "gangetic_alluvial")
        elif "District_Encoded" not in obs:
            raise ValueError("Observation must provide either 'District' or 'District_Encoded'.")

        if zone is not None:
            if zone not in zone_classes:
                raise ValueError(f"Unknown Zone '{zone}'. Expected one of: {zone_classes}")
            obs["Zone_Encoded"] = zone_classes.index(zone)
        elif "Zone_Encoded" not in obs:
            raise ValueError("Observation must provide either 'zone_id' or 'Zone_Encoded'.")

        # 2. Date and DOY encodings
        if "day_of_year" not in obs:
            if "Date" in obs:
                dt = pd.to_datetime(obs["Date"])
                doy = dt.dayofyear
                obs["day_of_year"] = doy
            else:
                raise ValueError("Observation must provide either 'day_of_year' or 'Date'.")
        else:
            doy = int(obs["day_of_year"])

        if "doy_sin" not in obs or "doy_cos" not in obs:
            obs["doy_sin"] = float(np.sin(2 * np.pi * doy / 365.25))
            obs["doy_cos"] = float(np.cos(2 * np.pi * doy / 365.25))

        # 3. Surface Thermodynamic Variables
        tmax = obs.get("Tmax_C")
        tmin = obs.get("Tmin_C")
        rh = obs.get("Relative_Humidity_pct")

        if tmax is None or tmin is None:
            raise ValueError("Observation missing mandatory surface temperature: 'Tmax_C' and 'Tmin_C'.")

        tmax = float(tmax)
        tmin = float(tmin)
        if tmax < tmin:
            tmax, tmin = max(tmax, tmin) + 0.5, min(tmax, tmin)

        if "dtr_c" not in obs:
            obs["dtr_c"] = max(0.5, tmax - tmin)

        if "vpd_kpa" not in obs:
            if rh is None:
                raise ValueError("Observation missing 'Relative_Humidity_pct' required to calculate VPD.")
            rh = float(rh)
            t_mean = (tmax + tmin) / 2.0
            e_sat = 0.61078 * np.exp((17.27 * t_mean) / (t_mean + 237.3))
            e_act = e_sat * (rh / 100.0)
            obs["vpd_kpa"] = max(0.0, e_sat - e_act)

        # 4. MJO Phases
        mjo_phase = obs.get("MJO_Phase")
        if mjo_phase is None:
            raise ValueError("Observation missing mandatory teleconnection variable: 'MJO_Phase'.")
        mjo_phase = int(mjo_phase)
        if "mjo_phase_sin" not in obs or "mjo_phase_cos" not in obs:
            obs["mjo_phase_sin"] = float(np.sin(2 * np.pi * mjo_phase / 8.0))
            obs["mjo_phase_cos"] = float(np.cos(2 * np.pi * mjo_phase / 8.0))

        # 5. IOD Flags
        if "iod_dmi" in obs:
            iod_val = float(obs["iod_dmi"])
            if "iod_positive_flag" not in obs:
                obs["iod_positive_flag"] = int(iod_val > 0.4)
            if "iod_negative_flag" not in obs:
                obs["iod_negative_flag"] = int(iod_val < -0.4)
            if "iod_dmi_lag7" not in obs:
                obs["iod_dmi_lag7"] = iod_val
            if "iod_dmi_lag14" not in obs:
                obs["iod_dmi_lag14"] = iod_val

        # 6. Verify and construct Baseline feature vector (26 cols)
        baseline_cols = self.baseline_feature_metadata["feature_names"]
        missing_base = [col for col in baseline_cols if col not in obs or obs[col] is None]
        if missing_base:
            raise ValueError(f"Observation missing mandatory baseline features: {missing_base}")

        df_base = pd.DataFrame([{col: obs[col] for col in baseline_cols}])[baseline_cols]

        # 7. Verify and construct IOD feature vector (31 cols)
        iod_cols = self.iod_feature_metadata["feature_names"]
        missing_iod = [col for col in iod_cols if col not in obs or obs[col] is None]
        if missing_iod:
            raise ValueError(f"Observation missing mandatory IOD features for IOD-enhanced heads: {missing_iod}")

        df_iod = pd.DataFrame([{col: obs[col] for col in iod_cols}])[iod_cols]

        return df_base, df_iod

    def predict(self, observation: Union[Dict[str, Any], pd.Series]) -> Dict[str, Any]:
        """
        Computes calibrated probability outputs for all six monsoon event heads.
        Returns probabilities (0 to 1) and percentages (0 to 100).
        """
        if isinstance(observation, pd.Series):
            obs_dict = observation.to_dict()
        elif isinstance(observation, dict):
            obs_dict = observation
        else:
            raise TypeError(f"Expected dict or pd.Series, got {type(observation)}")

        df_base, df_iod = self.prepare_feature_vectors(obs_dict)

        results_by_head = {}
        summary_probs = {}
        summary_pcts = {}

        for head_key, model in self.models.items():
            meta = self.model_metadata[head_key]
            # Select schema-aligned vector
            if meta["schema_type"] == "iod":
                X = df_iod
            else:
                X = df_base

            # Predict probability
            prob_raw = float(model.predict_proba(X)[0, 1])
            # Strict safety bounds
            prob = max(0.0, min(1.0, prob_raw))
            prob_pct = round(prob * 100.0, 2)
            prob_clean = round(prob, 4)

            results_by_head[head_key] = {
                "head_key": head_key,
                "description": meta["description"],
                "target_col": meta["target_col"],
                "model_version": meta["model_version"],
                "model_path": meta["model_path"],
                "features_evaluated": meta["feature_count"],
                "probability": prob_clean,
                "probability_pct": prob_pct
            }

            summary_probs[head_key] = prob_clean
            summary_pcts[head_key] = prob_pct

        return {
            "engine_version": ENGINE_VERSION,
            "operational_status": "EXPERIMENTAL_OBSERVATION_STATE",
            "disclaimer": (
                "This engine operates from the available observation/feature state. "
                "It is not yet an operational 7-30 day dynamical forecast."
            ),
            "summary_probabilities": summary_probs,
            "summary_percentages": summary_pcts,
            "head_details": results_by_head
        }


# Module-level singleton
_DEFAULT_ENGINE: Optional[ForecastEngine] = None


def predict_monsoon_events(observation: Union[Dict[str, Any], pd.Series]) -> Dict[str, Any]:
    """
    Primary API entrypoint for VARSHASENTINEL prediction.
    Accepts one observation record and returns calibrated probabilities for all six event heads.
    """
    global _DEFAULT_ENGINE
    if _DEFAULT_ENGINE is None:
        _DEFAULT_ENGINE = ForecastEngine()
    return _DEFAULT_ENGINE.predict(observation)


if __name__ == "__main__":
    import pprint
    engine = ForecastEngine()

    sample_obs = {
        "District": "Purba_Bardhaman",
        "Date": "2025-06-15",
        "Rainfall_Observed_mm": 15.2,
        "Tmax_C": 34.5,
        "Tmin_C": 26.0,
        "Relative_Humidity_pct": 80.0,
        "Solar_Radiation_MJm2": 22.0,
        "MJO_Phase": 5,
        "MJO_Amplitude": 1.5,
        "Nino34_Anomaly": -0.3,
        "Dry_Spell_Days_Streak": 0,
        "Rolling_Rainfall_7d_mm": 48.0,
        "Rolling_Rainfall_30d_mm": 160.0,
        "rolling_rain_3d_mm": 20.0,
        "rolling_rain_15d_mm": 95.0,
        "Drought_Stress_Index": 0.0,
        "Waterlogging_Risk_Index": 0.1,
        "iod_dmi": 0.45,
        "iod_dmi_lag7": 0.38,
        "iod_dmi_lag14": 0.25
    }

    result = engine.predict(sample_obs)
    print("\n--- VARSHASENTINEL Forecast Engine Test Prediction ---")
    pprint.pprint(result)
