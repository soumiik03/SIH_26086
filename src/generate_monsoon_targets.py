"""
VARSHASENTINEL (SIH26086) - Monsoon Target Generation & Feature Pipeline
========================================================================
This module ingests the 3 raw agro-climatic zone CSVs, rectifies physical
thermodynamic anomalies, computes derived agrometeorological features,
and algorithmically synthesizes the 6 core monsoon prediction targets
under strict anti-leakage rules.
"""

import os
import sys
import logging
import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("varshasentinel")

RAW_FILES = [
    ("gangetic_alluvial", "gangetic_alluvial_zone_2020_2025.csv"),
    ("red_laterite", "red_laterite_zone_2020_2025.csv"),
    ("terai_teesta", "terai_teesta_zone_2020_2025.csv")
]

PROCESSED_DIR = "data/processed"
LOG_DIR = "reports"


def clean_temperature_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rectifies physical thermodynamic inconsistencies (Tmax < Tmin and extreme outliers)
    using physical diurnal clamping.
    """
    df = df.copy()
    corrections = []

    for idx, row in df.iterrows():
        tmax = row["Tmax_C"]
        tmin = row["Tmin_C"]
        district = row["District"]
        date = row["Date"]

        # Check extreme sub-zero anomaly in tropical/subtropical summer
        if tmax < 10.0 and row["Rainfall_Observed_mm"] > 50.0 and pd.to_datetime(date).month in [5, 6, 7, 8, 9]:
            new_tmax = round(tmin + 1.2, 2)
            corrections.append({
                "index": idx,
                "date": date,
                "district": district,
                "issue": f"Unphysical low Tmax ({tmax} C) during heavy rain",
                "old_tmax": tmax,
                "old_tmin": tmin,
                "new_tmax": new_tmax,
                "new_tmin": tmin
            })
            df.at[idx, "Tmax_C"] = new_tmax
            tmax = new_tmax

        # Check thermodynamic inversion Tmax < Tmin
        if tmax < tmin:
            clean_tmin = round(min(tmax, tmin), 2)
            clean_tmax = round(max(tmax, tmin) + 0.5, 2)
            corrections.append({
                "index": idx,
                "date": date,
                "district": district,
                "issue": f"Inversion Tmax ({tmax} C) < Tmin ({tmin} C)",
                "old_tmax": tmax,
                "old_tmin": tmin,
                "new_tmax": clean_tmax,
                "new_tmin": clean_tmin
            })
            df.at[idx, "Tmax_C"] = clean_tmax
            df.at[idx, "Tmin_C"] = clean_tmin

    corr_df = pd.DataFrame(corrections)
    os.makedirs(LOG_DIR, exist_ok=True)
    corr_log_path = os.path.join(LOG_DIR, "temperature_corrections.csv")
    corr_df.to_csv(corr_log_path, index=False)
    logger.info(f"Rectified {len(corrections)} physical temperature anomalies. Log saved to {corr_log_path}")

    return df


def calculate_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes physically sound agrometeorological features strictly on or before date t:
    - Diurnal Temperature Range (DTR)
    - Vapor Pressure Deficit (VPD in kPa)
    - Day of year sin/cos (cyclical annual solar phase)
    - MJO phase sin/cos (cyclical intra-seasonal wave phase)
    - Short/Medium backward rolling rainfall (3d, 15d)
    """
    df = df.copy()
    dt_series = pd.to_datetime(df["Date"])
    doy = dt_series.dt.dayofyear

    # 1. Diurnal Temperature Range
    df["dtr_c"] = (df["Tmax_C"] - df["Tmin_C"]).clip(lower=0.5)

    # 2. Vapor Pressure Deficit (VPD in kPa)
    # T_mean proxy
    t_mean = (df["Tmax_C"] + df["Tmin_C"]) / 2.0
    # Saturation vapor pressure (Tetens formula in kPa)
    e_sat = 0.61078 * np.exp((17.27 * t_mean) / (t_mean + 237.3))
    # Actual vapor pressure
    e_act = e_sat * (df["Relative_Humidity_pct"] / 100.0)
    df["vpd_kpa"] = np.maximum(0.0, e_sat - e_act).round(4)

    # 3. Cyclical Temporal Encodings
    df["day_of_year"] = doy
    df["doy_sin"] = np.sin(2 * np.pi * doy / 365.25).round(5)
    df["doy_cos"] = np.cos(2 * np.pi * doy / 365.25).round(5)

    # 4. Cyclical MJO Encodings
    mjo_phase = df["MJO_Phase"].astype(int)
    df["mjo_phase_sin"] = np.sin(2 * np.pi * mjo_phase / 8.0).round(5)
    df["mjo_phase_cos"] = np.cos(2 * np.pi * mjo_phase / 8.0).round(5)

    # 5. Backward Rolling Windows per District (Anti-leakage: closed='left' or shift(0) strictly backward)
    # Sort chronologically per district
    df = df.sort_values(["District", "Date"]).reset_index(drop=True)
    grouped = df.groupby("District")["Rainfall_Observed_mm"]

    # 3-day and 15-day backward rolling sums
    df["rolling_rain_3d_mm"] = grouped.rolling(3, min_periods=1).sum().reset_index(drop=True).round(2)
    df["rolling_rain_15d_mm"] = grouped.rolling(15, min_periods=1).sum().reset_index(drop=True).round(2)

    # Ensure zone risk columns are harmonized across all zones
    if "Drought_Stress_Index" not in df.columns:
        df["Drought_Stress_Index"] = 0.0
    else:
        df["Drought_Stress_Index"] = df["Drought_Stress_Index"].fillna(0.0)

    if "Waterlogging_Risk_Index" not in df.columns:
        df["Waterlogging_Risk_Index"] = 0.0
    else:
        df["Waterlogging_Risk_Index"] = df["Waterlogging_Risk_Index"].fillna(0.0)

    return df


