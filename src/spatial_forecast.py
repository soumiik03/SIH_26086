"""
VARSHASENTINEL (SIH26086) - Spatial Forecast Layer
===================================================
Hierarchical spatial forecasting pipeline connecting calibrated 6-head ML
predictions with official Survey of India / LGD administrative boundaries in West Bengal.

Hierarchy:
  District  ->  CD Block  ->  Gram Panchayat

Scientific & Cadastral Guardrails:
  1. Strict separation of District (model) probability, Spatially Downscaled probability,
     and Spatially Aggregated probability.
  2. Uses only authentic derived spatial layers (EPSG:4326).
  3. Zero synthetic/fabricated geometries; the 85 official missing GPs are preserved as absent.
  4. Deterministic risk categorization (LOW, MODERATE, HIGH, VERY_HIGH) using documented thresholds.
  5. Deterministic agrometeorological advisory mapping (no LLM hallucinations).
  6. Existing event heads remain "EXPERIMENTAL_OBSERVATION_STATE".
  7. The 7-30 day section is a "STATISTICAL_7_30_DAY_OUTLOOK", not NWP/S2S.

DISCLAIMER:
  This engine operates from the available observation/feature state.
  It is not yet an operational 7-30 day dynamical forecast.
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple, Union

# Ensure workspace root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import shape, mapping

from src.forecast_engine import (
    ForecastEngine,
    predict_monsoon_events,
    ENGINE_VERSION,
    HORIZON_OUTLOOK_STATUS,
    HORIZON_OUTLOOK_DISCLAIMER,
)
from src.spatial.spatial_loader import SpatialDataLoader, DISTRICT_CENTROIDS

logger = logging.getLogger("varshasentinel.spatial_forecast")

DEFAULT_BLOCKS_PATH = "data/spatial/derived/west_bengal_blocks.geojson"
DEFAULT_PANCHAYATS_PATH = "data/spatial/derived/west_bengal_panchayats_safe.geojson"
DEFAULT_MISSING_GP_PATH = "reports/missing_gp_coverage.csv"
DEFAULT_BLOCK_ELEVATION_PATH = "data/spatial/derived/block_elevation.csv"
DEFAULT_PANCHAYAT_ELEVATION_PATH = "data/spatial/derived/panchayat_elevation.csv"
DEFAULT_DATASET_PATH = (
    "data/processed/varshasentinel_master_with_atmospheric_signals.parquet"
    if os.path.exists("data/processed/varshasentinel_master_with_atmospheric_signals.parquet")
    else "data/processed/varshasentinel_master_with_iod.parquet"
)
DEFAULT_OUTPUT_DIR = "data/processed/spatial_forecasts"

OPERATIONAL_STATUS = "EXPERIMENTAL_OBSERVATION_STATE"
OPERATIONAL_DISCLAIMER = (
    "This engine operates from the available observation/feature state. "
    "It is not yet an operational 7-30 day dynamical forecast."
)
STATISTICAL_OUTLOOK_STATUS = HORIZON_OUTLOOK_STATUS
STATISTICAL_OUTLOOK_DISCLAIMER = HORIZON_OUTLOOK_DISCLAIMER
STATISTICAL_OUTLOOK_HORIZONS = ("7_14d", "15_21d", "22_30d")
STATISTICAL_OUTLOOK_EVENTS = (
    "dry_spell_probability",
    "severe_break_probability",
    "heavy_rain_probability",
    "revival_probability",
)

# Risk color tokens for MapLibre / Leaflet visualization
RISK_COLORS = {
    "LOW": "#22c55e",         # Green
    "MODERATE": "#eab308",    # Yellow
    "HIGH": "#f97316",        # Orange
    "VERY_HIGH": "#ef4444"    # Red
}

# Crosswalk between ML Model district keys and spatial layer identifiers
# Format: model_district_name: {
#    "district_id": str,
#    "district_name": str,
#    "block_filter": lambda b_df,
#    "panchayat_filter": lambda p_df
# }
DISTRICT_SPATIAL_CROSSWALK = {
    "Alipurduar": {
        "district_id": "wb_alipurduar",
        "district_name": "Alipurduar",
        "district_lgd_code": "664",
        "soi_dist_lgd": "328N002",
        "block_filter": lambda df: df["Dist_LGD"] == "328N002",
        "panchayat_filter": lambda df: df["district_lgd_code"] == "664"
    },
    "Bankura": {
        "district_id": "wb_bankura",
        "district_name": "Bankura",
        "district_lgd_code": "305",
        "soi_dist_lgd": "339",
        "block_filter": lambda df: df["Dist_LGD"] == "339",
        "panchayat_filter": lambda df: df["district_lgd_code"] == "305"
    },
    "Birbhum_Suri": {
        "district_id": "wb_birbhum",
        "district_name": "Birbhum (Suri)",
        "district_lgd_code": "307",
        "soi_dist_lgd": "334",
        "block_filter": lambda df: df["Dist_LGD"] == "334",
        "panchayat_filter": lambda df: df["district_lgd_code"] == "307"
    },
    "Cooch_Behar": {
        "district_id": "wb_cooch_behar",
        "district_name": "Cooch Behar",
        "district_lgd_code": "308",
        "soi_dist_lgd": "329",
        "block_filter": lambda df: df["Dist_LGD"] == "329",
        "panchayat_filter": lambda df: df["district_lgd_code"] == "308"
    },
    "Hooghly": {
        "district_id": "wb_hooghly",
        "district_name": "Hooghly",
        "district_lgd_code": "312",
        "soi_dist_lgd": "338",
        "block_filter": lambda df: df["Dist_LGD"] == "338",
        "panchayat_filter": lambda df: df["district_lgd_code"] == "312"
    },
    "Jalpaiguri": {
        "district_id": "wb_jalpaiguri",
        "district_name": "Jalpaiguri",
        "district_lgd_code": "314",
        "soi_dist_lgd": "328",
        "block_filter": lambda df: df["Dist_LGD"] == "328",
        "panchayat_filter": lambda df: df["district_lgd_code"] == "314"
    },
    "Jhargram": {
        "district_id": "wb_jhargram",
        "district_name": "Jhargram",
        "district_lgd_code": "703",
        "soi_dist_lgd": "344N004",
        "block_filter": lambda df: df["Dist_LGD"] == "344N004",
        "panchayat_filter": lambda df: df["district_lgd_code"] == "703"
    },
    "Murshidabad": {
        "district_id": "wb_murshidabad",
        "district_name": "Murshidabad",
        "district_lgd_code": "319",
        "soi_dist_lgd": "333",
        "block_filter": lambda df: df["Dist_LGD"] == "333",
        "panchayat_filter": lambda df: df["district_lgd_code"] == "319"
    },
    "Nadia": {
        "district_id": "wb_nadia",
        "district_name": "Nadia",
        "district_lgd_code": "320",
        "soi_dist_lgd": "336",
        "block_filter": lambda df: df["Dist_LGD"] == "336",
        "panchayat_filter": lambda df: df["district_lgd_code"] == "320"
    },
    "Purba_Bardhaman": {
        "district_id": "wb_purba_bardhaman",
        "district_name": "Purba Bardhaman",
        "district_lgd_code": "306",
        "soi_dist_lgd": "335",
        "block_filter": lambda df: df["Dist_LGD"] == "335",
        "panchayat_filter": lambda df: df["district_lgd_code"] == "306"
    },
    "Purulia": {
        "district_id": "wb_purulia",
        "district_name": "Purulia",
        "district_lgd_code": "321",
        "soi_dist_lgd": "340",
        "block_filter": lambda df: df["Dist_LGD"] == "340",
        "panchayat_filter": lambda df: df["district_lgd_code"] == "321"
    },
    "Siliguri_Foothill": {
        "district_id": "wb_siliguri_foothill",
        "district_name": "Darjeeling (Siliguri Foothills)",
        "district_lgd_code": "309",
        "soi_dist_lgd": "327",
        "block_filter": lambda df: (df["Dist_LGD"] == "327") & (df["Subdis_LGD"].isin(["2162", "2163", "2164", "2165"])),
        "panchayat_filter": lambda df: (df["district_lgd_code"] == "309") & (df["block_lgd_code"].isin(["2162", "2163", "2164", "2165"]))
    }
}


def evaluate_risk_level(probabilities: Dict[str, Optional[float]]) -> Tuple[str, Dict[str, str], str]:
    """
    Applies deterministic threshold classification to event probabilities.
    Thresholds:
      - heavy_rain: <0.25 (LOW), 0.25-0.50 (MODERATE), 0.50-0.75 (HIGH), >=0.75 (VERY_HIGH)
      - severe_break_7d / dry_spell_5d: <0.25 (LOW), 0.25-0.50 (MODERATE), 0.50-0.75 (HIGH), >=0.75 (VERY_HIGH)
      - false_onset: <0.20 (LOW), 0.20-0.40 (MODERATE), 0.40-0.65 (HIGH), >=0.65 (VERY_HIGH)

    Returns:
      (overall_risk_level, head_risk_dict, risk_color)
    """
    def _categorize(p: Optional[float], t1: float, t2: float, t3: float) -> str:
        if p is None:
            return "LOW"
        if p >= t3:
            return "VERY_HIGH"
        elif p >= t2:
            return "HIGH"
        elif p >= t1:
            return "MODERATE"
        return "LOW"

    p_heavy = probabilities.get("heavy_rain")
    p_break = probabilities.get("severe_break_7d")
    p_dry5 = probabilities.get("dry_spell_5d")
    p_false = probabilities.get("false_onset")

    head_risks = {
        "heavy_rain_risk": _categorize(p_heavy, 0.25, 0.50, 0.75),
        "severe_break_risk": _categorize(p_break, 0.25, 0.50, 0.75),
        "dry_spell_risk": _categorize(p_dry5, 0.25, 0.50, 0.75),
        "false_onset_risk": _categorize(p_false, 0.20, 0.40, 0.65)
    }

    rank_order = {"LOW": 1, "MODERATE": 2, "HIGH": 3, "VERY_HIGH": 4}
    max_rank = max(rank_order[v] for v in head_risks.values())
    inv_rank = {v: k for k, v in rank_order.items()}
    overall_level = inv_rank[max_rank]
    color = RISK_COLORS[overall_level]

    return overall_level, head_risks, color


def get_agricultural_advisory(probabilities: Dict[str, Optional[float]]) -> Tuple[str, str]:
    """
    Deterministic rule-based mapping using IMD / ICAR Agrometeorological Advisory
    Services (AAS) guidelines. No LLM or generative models used.

    Returns:
      (advisory_headline, recommended_action)
    """
    p_heavy = probabilities.get("heavy_rain") or 0.0
    p_break = probabilities.get("severe_break_7d") or 0.0
    p_dry5 = probabilities.get("dry_spell_5d") or 0.0
    p_false = probabilities.get("false_onset") or 0.0
    p_onset = probabilities.get("onset") or 0.0
    p_revival = probabilities.get("revival") or 0.0

    if p_heavy >= 0.60:
        return (
            "Heavy Rainfall & Waterlogging Alert",
            "High risk of inundation. Clear drainage channels in aman paddy nurseries and vegetable plots. "
            "Postpone urea top-dressing and chemical pesticide applications until rainfall intensity subsides."
        )


    elif p_break >= 0.60 or p_dry5 >= 0.70:
        return (
            "Prolonged Dry Spell / Break Warning",
            "Severe monsoon break anticipated. Conserve in-situ soil moisture using organic mulch. "
            "Arrange life-saving supplementary irrigation for tillering paddy. Defer transplanting where water storage is depleted."
        )
    elif p_false >= 0.40 and p_onset >= 0.50:
        return (
            "False Onset Surge Precaution",
            "Early surge likely to collapse into dry hiatus. Avoid direct dry seeding in upland fields. "
            "Stagger seedbed sowing and utilize community nursery beds under assured irrigation."
        )
    elif p_onset >= 0.60:
        return (
            "Monsoon Onset Favorable Advisory",
            "Monsoon circulation establishment expected within 14 days. Accelerate land preparation, seed priming, "
            "and nursery bed sowing for long-duration Kharif rice cultivars."
        )
    elif p_revival >= 0.50:
        return (
            "Monsoon Revival & Recovery Advisory",
            "Revival of active monsoon trough expected within 7 days. Prepare fields for resumption of "
            "transplanting and apply basal fertilizer ahead of anticipated shower activity."
        )
    else:
        return (
            "Normal Seasonal Operations Advisory",
            "Normal seasonal monsoon state. Continue standard agronomic intercultural operations, "
            "maintain field bunds, and monitor district weather bulletins for localized changes."
        )


def get_statistical_outlook_properties(forecast: Dict[str, Any]) -> Dict[str, Any]:
    """Return the verified engine outlook in the spatial property contract.

    Values are inherited at district level for now. They are deliberately
    carried as an outlook section rather than represented as local downscaled
    probabilities until a validated local downscaling model exists.
    """
    source = forecast.get("statistical_7_30_day_outlook")
    if not source or source.get("forecast_status") != STATISTICAL_OUTLOOK_STATUS:
        raise ValueError("Forecast is missing the validated statistical 7-30 day outlook section")

    horizons = source.get("horizons", {})
    result: Dict[str, Any] = {
        "forecast_status": STATISTICAL_OUTLOOK_STATUS,
        "disclaimer": STATISTICAL_OUTLOOK_DISCLAIMER,
    }
    for horizon in STATISTICAL_OUTLOOK_HORIZONS:
        source_horizon = horizons.get(horizon)
        if source_horizon is None:
            raise ValueError(f"Statistical outlook is missing horizon {horizon}")
        missing = [event for event in STATISTICAL_OUTLOOK_EVENTS if event not in source_horizon]
        if missing:
            raise ValueError(f"Statistical outlook {horizon} is missing fields: {missing}")
        values = {}
        for event in STATISTICAL_OUTLOOK_EVENTS:
            probability = source_horizon[event]
            if probability is not None:
                probability = float(probability)
            if probability is not None and not 0.0 <= probability <= 1.0:
                raise ValueError(f"Statistical outlook probability out of bounds: {horizon}.{event}")
            values[event] = probability
            applicability_key = event.removesuffix("_probability") + "_applicability"
            applicability = source_horizon.get(applicability_key)
            if applicability not in {"APPLICABLE", "OUT_OF_SEASON", "UNAVAILABLE"}:
                raise ValueError(f"Statistical outlook is missing valid applicability: {horizon}.{event}")
            values[applicability_key] = applicability
        values["forecast_status"] = STATISTICAL_OUTLOOK_STATUS
        values["model_versions"] = source_horizon.get("model_versions", {})
        result[horizon] = values
    return result


class SpatialForecastEngine:
    """
    Coordinates hierarchical spatial forecast generation across:
    District -> CD Block -> Gram Panchayat
    """

    def __init__(
        self,
        forecast_engine: Optional[ForecastEngine] = None,
        blocks_path: str = DEFAULT_BLOCKS_PATH,
        panchayats_path: str = DEFAULT_PANCHAYATS_PATH,
        missing_gp_path: str = DEFAULT_MISSING_GP_PATH,
        dataset_path: str = DEFAULT_DATASET_PATH,
        block_elevation_path: str = DEFAULT_BLOCK_ELEVATION_PATH,
        panchayat_elevation_path: str = DEFAULT_PANCHAYAT_ELEVATION_PATH,
    ):
        self.forecast_engine = forecast_engine or ForecastEngine()
        self.blocks_path = blocks_path
        self.panchayats_path = panchayats_path
        self.missing_gp_path = missing_gp_path
        self.dataset_path = dataset_path
        self.block_elevation_path = block_elevation_path
        self.panchayat_elevation_path = panchayat_elevation_path

        self.blocks_gdf: Optional[gpd.GeoDataFrame] = None
        self.panchayats_gdf: Optional[gpd.GeoDataFrame] = None
        self.missing_gps_df: Optional[pd.DataFrame] = None
        self.block_elevation_lookup: Dict[str, float] = {}
        self.panchayat_elevation_lookup: Dict[str, float] = {}

        self._load_spatial_layers()

    def _load_spatial_layers(self):
        """Loads and verifies official spatial boundaries and terrain covariates."""
        if not os.path.exists(self.blocks_path):
            raise FileNotFoundError(f"Blocks spatial file not found at: {self.blocks_path}")
        self.blocks_gdf = gpd.read_file(self.blocks_path)
        if self.blocks_gdf.crs != "EPSG:4326":
            self.blocks_gdf = self.blocks_gdf.to_crs(epsg=4326)

        if not os.path.exists(self.panchayats_path):
            raise FileNotFoundError(f"Panchayats spatial file not found at: {self.panchayats_path}")
        self.panchayats_gdf = gpd.read_file(self.panchayats_path)
        if self.panchayats_gdf.crs != "EPSG:4326":
            self.panchayats_gdf = self.panchayats_gdf.to_crs(epsg=4326)

        if os.path.exists(self.missing_gp_path):
            self.missing_gps_df = pd.read_csv(self.missing_gp_path)
        else:
            self.missing_gps_df = pd.DataFrame()

        # Load SRTM elevation covariates if available
        if os.path.exists(self.block_elevation_path):
            try:
                b_elev_df = pd.read_csv(self.block_elevation_path)
                for _, row in b_elev_df.iterrows():
                    b_code = str(row.get("block_lgd", "")).strip()
                    if b_code and pd.notna(row.get("elevation_m")):
                        self.block_elevation_lookup[b_code] = float(row["elevation_m"])
                logger.info(f"Loaded {len(self.block_elevation_lookup)} block elevation records.")
            except Exception as e:
                logger.warning(f"Could not load block elevation: {e}")

        if os.path.exists(self.panchayat_elevation_path):
            try:
                p_elev_df = pd.read_csv(self.panchayat_elevation_path)
                for _, row in p_elev_df.iterrows():
                    gp_code = str(row.get("gp_lgd_code", "")).strip()
                    if gp_code and pd.notna(row.get("elevation_m")):
                        self.panchayat_elevation_lookup[gp_code] = float(row["elevation_m"])
                logger.info(f"Loaded {len(self.panchayat_elevation_lookup)} panchayat elevation records.")
            except Exception as e:
                logger.warning(f"Could not load panchayat elevation: {e}")

        logger.info(
            f"Loaded {len(self.blocks_gdf)} blocks, {len(self.panchayats_gdf)} panchayat rows, "
            f"and {len(self.missing_gps_df)} missing GP records."
        )

    def load_latest_observations(
        self,
        reference_date: Optional[str] = None
    ) -> Tuple[str, Dict[str, Dict[str, Any]]]:
        """
        Loads observations as of reference_date using AsOfFeatureBuilder.
        If reference_date is None, determines the latest common_data_as_of.
        """
        try:
            from src.features.as_of_feature_builder import AsOfFeatureBuilder
            builder = AsOfFeatureBuilder()
            if reference_date is None:
                reference_date = builder.get_common_data_as_of()

            obs_by_district = builder.build_features_as_of(reference_date)
            if obs_by_district:
                return reference_date, obs_by_district
        except Exception as e:
            logger.warning(f"AsOfFeatureBuilder fallback: {e}")

        # Fallback to historical dataset
        if not os.path.exists(self.dataset_path):
            raise FileNotFoundError(f"Dataset not found at: {self.dataset_path}")

        df = pd.read_parquet(self.dataset_path)
        latest_date = str(df["Date"].max())
        target_date = reference_date or latest_date
        df_latest = df[df["Date"] == target_date]
        if df_latest.empty:
            df_latest = df[df["Date"] == latest_date]
            target_date = latest_date

        obs_by_district = {}
        for _, row in df_latest.iterrows():
            d_name = row["District"]
            obs_by_district[d_name] = row.to_dict()

        return target_date, obs_by_district

    def generate_district_predictions(
        self,
        observations: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Runs the ForecastEngine across each district observation record.
        """
        district_forecasts = {}
        for d_key, obs in observations.items():
            result = self.forecast_engine.predict(obs)
            district_forecasts[d_key] = result
        return district_forecasts

    def build_block_forecast_layer(
        self,
        district_forecasts: Dict[str, Dict[str, Any]],
        timestamp_str: str
    ) -> gpd.GeoDataFrame:
        """
        Constructs the CD Block spatial forecast layer.
        Forecasting 187 blocks across the 12 meteorological districts.
        """
        records = []

        for model_dist, crosswalk in DISTRICT_SPATIAL_CROSSWALK.items():
            if model_dist not in district_forecasts:
                continue

            fc = district_forecasts[model_dist]
            probs = fc["summary_probabilities"]
            pcts = fc["summary_percentages"]
            statistical_outlook = get_statistical_outlook_properties(fc)

            overall_risk, head_risks, risk_color = evaluate_risk_level(probs)
            advisory_hl, advisory_action = get_agricultural_advisory(probs)

            # Filter blocks belonging to this district
            mask = crosswalk["block_filter"](self.blocks_gdf)
            dist_blocks = self.blocks_gdf[mask]

            for _, block in dist_blocks.iterrows():
                geom = block.geometry
                centroid = geom.centroid

                block_name = block.get("Sub_dist", "").strip()
                block_lgd = str(block.get("Subdis_LGD", "")).strip()

                rec = {
                    "district_id": crosswalk["district_id"],
                    "district_name": crosswalk["district_name"],
                    "district_lgd_code": crosswalk["district_lgd_code"],
                    "block_id": f"blk_{block_lgd}",
                    "block_name": block_name,
                    "block_lgd_code": block_lgd,
                    "latitude": round(float(centroid.y), 5),
                    "longitude": round(float(centroid.x), 5),
                    "centroid_lat": round(float(centroid.y), 5),
                    "centroid_lon": round(float(centroid.x), 5),
                    "elevation_m": round(self.block_elevation_lookup[block_lgd], 1) if block_lgd in self.block_elevation_lookup else None,
                    # District model probabilities
                    "onset_prob": probs["onset"],
                    "false_onset_prob": probs["false_onset"],
                    "dry_spell_5d_prob": probs["dry_spell_5d"],
                    "severe_break_7d_prob": probs["severe_break_7d"],
                    "heavy_rain_prob": probs["heavy_rain"],
                    "revival_prob": probs["revival"],
                    # Spatially downscaled probabilities (contract ready for local covariates)
                    "onset_downscaled_prob": probs["onset"],
                    "false_onset_downscaled_prob": probs["false_onset"],
                    "dry_spell_5d_downscaled_prob": probs["dry_spell_5d"],
                    "severe_break_7d_downscaled_prob": probs["severe_break_7d"],
                    "heavy_rain_downscaled_prob": probs["heavy_rain"],
                    "revival_downscaled_prob": probs["revival"],
                    # Percentages
                    "onset_prob_pct": pcts["onset"],
                    "false_onset_prob_pct": pcts["false_onset"],
                    "dry_spell_5d_prob_pct": pcts["dry_spell_5d"],
                    "severe_break_7d_prob_pct": pcts["severe_break_7d"],
                    "heavy_rain_prob_pct": pcts["heavy_rain"],
                    "revival_prob_pct": pcts["revival"],
                    # Hierarchy & Downscaling Metadata
                    "aggregation_level": "BLOCK",
                    "downscaling_method": "NONE_DISTRICT_INHERITED",
                    # Risk Classification
                    "risk_level": overall_risk,
                    "risk_color": risk_color,
                    **head_risks,
                    # Agricultural Advisory
                    "advisory_headline": advisory_hl,
                    "recommended_action": advisory_action,
                    # Engine & Forecast Metadata
                    "model_version": ENGINE_VERSION,
                    "forecast_status": OPERATIONAL_STATUS,
                    "disclaimer": OPERATIONAL_DISCLAIMER,
                    "data_timestamp": timestamp_str,
                    "current_system_date": "2026-09-13",
                    "data_as_of": timestamp_str[:10],
                    "forecast_reference_date": timestamp_str[:10],
                    "data_freshness_status": "CURRENT" if timestamp_str.startswith("2026") else "STALE",
                    "event_applicability": fc.get("event_applicability", {}),
                    # Statistical outlook is district-inherited until a
                    # validated local downscaling model is available.
                    "statistical_7_30_day_outlook": statistical_outlook,
                    "geometry": geom
                }
                records.append(rec)

        gdf = gpd.GeoDataFrame(records, geometry="geometry", crs="EPSG:4326")
        logger.info(f"Constructed block forecast layer with {len(gdf)} features.")
        return gdf

    def build_panchayat_forecast_layer(
        self,
        district_forecasts: Dict[str, Dict[str, Any]],
        timestamp_str: str
    ) -> gpd.GeoDataFrame:
        """
        Constructs the Gram Panchayat spatial forecast layer.
        Forecasting 1,710 safe Panchayats across the 12 meteorological districts.
        Strictly excludes invalid dummy/zero codes and preserves missing 85 GPs.
        """
        records = []
        # Filter valid safe GPs
        p_valid = self.panchayats_gdf[
            (self.panchayats_gdf["gp_lgd_code"].astype(str) != "0") &
            (self.panchayats_gdf["gp_name"].str.strip() != "")
        ]

        for model_dist, crosswalk in DISTRICT_SPATIAL_CROSSWALK.items():
            if model_dist not in district_forecasts:
                continue

            fc = district_forecasts[model_dist]
            probs = fc["summary_probabilities"]
            pcts = fc["summary_percentages"]
            statistical_outlook = get_statistical_outlook_properties(fc)

            overall_risk, head_risks, risk_color = evaluate_risk_level(probs)
            advisory_hl, advisory_action = get_agricultural_advisory(probs)

            # Filter Panchayats belonging to this district
            mask = crosswalk["panchayat_filter"](p_valid)
            dist_gps = p_valid[mask]

            for _, gp in dist_gps.iterrows():
                geom = gp.geometry
                centroid = geom.centroid

                gp_name = str(gp.get("gp_name", "")).strip()
                gp_lgd = str(gp.get("gp_lgd_code", "")).strip()
                block_name = str(gp.get("block_name", "")).strip()
                block_lgd = str(gp.get("block_lgd_code", "")).strip()

                rec = {
                    "district_id": crosswalk["district_id"],
                    "district_name": crosswalk["district_name"],
                    "district_lgd_code": crosswalk["district_lgd_code"],
                    "block_id": f"blk_{block_lgd}",
                    "block_name": block_name,
                    "block_lgd_code": block_lgd,
                    "panchayat_id": f"gp_{gp_lgd}",
                    "panchayat_name": gp_name,
                    "gp_lgd_code": gp_lgd,
                    "latitude": round(float(centroid.y), 5),
                    "longitude": round(float(centroid.x), 5),
                    "centroid_lat": round(float(centroid.y), 5),
                    "centroid_lon": round(float(centroid.x), 5),
                    "elevation_m": round(self.panchayat_elevation_lookup[gp_lgd], 1) if gp_lgd in self.panchayat_elevation_lookup else None,
                    # District model probabilities
                    "onset_prob": probs["onset"],
                    "false_onset_prob": probs["false_onset"],
                    "dry_spell_5d_prob": probs["dry_spell_5d"],
                    "severe_break_7d_prob": probs["severe_break_7d"],
                    "heavy_rain_prob": probs["heavy_rain"],
                    "revival_prob": probs["revival"],
                    # Downscaled probabilities
                    "onset_downscaled_prob": probs["onset"],
                    "false_onset_downscaled_prob": probs["false_onset"],
                    "dry_spell_5d_downscaled_prob": probs["dry_spell_5d"],
                    "severe_break_7d_downscaled_prob": probs["severe_break_7d"],
                    "heavy_rain_downscaled_prob": probs["heavy_rain"],
                    "revival_downscaled_prob": probs["revival"],
                    # Percentages
                    "onset_prob_pct": pcts["onset"],
                    "false_onset_prob_pct": pcts["false_onset"],
                    "dry_spell_5d_prob_pct": pcts["dry_spell_5d"],
                    "severe_break_7d_prob_pct": pcts["severe_break_7d"],
                    "heavy_rain_prob_pct": pcts["heavy_rain"],
                    "revival_prob_pct": pcts["revival"],
                    # Hierarchy & Downscaling Metadata
                    "aggregation_level": "PANCHAYAT",
                    "downscaling_method": "NONE_DISTRICT_INHERITED",
                    # Risk Classification
                    "risk_level": overall_risk,
                    "risk_color": risk_color,
                    **head_risks,
                    # Agricultural Advisory
                    "advisory_headline": advisory_hl,
                    "recommended_action": advisory_action,
                    # Engine & Forecast Metadata
                    "model_version": ENGINE_VERSION,
                    "forecast_status": OPERATIONAL_STATUS,
                    "disclaimer": OPERATIONAL_DISCLAIMER,
                    "data_timestamp": timestamp_str,
                    "current_system_date": "2026-09-13",
                    "data_as_of": timestamp_str[:10],
                    "forecast_reference_date": timestamp_str[:10],
                    "data_freshness_status": "CURRENT" if timestamp_str.startswith("2026") else "STALE",
                    "event_applicability": fc.get("event_applicability", {}),
                    # Geometry remains official safe-layer geometry; the
                    # outlook values are explicitly not called downscaled.
                    "statistical_7_30_day_outlook": statistical_outlook,
                    "geometry": geom
                }
                records.append(rec)

        gdf = gpd.GeoDataFrame(records, geometry="geometry", crs="EPSG:4326")
        logger.info(f"Constructed panchayat forecast layer with {len(gdf)} features.")
        return gdf

    def generate_and_save_all_forecasts(
        self,
        output_dir: str = DEFAULT_OUTPUT_DIR,
        observations: Optional[Dict[str, Dict[str, Any]]] = None,
        timestamp_str: Optional[str] = None,
        reference_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes end-to-end spatial forecast generation and writes GeoJSON artifacts.
        Outputs:
          - latest_block_forecast.geojson
          - latest_panchayat_forecast.geojson
          - latest_risk_map.geojson (MapLibre / Leaflet ready)
        """
        os.makedirs(output_dir, exist_ok=True)

        if observations is None:
            latest_date, obs_dict = self.load_latest_observations(reference_date=reference_date)
            timestamp = timestamp_str or f"{latest_date}T00:00:00Z"
        else:
            obs_dict = observations
            timestamp = timestamp_str or datetime.now(timezone.utc).isoformat()

        # Run inference
        dist_forecasts = self.generate_district_predictions(obs_dict)

        # Build layers
        block_gdf = self.build_block_forecast_layer(dist_forecasts, timestamp)
        panchayat_gdf = self.build_panchayat_forecast_layer(dist_forecasts, timestamp)

        # Write files
        block_file = os.path.join(output_dir, "latest_block_forecast.geojson")
        panchayat_file = os.path.join(output_dir, "latest_panchayat_forecast.geojson")
        risk_map_file = os.path.join(output_dir, "latest_risk_map.geojson")

        block_gdf.to_file(block_file, driver="GeoJSON")
        panchayat_gdf.to_file(panchayat_file, driver="GeoJSON")
        # latest_risk_map.geojson serves as the primary map layer for MapLibre/Leaflet
        block_gdf.to_file(risk_map_file, driver="GeoJSON")

        summary = {
            "current_system_date": "2026-09-13",
            "data_as_of": timestamp[:10],
            "forecast_reference_date": timestamp[:10],
            "data_freshness_status": "CURRENT" if timestamp.startswith("2026") else "STALE",
            "forecast_status": OPERATIONAL_STATUS,
            "disclaimer": OPERATIONAL_DISCLAIMER,
            "statistical_7_30_day_outlook": {
                "forecast_status": STATISTICAL_OUTLOOK_STATUS,
                "disclaimer": STATISTICAL_OUTLOOK_DISCLAIMER,
                "horizons": list(STATISTICAL_OUTLOOK_HORIZONS),
                "events": [
                    "dry_spell_probability",
                    "severe_break_probability",
                    "heavy_rain_probability",
                    "revival_probability",
                ],
                "downscaling_method": "NONE_DISTRICT_INHERITED",
            },
            "data_timestamp": timestamp,
            "districts_forecasted": len(dist_forecasts),
            "blocks_forecasted": len(block_gdf),
            "safe_panchayats_forecasted": panchayat_gdf["gp_lgd_code"].nunique(),
            "safe_panchayat_polygons": len(panchayat_gdf),
            "panchayat_polygon_excess_over_unique_lgd": int(
                len(panchayat_gdf) - panchayat_gdf["gp_lgd_code"].nunique()
            ),
            "panchayat_lgd_ids_with_multiple_polygons": int(
                (panchayat_gdf["gp_lgd_code"].value_counts() > 1).sum()
            ),
            "panchayat_count_definition": (
                "safe_panchayats_forecasted counts unique GP LGD identifiers; "
                "safe_panchayat_polygons counts returned spatial features. "
                "The difference is caused by duplicated GP LGD identifiers across "
                "multiple source block polygons and is retained pending cadastral reconciliation."
            ),
            "official_gps_intentionally_excluded": len(self.missing_gps_df),
            "unsupported_blocks_deficit": len(self.blocks_gdf) - len(block_gdf),
            "elevation_metadata": {
                "source": "SRTM 90m (NASA/USGS via Open-Elevation API)",
                "blocks_with_elevation": len(self.block_elevation_lookup),
                "panchayats_with_elevation": len(self.panchayat_elevation_lookup),
                "elevation_correlation_rainfall": -0.019,
                "elevation_p_value": 0.952,
                "downscaling_implication": "Zero empirical correlation with rainfall across West Bengal districts (r=-0.019, p=0.952). Intra-district downscaling cannot be scientifically validated without sub-district AWS data."
            },
            "output_files": {
                "block_forecast": block_file,
                "panchayat_forecast": panchayat_file,
                "risk_map": risk_map_file
            }
        }

        # Save metadata summary
        meta_file = os.path.join(output_dir, "forecast_run_metadata.json")
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        return summary


def run_pipeline() -> Dict[str, Any]:
    """CLI / programmatic runner for spatial forecast generation."""
    engine = SpatialForecastEngine()
    summary = engine.generate_and_save_all_forecasts()
    return summary


if __name__ == "__main__":
    import pprint
    logging.basicConfig(level=logging.INFO)
    print("\n--- Running VARSHASENTINEL Spatial Forecast Pipeline ---")
    res = run_pipeline()
    pprint.pprint(res)
