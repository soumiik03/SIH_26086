"""
VARSHASENTINEL (SIH26086) - Leakage-Safe IOD Feature Integration Pipeline
=========================================================================
Parses official Australian Bureau of Meteorology (BoM) weekly IOD/DMI records,
applies the established 3-day publication lag rule, and merges the point-in-time
climate driver into the daily master dataset via deterministic as-of backward join.

Outputs:
  - data/processed/varshasentinel_master_with_iod.csv
  - data/processed/varshasentinel_master_with_iod.parquet
"""

import os
import sys
import logging
import pandas as pd
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("varshasentinel.integrate_iod")

BOM_RAW_PATH = "data/raw/climate_indices/bom_iod_weekly_raw.txt"
MASTER_DATASET_CSV = "data/processed/varshasentinel_master_dataset.csv"
OUTPUT_CSV = "data/processed/varshasentinel_master_with_iod.csv"
OUTPUT_PARQUET = "data/processed/varshasentinel_master_with_iod.parquet"


def build_iod_features():
    logger.info(f"Loading raw BoM weekly IOD records: {BOM_RAW_PATH}")
    if not os.path.exists(BOM_RAW_PATH):
        raise FileNotFoundError(f"BoM raw file not found at {BOM_RAW_PATH}")

    bom_df = pd.read_csv(
        BOM_RAW_PATH,
        header=None,
        names=["start_int", "end_int", "iod_dmi"]
    )
    bom_df["period_start_date"] = pd.to_datetime(bom_df["start_int"].astype(str), format="%Y%m%d")
    bom_df["period_end_date"] = pd.to_datetime(bom_df["end_int"].astype(str), format="%Y%m%d")

    # Publication Lag Rule: Value ending Sunday becomes available 3 days later (Wednesday)
    bom_df["available_date"] = bom_df["period_end_date"] + pd.Timedelta(days=3)
    bom_df = bom_df.sort_values("available_date").reset_index(drop=True)
    logger.info(f"Loaded {len(bom_df)} weekly BoM records ({bom_df['period_start_date'].min().date()} to {bom_df['period_end_date'].max().date()})")

    # Load master dataset
    logger.info(f"Loading existing master dataset: {MASTER_DATASET_CSV}")
    master_df = pd.read_csv(MASTER_DATASET_CSV)
    master_df["Date"] = pd.to_datetime(master_df["Date"])
    min_date = master_df["Date"].min()
    max_date = master_df["Date"].max()
    logger.info(f"Master dataset has {len(master_df):,} rows spanning {min_date.date()} to {max_date.date()}")

    # Construct continuous daily timeline starting 30 days before min_date for warm-up lags
    warmup_start = min_date - pd.Timedelta(days=30)
    daily_timeline = pd.date_range(start=warmup_start, end=max_date, freq="D")
    daily_iod_df = pd.DataFrame({"Date": daily_timeline})

    # Point-in-time backward As-Of merge
    # For any date D, selects latest BoM release with available_date <= D
    daily_merged = pd.merge_asof(
        daily_iod_df,
        bom_df[["available_date", "period_start_date", "period_end_date", "iod_dmi"]],
        left_on="Date",
        right_on="available_date",
        direction="backward"
    )

    # Feature Engineering on continuous daily series
    daily_merged["iod_positive_flag"] = (daily_merged["iod_dmi"] > 0.4).astype(int)
    daily_merged["iod_negative_flag"] = (daily_merged["iod_dmi"] < -0.4).astype(int)
    daily_merged["iod_dmi_lag7"] = daily_merged["iod_dmi"].shift(7)
    daily_merged["iod_dmi_lag14"] = daily_merged["iod_dmi"].shift(14)

    # Filter for exact master dataset timeframe
    daily_features = daily_merged[daily_merged["Date"] >= min_date].copy()

    # Verification: Confirm that for every row, period_end_date + 3 days <= Date
    future_leakage_mask = (daily_features["period_end_date"] + pd.Timedelta(days=3)) > daily_features["Date"]
    assert future_leakage_mask.sum() == 0, f"Critical error: Found {future_leakage_mask.sum()} lookahead violations!"
    logger.info("Point-in-time as-of join verified: ZERO lookahead leakage detected.")

    # Select feature columns to merge
    cols_to_merge = [
        "Date",
        "iod_dmi",
        "iod_positive_flag",
        "iod_negative_flag",
        "iod_dmi_lag7",
        "iod_dmi_lag14"
    ]
    iod_subset = daily_features[cols_to_merge].copy()

    # Merge into master dataset on Date
    enriched_df = pd.merge(master_df, iod_subset, on="Date", how="left")

    # Assert row count and null integrity
    assert len(enriched_df) == len(master_df), f"Row count mismatch: {len(enriched_df)} vs {len(master_df)}"
    for col in cols_to_merge:
        null_count = enriched_df[col].isna().sum()
        assert null_count == 0, f"Found {null_count} nulls in {col}!"

    logger.info(f"Enriched master dataset successfully constructed ({len(enriched_df):,} rows, {len(enriched_df.columns)} columns).")

    # Format Date back to string for consistency
    enriched_df["Date"] = enriched_df["Date"].dt.strftime("%Y-%m-%d")

    # Save to CSV and Parquet
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    logger.info(f"Saving enriched dataset to CSV: {OUTPUT_CSV}")
    enriched_df.to_csv(OUTPUT_CSV, index=False)

    logger.info(f"Saving enriched dataset to Parquet: {OUTPUT_PARQUET}")
    enriched_df.to_parquet(OUTPUT_PARQUET, index=False)

    logger.info("IOD feature integration complete.")
    return enriched_df, daily_features


if __name__ == "__main__":
    build_iod_features()