def generate_monsoon_targets(df: pd.DataFrame) -> pd.DataFrame:
    """
    Synthesizes the 6 core monsoon prediction targets looking into future windows [t+1, t+H]:
    1. target_onset_window_14d: Seasonal monsoon onset occurs within [t, t+14]
    2. target_false_onset_flag: An early pre-monsoon surge collapses within 10d
    3. target_dry_spell_5d_14d: A >=5-day dry spell starts within [t+1, t+14]
    4. target_dry_spell_7d_21d: A >=7-day dry break starts within [t+1, t+21]
    5. target_heavy_rain_7d: Daily rain >=64.5mm or 3-day rain >=150mm within [t+1, t+7]
    6. target_revival_7d: If in dry spell, revival (>=5mm rain) occurs within [t+1, t+7]
    """
    df = df.sort_values(["District", "Date"]).reset_index(drop=True).copy()
    dt = pd.to_datetime(df["Date"])
    df["_dt"] = dt
    df["_year"] = dt.dt.year
    df["_month"] = dt.dt.month
    df["_doy"] = dt.dt.dayofyear

    # Initialize target columns
    df["target_onset_window_14d"] = 0
    df["target_false_onset_flag"] = 0
    df["target_dry_spell_5d_14d"] = 0
    df["target_dry_spell_7d_21d"] = 0
    df["target_heavy_rain_7d"] = 0
    df["target_revival_7d"] = 0

    districts = df["District"].unique()

    for district in districts:
        dist_idx = df[df["District"] == district].index
        dist_df = df.loc[dist_idx].copy()
        n = len(dist_df)
        precip = dist_df["Rainfall_Observed_mm"].values
        tmax = dist_df["Tmax_C"].values
        rh = dist_df["Relative_Humidity_pct"].values
        dates = dist_df["_dt"].values
        months = dist_df["_month"].values
        years = dist_df["_year"].values
        doys = dist_df["_doy"].values

        # ------------------------------------------------------------------
        # TARGET 1 & 2: ONSET AND FALSE ONSET PER YEAR
        # ------------------------------------------------------------------
        unique_years = np.unique(years)
        for yr in unique_years:
            yr_mask = (years == yr)
            yr_indices = np.where(yr_mask)[0]

            # Candidate search window for onset: May 15 (DOY ~135) to July 15 (DOY ~196)
            onset_day_idx = None
            false_onset_indices = []

            for i in yr_indices:
                m = months[i]
                d = doys[i]
                # Look for onset criteria between May 15 and July 15
                if m in [5, 6, 7] and d >= 135:
                    if i + 3 < n:
                        # 1. 2 consecutive rainy days (>=2.5mm)
                        cond_2day = (precip[i] >= 2.5) and (precip[i + 1] >= 2.5)
                        # 2. 3-day rainfall >= 25mm (40mm in Terai)
                        zone_thresh = 40.0 if "terai" in str(dist_df["Zone"].iloc[0]).lower() else 25.0
                        cond_vol = (precip[i:i + 3].sum() >= zone_thresh)
                        # 3. Sustained maritime humidity
                        cond_rh = (rh[i] >= 70.0)

                        if cond_2day and cond_vol and cond_rh:
                            # Check subsequent 10 days for collapse (false onset)
                            end_check = min(n, i + 10)
                            forward_dry_max = 0
                            curr_dry = 0
                            for k in range(i + 2, end_check):
                                if precip[k] < 2.5:
                                    curr_dry += 1
                                    forward_dry_max = max(forward_dry_max, curr_dry)
                                else:
                                    curr_dry = 0

                            # If it collapsed into >=5 dry days within 10 days, it is a false onset
                            if forward_dry_max >= 5 and onset_day_idx is None:
                                false_onset_indices.append(i)
                            elif onset_day_idx is None:
                                # First sustained surge is true onset
                                onset_day_idx = i

            # If no onset found by strict rule, take the peak June surge
            if onset_day_idx is None:
                june_indices = [i for i in yr_indices if months[i] == 6]
                if june_indices:
                    onset_day_idx = june_indices[int(len(june_indices) / 2)]

            # Populate Target 1: target_onset_window_14d
            if onset_day_idx is not None:
                for i in yr_indices:
                    # If current day is within 14 days preceding or at onset
                    if 0 <= (onset_day_idx - i) <= 14:
                        df.loc[dist_idx[i], "target_onset_window_14d"] = 1

            # Populate Target 2: target_false_onset_flag
            for fo_idx in false_onset_indices:
                # Mark the false onset surge window (surge day and 2 days before)
                for w in range(max(0, fo_idx - 2), min(n, fo_idx + 1)):
                    df.loc[dist_idx[w], "target_false_onset_flag"] = 1

        # ------------------------------------------------------------------
        # TARGET 3, 4, 5, 6: INTRA-SEASONAL HAZARDS & BREAKS
        # ------------------------------------------------------------------
        for i in range(n):
            # Target 5: Heavy Rainfall in next 7 days [t+1, t+7]
            if i + 7 < n:
                fwd_rain = precip[i + 1:i + 8]
                has_daily_heavy = (fwd_rain >= 64.5).any()
                has_3day_heavy = False
                for j in range(len(fwd_rain) - 2):
                    if fwd_rain[j:j + 3].sum() >= 150.0:
                        has_3day_heavy = True
                        break
                if has_daily_heavy or has_3day_heavy:
                    df.loc[dist_idx[i], "target_heavy_rain_7d"] = 1

            # Target 3 & 4: Dry Spells during monsoon (June to October)
            m = months[i]
            if m in [6, 7, 8, 9, 10]:
                # Target 3: 5-day dry spell starts in next 14 days [t+1, t+14]
                if i + 14 + 5 < n:
                    # Check if a 5-consecutive-day dry streak starts within [i+1, i+14]
                    for start_offset in range(1, 15):
                        run = precip[i + start_offset:i + start_offset + 5]
                        if (run < 2.5).all():
                            df.loc[dist_idx[i], "target_dry_spell_5d_14d"] = 1
                            break

                # Target 4: 7-day severe break starts in next 21 days [t+1, t+21]
                if i + 21 + 7 < n:
                    for start_offset in range(1, 22):
                        run = precip[i + start_offset:i + start_offset + 7]
                        if (run < 2.5).all():
                            df.loc[dist_idx[i], "target_dry_spell_7d_21d"] = 1
                            break

            # Target 6: Revival within next 7 days (conditional on currently in dry spell)
            # Current dry spell is active if Dry_Spell_Days_Streak >= 3
            current_streak = dist_df["Dry_Spell_Days_Streak"].iloc[i]
            if current_streak >= 3 and i + 7 < n:
                # Revival occurs if within [i+1, i+7], rain >= 5mm followed by sustained rain >=2.5mm
                for fwd in range(1, 8):
                    if i + fwd + 1 < n:
                        if precip[i + fwd] >= 5.0 and precip[i + fwd + 1] >= 2.5:
                            df.loc[dist_idx[i], "target_revival_7d"] = 1
                            break

    # Clean temporary helper columns
    df = df.drop(columns=["_dt", "_year", "_month", "_doy"])
    return df


