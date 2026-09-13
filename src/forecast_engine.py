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

STATUS:
  The original event heads remain in EXPERIMENTAL_OBSERVATION_STATE.
  The additional 7-30 day heads are STATISTICAL_7_30_DAY_OUTLOOK models,
  not NWP or subseasonal dynamical forecasts.
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
ATMOSPHERIC_MODELS_DIR = "models/atmospheric_enhanced"
HORIZON_MODELS_DIR = "models/horizon_7_30d"
ENGINE_VERSION = "VARSHASENTINEL_FORECAST_ENGINE_v1.2"
HORIZON_OUTLOOK_STATUS = "STATISTICAL_7_30_DAY_OUTLOOK"
HORIZON_OUTLOOK_DISCLAIMER = (
    "This is a statistical probabilistic outlook based on the observation and climate state "
    "available on the reference date. It is not an NWP or S2S forecast and does not claim "
    "operational 7-30 day dynamical forecasting."
)
HORIZON_EVENT_APPLICABILITY_MONTHS = {
    "dry_spell": frozenset({6, 7, 8, 9, 10}),
    "severe_break": frozenset({6, 7, 8, 9, 10}),
    "heavy_rain": frozenset(range(1, 13)),
    "revival": frozenset({6, 7, 8, 9, 10}),
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


class ForecastEngine:
    """
    Calibrated probabilistic inference engine for the 6 core VARSHASENTINEL monsoon events.
    Loads models without modification and enforces strict schema alignment per head.
    """

    def __init__(
        self,
        baseline_dir: str = BASELINE_MODELS_DIR,
        iod_dir: str = IOD_MODELS_DIR,
        atmospheric_dir: str = ATMOSPHERIC_MODELS_DIR,
        horizon_dir: str = HORIZON_MODELS_DIR
    ):
        self.baseline_dir = baseline_dir
        self.iod_dir = iod_dir
        self.atmospheric_dir = atmospheric_dir
        self.horizon_dir = horizon_dir
        self.models: Dict[str, Any] = {}
        self.model_metadata: Dict[str, Dict[str, Any]] = {}
        self.horizon_models: Dict[str, Any] = {}
        self.horizon_model_metadata: Dict[str, Dict[str, Any]] = {}
        self.baseline_feature_metadata: Optional[Dict[str, Any]] = None
        self.iod_feature_metadata: Optional[Dict[str, Any]] = None
        self.atmospheric_feature_metadata: Optional[Dict[str, Any]] = None
        self.horizon_feature_metadata: Optional[Dict[str, Any]] = None

        self._load_feature_schemas()
        self._load_benchmark_models()
        self._load_horizon_models()

    def _load_feature_schemas(self):
        """Loads and parses feature metadata for baseline, IOD, atmospheric, and horizon models."""
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

        atmos_meta_path = os.path.join(self.atmospheric_dir, "feature_metadata.json")
        if not os.path.exists(atmos_meta_path):
            raise FileNotFoundError(f"Atmospheric feature metadata not found at: {atmos_meta_path}")
        with open(atmos_meta_path, "r", encoding="utf-8") as f:
            self.atmospheric_feature_metadata = json.load(f)

        logger.info(
            f"Loaded baseline schema ({len(self.baseline_feature_metadata['feature_names'])} features), "
            f"IOD schema ({len(self.iod_feature_metadata['feature_names'])} features), and "
            f"atmospheric schema ({len(self.atmospheric_feature_metadata['feature_names'])} features)."
        )

        horizon_meta_path = os.path.join(self.horizon_dir, "feature_metadata.json")
        if not os.path.exists(horizon_meta_path):
            raise FileNotFoundError(f"Horizon feature metadata not found at: {horizon_meta_path}")
        with open(horizon_meta_path, "r", encoding="utf-8") as f:
            self.horizon_feature_metadata = json.load(f)

        logger.info(
            "Loaded horizon schema (%d features) from %s",
            len(self.horizon_feature_metadata["feature_names"]),
            horizon_meta_path,
        )

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
                "source_dir": self.atmospheric_dir,
                "version": "atmospheric_enhanced",
                "schema": "atmospheric"
            },
            "revival": {
                "target_col": "target_revival_7d",
                "description": "Dry Spell Revival (7-Day Lead)",
                "source_dir": self.atmospheric_dir,
                "version": "atmospheric_enhanced",
                "schema": "atmospheric"
            },
            "heavy_rain": {
                "target_col": "target_heavy_rain_7d",
                "description": "Heavy Rainfall / Flood Hazard (7-Day Lead)",
                "source_dir": self.atmospheric_dir,
                "version": "atmospheric_enhanced",
                "schema": "atmospheric"
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
            # IOD and Atmospheric models are stored directly as the calibrated estimator
            if isinstance(loaded_obj, dict) and "model" in loaded_obj:
                estimator = loaded_obj["model"]
            else:
                estimator = loaded_obj

            feat_count = 40 if cfg["schema"] == "atmospheric" else (31 if cfg["schema"] == "iod" else 26)
            self.models[head_key] = estimator
            self.model_metadata[head_key] = {
                "head_key": head_key,
                "description": cfg["description"],
                "target_col": cfg["target_col"],
                "model_version": cfg["version"],
                "model_path": path,
                "schema_type": cfg["schema"],
                "feature_count": feat_count
            }
            logger.info(f"Loaded head '{head_key}' [{cfg['version']}] from {path}")

    def _load_horizon_models(self):
        """Load the 12 calibrated statistical outlook heads without altering old heads."""
        target_columns = self.horizon_feature_metadata.get("target_columns", [])
        expected_targets = [
            f"target_{event}_{window}"
            for event in ("dry_spell", "severe_break", "heavy_rain", "revival")
            for window in ("7_14d", "15_21d", "22_30d")
        ]
        if target_columns != expected_targets:
            raise ValueError(
                "Horizon target metadata does not match the required event/window ordering: "
                f"expected {expected_targets}, got {target_columns}"
            )

        feature_names = self.horizon_feature_metadata["feature_names"]
        for target_col in expected_targets:
            filename = f"{target_col}_calibrated_xgb.joblib"
            path = os.path.join(self.horizon_dir, filename)
            if not os.path.exists(path):
                raise FileNotFoundError(f"Calibrated horizon model not found for {target_col} at: {path}")

            loaded_obj = joblib.load(path)
            if not isinstance(loaded_obj, dict) or "model" not in loaded_obj:
                raise ValueError(f"Invalid calibrated horizon artifact for {target_col}: {path}")
            estimator = loaded_obj["model"]
            artifact_features = loaded_obj.get("feature_cols", feature_names)
            if not all(col in feature_names for col in artifact_features):
                raise ValueError(
                    f"Feature ordering mismatch for {target_col}: artifact metadata contains unrecognized features"
                )

            target_without_prefix = target_col.removeprefix("target_")
            window = next(
                (candidate for candidate in ("7_14d", "15_21d", "22_30d")
                 if target_without_prefix.endswith(f"_{candidate}")),
                None,
            )
            if window is None:
                raise ValueError(f"Unrecognized horizon label in target column: {target_col}")
            event = target_without_prefix[:-(len(window) + 1)]
            self.horizon_models[target_col] = estimator
            self.horizon_model_metadata[target_col] = {
                "target_col": target_col,
                "event": event,
                "horizon": window,
                "model_version": "horizon_7_30d_calibrated_platt_sigmoid",
                "model_path": path,
                "artifact_calibration_method": loaded_obj.get("calibration_method", "platt_sigmoid"),
                "feature_cols": artifact_features,
                "feature_count": len(artifact_features),
            }
            logger.info("Loaded horizon head '%s' (%d features) from %s", target_col, len(artifact_features), path)

    def prepare_feature_vectors(self, observation: Dict[str, Any], return_atmospheric: bool = False):
        """
        Validates the incoming observation, computes any derived variables if missing,
        and constructs the exact feature matrices required by baseline, IOD, and atmospheric models.
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

        # 6. Regional Atmospheric Circulation Variables
        u850 = obs.get("u850_regional", 1.5528)
        v850 = obs.get("v850_regional", 0.0833)
        obs.setdefault("u850_regional", float(u850))
        obs.setdefault("v850_regional", float(v850))
        if "wind850_speed" not in obs:
            obs["wind850_speed"] = float(np.sqrt(obs["u850_regional"]**2 + obs["v850_regional"]**2))
        obs.setdefault("mslp_regional", float(obs.get("mslp_regional", 1009.545)))
        obs.setdefault("regional_slp_gradient", float(obs.get("regional_slp_gradient", 3.61)))
        obs.setdefault("u850_lag7", float(obs.get("u850_lag7", obs["u850_regional"])))
        obs.setdefault("mslp_lag7", float(obs.get("mslp_lag7", obs["mslp_regional"])))
        obs.setdefault("u850_rolling_7d", float(obs.get("u850_rolling_7d", obs["u850_regional"])))
        obs.setdefault("mslp_rolling_7d", float(obs.get("mslp_rolling_7d", obs["mslp_regional"])))

        # 7. Verify and construct Baseline feature vector (26 cols)
        baseline_cols = self.baseline_feature_metadata["feature_names"]
        missing_base = [col for col in baseline_cols if col not in obs or obs[col] is None]
        if missing_base:
            raise ValueError(f"Observation missing mandatory baseline features: {missing_base}")

        df_base = pd.DataFrame([{col: obs[col] for col in baseline_cols}])[baseline_cols]

        # 8. Verify and construct IOD feature vector (31 cols)
        iod_cols = self.iod_feature_metadata["feature_names"]
        missing_iod = [col for col in iod_cols if col not in obs or obs[col] is None]
        if missing_iod:
            raise ValueError(f"Observation missing mandatory IOD features for IOD-enhanced heads: {missing_iod}")

        df_iod = pd.DataFrame([{col: obs[col] for col in iod_cols}])[iod_cols]

        # 9. Verify and construct Atmospheric feature vector (40 cols)
        atmos_cols = self.atmospheric_feature_metadata["feature_names"]
        missing_atmos = [col for col in atmos_cols if col not in obs or obs[col] is None]
        if missing_atmos:
            raise ValueError(f"Observation missing mandatory atmospheric features: {missing_atmos}")

        df_atmos = pd.DataFrame([{col: obs[col] for col in atmos_cols}])[atmos_cols]

        if return_atmospheric:
            return df_base, df_iod, df_atmos
        return df_base, df_iod

    def prepare_atmospheric_feature_vector(self, observation: Dict[str, Any]) -> pd.DataFrame:
        """Build the exact 40-column atmospheric matrix in artifact metadata order."""
        _, _, df_atmos = self.prepare_feature_vectors(observation, return_atmospheric=True)
        return df_atmos

    def prepare_horizon_feature_vector(self, observation: Dict[str, Any]) -> pd.DataFrame:
        """Build the exact 38-column horizon matrix in artifact metadata order."""
        _, _, df_atmos = self.prepare_feature_vectors(observation, return_atmospheric=True)
        horizon_cols = self.horizon_feature_metadata["feature_names"]
        missing_horizon = [col for col in horizon_cols if col not in df_atmos.columns]
        if missing_horizon:
            raise ValueError(f"Observation missing mandatory horizon features: {missing_horizon}")
        horizon_df = df_atmos.loc[:, horizon_cols].copy()
        if list(horizon_df.columns) != horizon_cols:
            raise ValueError("Horizon feature ordering does not match feature metadata")
        return horizon_df

    def _predict_horizon_outlook(self, horizon_features: pd.DataFrame, reference_date: Any) -> Dict[str, Any]:
        """Predict all new heads and return the explicitly labelled outlook section."""
        month = pd.to_datetime(reference_date).month
        horizons: Dict[str, Dict[str, Any]] = {
            "7_14d": {}, "15_21d": {}, "22_30d": {}
        }
        event_order = ("dry_spell", "severe_break", "heavy_rain", "revival")
        for target_col, model in self.horizon_models.items():
            meta = self.horizon_model_metadata[target_col]
            horizon = meta["horizon"]
            event = meta["event"]
            applicable = month in HORIZON_EVENT_APPLICABILITY_MONTHS[event]
            probability = None
            if applicable:
                feat_cols = meta.get("feature_cols", list(horizon_features.columns))
                X_model = horizon_features[feat_cols]
                probability_raw = float(model.predict_proba(X_model)[0, 1])
                probability = round(max(0.0, min(1.0, probability_raw)), 4)
            horizons[horizon][f"{event}_probability"] = probability
            horizons[horizon][f"{event}_applicability"] = (
                "APPLICABLE" if applicable else "OUT_OF_SEASON"
            )
            horizons[horizon].setdefault("model_versions", {})[event] = {
                "target_col": target_col,
                "model_version": meta["model_version"],
                "artifact_path": meta["model_path"],
                "calibration_method": meta["artifact_calibration_method"],
                "features_evaluated": meta["feature_count"],
            }

        for horizon, values in horizons.items():
            missing_events = [
                field for event in event_order
                for field in (f"{event}_probability", f"{event}_applicability")
                if field not in values
            ]
            if missing_events:
                raise RuntimeError(f"Horizon {horizon} is missing predictions: {missing_events}")
        return {
            "forecast_status": HORIZON_OUTLOOK_STATUS,
            "disclaimer": HORIZON_OUTLOOK_DISCLAIMER,
            "horizons": horizons,
        }

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

        df_base, df_iod, df_atmos = self.prepare_feature_vectors(obs_dict, return_atmospheric=True)

        results_by_head = {}
        summary_probs = {}
        summary_pcts = {}

        for head_key, model in self.models.items():
            meta = self.model_metadata[head_key]
            # Select schema-aligned vector
            if meta["schema_type"] == "atmospheric":
                X = df_atmos
            elif meta["schema_type"] == "iod":
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

        if "Date" not in obs_dict:
            raise ValueError("Observation must provide 'Date' for horizon applicability")
        horizon_outlook = self._predict_horizon_outlook(
            self.prepare_horizon_feature_vector(obs_dict), obs_dict["Date"]
        )

        return {
            "engine_version": ENGINE_VERSION,
            "operational_status": "EXPERIMENTAL_OBSERVATION_STATE",
            "disclaimer": (
                "This engine operates from the available observation/feature state. "
                "It is not yet an operational 7-30 day dynamical forecast."
            ),
            "forecast_sections": {
                "existing_short_horizon_event_forecasts": {
                    "forecast_status": "EXPERIMENTAL_OBSERVATION_STATE",
                    "description": "Existing six calibrated event heads.",
                },
                "statistical_7_30_day_outlook": {
                    "forecast_status": HORIZON_OUTLOOK_STATUS,
                    "description": "Statistical probabilistic outlook; not NWP/S2S.",
                },
            },
            "summary_probabilities": summary_probs,
            "summary_percentages": summary_pcts,
            "head_details": results_by_head,
            "statistical_7_30_day_outlook": horizon_outlook,
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