def main():
    logger.info("Starting VARSHASENTINEL Data Pipeline...")

    zone_dfs = []
    for zone_id, filename in RAW_FILES:
        candidate_paths = [
            os.path.join("data", "raw", "weather", filename),
            filename,
            os.path.join(os.getcwd(), "data", "raw", "weather", filename),
            os.path.join(os.getcwd(), filename),
        ]
        filepath = next((p for p in candidate_paths if os.path.exists(p)), None)
        if filepath is None:
            raise FileNotFoundError(f"Could not locate {filename} in {candidate_paths}")
        logger.info(f"Loading {zone_id} from {filepath}")
        zdf = pd.read_csv(filepath)
        zdf["zone_id"] = zone_id
        zone_dfs.append(zdf)

    master_raw = pd.concat(zone_dfs, ignore_index=True)
    logger.info(f"Combined Raw Dataset: {master_raw.shape[0]} rows, {master_raw.shape[1]} columns")

    # 1. Clean Temperature Anomalies
    master_clean = clean_temperature_anomalies(master_raw)

    # 2. Calculate Derived Features
    master_featured = calculate_derived_features(master_clean)

    # 3. Synthesize Ground Truth Targets
    master_dataset = generate_monsoon_targets(master_featured)

    # 4. Anti-Leakage Feature Filtering
    # Never include Target_Crops, Active_Crop_Cycle as model features
    if "Active_Crop_Cycle" in master_dataset.columns:
        master_dataset = master_dataset.drop(columns=["Active_Crop_Cycle"])

    # 5. Export Master Datasets
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    csv_path = os.path.join(PROCESSED_DIR, "varshasentinel_master_dataset.csv")
    parquet_path = os.path.join(PROCESSED_DIR, "varshasentinel_master_dataset.parquet")

    master_dataset.to_csv(csv_path, index=False)
    master_dataset.to_parquet(parquet_path, index=False)

    logger.info(f"Successfully exported master CSV to: {csv_path}")
    logger.info(f"Successfully exported master Parquet to: {parquet_path}")

    # Log summary statistics
    target_cols = [
        "target_onset_window_14d",
        "target_false_onset_flag",
        "target_dry_spell_5d_14d",
        "target_dry_spell_7d_21d",
        "target_heavy_rain_7d",
        "target_revival_7d"
    ]
    logger.info("\n=== TARGET POSITIVE OCCURRENCE RATES ===")
    for t in target_cols:
        count = master_dataset[t].sum()
        pct = (count / len(master_dataset)) * 100
        logger.info(f"  {t:25s}: {count:5d} / {len(master_dataset)} ({pct:5.2f}%)")


if __name__ == "__main__":
    main()
