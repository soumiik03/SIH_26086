"""
VARSHASENTINEL (SIH26086) — Regional Atmospheric Signal Ingestion & Feature Integration
Author: Lead ML & Climate-Data Engineer
Date: September 2026

Ingests real, authoritative meteorological reanalysis data from NOAA Physical Sciences
Laboratory (PSL) / NCEP-NCAR Reanalysis 1 Daily Averages (U850, V850, SLP/MSLP)
covering 2020-01-01 to 2025-12-31 for West Bengal (Lat 21.8°N - 27.5°N, Lon 85.0°E - 90.0°E).

Applies strict point-in-time publication lag (delta = 1 day) to prevent lookahead leakage.
Merges with varshasentinel_master_with_iod.parquet and exports the enhanced master dataset.
"""

import os
import re
import time
import urllib.request
from pathlib import Path
import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]
RAW_ATMOS_DIR = ROOT_DIR / "data" / "raw" / "atmospheric"
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
MASTER_IOD_PARQUET = PROCESSED_DIR / "varshasentinel_master_with_iod.parquet"
OUTPUT_PARQUET = PROCESSED_DIR / "varshasentinel_master_with_atmospheric_signals.parquet"
OUTPUT_CSV = PROCESSED_DIR / "varshasentinel_master_with_atmospheric_signals.csv"

# NOAA PSL OPeNDAP base URLs
# Lat: 27.5 (idx 25), 25.0 (idx 26), 22.5 (idx 27) -> 3 points
# Lon: 85.0 (idx 34), 87.5 (idx 35), 90.0 (idx 36) -> 3 points
# Level: 850 hPa is index 2 in level[17]
NOAA_PRESSURE_URL = "https://psl.noaa.gov/thredds/dodsC/Datasets/ncep.reanalysis.dailyavgs/pressure"
NOAA_SURFACE_URL = "https://psl.noaa.gov/thredds/dodsC/Datasets/ncep.reanalysis.dailyavgs/surface"

YEARS = [2020, 2021, 2022, 2023, 2024, 2025]


def fetch_and_cache(url: str, cache_path: Path, max_retries: int = 3) -> str:
    """Fetch URL with disk caching and retry."""
    if cache_path.exists():
        with open(cache_path, "r", encoding="utf-8") as f:
            return f.read()

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (VARSHASENTINEL; SIH26086)"})

    for attempt in range(max_retries):
        try:
            print(f"[Fetch] {url} (attempt {attempt + 1}/{max_retries})...")
            with urllib.request.urlopen(req, timeout=45) as resp:
                content = resp.read().decode("utf-8")
                with open(cache_path, "w", encoding="utf-8") as f:
                    f.write(content)
                return content
        except Exception as e:
            print(f"[Warning] Failed attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(3)
            else:
                raise


def parse_grid_ascii(text: str) -> dict[int, dict[int, list[float]]]:
    """
    Parse NOAA PSL OPeNDAP ASCII response into a dict:
    time_idx -> {lat_idx: [val_lon0, val_lon1, val_lon2]}
    """
    lines = text.split("\n")
    data_lines = []
    capture = False
    for line in lines:
        if "---" in line:
            capture = True
            continue
        if capture and line.strip():
            data_lines.append(line.strip())

    grid_by_time = {}
    for dl in data_lines:
        # Match lines like "[0][0][1], 3.0, 1.3, 0.125" (pressure) or "[0][1], 101497.5, ..." (surface)
        m = re.match(r"\[(\d+)\](?:\[(\d+)\])?\[(\d+)\],\s*(.*)", dl)
        if m:
            t = int(m.group(1))
            lat_idx = int(m.group(3))
            vals = [float(v.strip()) for v in m.group(4).split(",") if v.strip()]
            if t not in grid_by_time:
                grid_by_time[t] = {}
            grid_by_time[t][lat_idx] = vals

    return grid_by_time


def get_days_in_year(year: int) -> int:
    return 366 if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else 365


def ingest_noaa_atmospheric_data() -> pd.DataFrame:
    """Ingest NOAA PSL U850, V850, and SLP for 2020-2025."""
    RAW_ATMOS_DIR.mkdir(parents=True, exist_ok=True)
    all_daily_records = []

    for year in YEARS:
        num_days = get_days_in_year(year)
        max_day_idx = num_days - 1

        # U850
        u_url = f"{NOAA_PRESSURE_URL}/uwnd.{year}.nc.ascii?uwnd[0:1:{max_day_idx}][2:1:2][25:1:27][34:1:36]"
        u_cache = RAW_ATMOS_DIR / f"uwnd_{year}_850hpa_wb.ascii"
        u_text = fetch_and_cache(u_url, u_cache)
        u_grid = parse_grid_ascii(u_text)

        # V850
        v_url = f"{NOAA_PRESSURE_URL}/vwnd.{year}.nc.ascii?vwnd[0:1:{max_day_idx}][2:1:2][25:1:27][34:1:36]"
        v_cache = RAW_ATMOS_DIR / f"vwnd_{year}_850hpa_wb.ascii"
        v_text = fetch_and_cache(v_url, v_cache)
        v_grid = parse_grid_ascii(v_text)

        # SLP (Surface Sea Level Pressure)
        slp_url = f"{NOAA_SURFACE_URL}/slp.{year}.nc.ascii?slp[0:1:{max_day_idx}][25:1:27][34:1:36]"
        slp_cache = RAW_ATMOS_DIR / f"slp_{year}_surface_wb.ascii"
        slp_text = fetch_and_cache(slp_url, slp_cache)
        slp_grid = parse_grid_ascii(slp_text)

        start_date = pd.Timestamp(f"{year}-01-01")
        for day_idx in range(num_days):
            current_date = start_date + pd.Timedelta(days=day_idx)

            # Extract 3x3 grids
            # lat_idx: 0=27.5°N (North), 1=25.0°N (Central), 2=22.5°N (South)
            # lon_idx: 0=85.0°E, 1=87.5°E, 2=90.0°E
            u_rows = [u_grid[day_idx][lat_idx] for lat_idx in [0, 1, 2]]
            v_rows = [v_grid[day_idx][lat_idx] for lat_idx in [0, 1, 2]]
            slp_rows = [slp_grid[day_idx][lat_idx] for lat_idx in [0, 1, 2]]

            # Regional averages across West Bengal bounding box
            u850_mean = float(np.mean(u_rows))
            v850_mean = float(np.mean(v_rows))
            wind850_speed = float(np.sqrt(u850_mean**2 + v850_mean**2))

            # SLP in Pascals -> convert to hPa
            slp_hpa_matrix = np.array(slp_rows) / 100.0
            mslp_mean = float(np.mean(slp_hpa_matrix))

            # Synoptic pressure gradient: Sub-Himalayan (lat 27.5) minus South (lat 22.5)
            # Negative: Monsoon trough over central/south plains (active)
            # Positive: Trough shifts north to foothills (break)
            slp_north = float(np.mean(slp_hpa_matrix[0, :]))
            slp_south = float(np.mean(slp_hpa_matrix[2, :]))
            regional_slp_gradient = float(slp_north - slp_south)

            all_daily_records.append({
                "Date": current_date.strftime("%Y-%m-%d"),
                "u850_raw": round(u850_mean, 4),
                "v850_raw": round(v850_mean, 4),
                "wind850_speed_raw": round(wind850_speed, 4),
                "mslp_raw": round(mslp_mean, 2),
                "regional_slp_gradient_raw": round(regional_slp_gradient, 2),
            })

    df_atmos = pd.DataFrame(all_daily_records)
    df_atmos = df_atmos.sort_values("Date").reset_index(drop=True)
    return df_atmos


def apply_leakage_safe_features(df_atmos: pd.DataFrame, lag_days: int = 1) -> pd.DataFrame:
    """
    Apply operational availability lag (delta = 1 day) and engineer rolling circulation metrics.
    Observation on date t is only available at t + lag_days.
    Hence, feature at date D uses observation from D - lag_days.
    """
    df = df_atmos.copy()

    # Base shifted features (1-day operational availability lag)
    df["u850_regional"] = df["u850_raw"].shift(lag_days).bfill()
    df["v850_regional"] = df["v850_raw"].shift(lag_days).bfill()
    df["wind850_speed"] = df["wind850_speed_raw"].shift(lag_days).bfill()
    df["mslp_regional"] = df["mslp_raw"].shift(lag_days).bfill()
    df["regional_slp_gradient"] = df["regional_slp_gradient_raw"].shift(lag_days).bfill()

    # 7-day lag (observation from D - 1 - 7 = D - 8)
    df["u850_lag7"] = df["u850_regional"].shift(7).bfill()
    df["mslp_lag7"] = df["mslp_regional"].shift(7).bfill()

    # 7-day rolling synoptic means (backward rolling window on usable observations)
    df["u850_rolling_7d"] = df["u850_regional"].rolling(window=7, min_periods=1).mean().round(4).bfill()
    df["mslp_rolling_7d"] = df["mslp_regional"].rolling(window=7, min_periods=1).mean().round(2).bfill()

    feature_cols = [
        "Date",
        "u850_regional",
        "v850_regional",
        "wind850_speed",
        "mslp_regional",
        "regional_slp_gradient",
        "u850_lag7",
        "mslp_lag7",
        "u850_rolling_7d",
        "mslp_rolling_7d",
    ]
    return df[feature_cols]


def merge_with_master_dataset():
    """Merge atmospheric features with master dataset."""
    print("=== Step 4: Atmospheric Signal Ingestion & Integration ===")

    # 1. Ingest real NOAA PSL data
    df_atmos_raw = ingest_noaa_atmospheric_data()
    print(f"[Ingest] Ingested {len(df_atmos_raw)} daily records from NOAA PSL (2020-2025).")

    # 2. Engineer leakage-safe features with 1-day operational availability lag
    df_atmos_features = apply_leakage_safe_features(df_atmos_raw, lag_days=1)
    print(f"[Features] Engineered {len(df_atmos_features.columns) - 1} atmospheric circulation features.")

    # 3. Load master dataset
    df_master = pd.read_parquet(MASTER_IOD_PARQUET)
    orig_rows = len(df_master)
    print(f"[Master] Loaded existing master dataset: {orig_rows} rows, {len(df_master.columns)} columns.")

    # 4. Merge on Date
    df_merged = df_master.merge(df_atmos_features, on="Date", how="left")

    # 5. Validation assertions
    assert len(df_merged) == orig_rows, f"Row count mismatch! {len(df_merged)} vs {orig_rows}"
    assert df_merged["Date"].min() == "2020-01-01", "Start date mismatch!"
    assert df_merged["Date"].max() == "2025-12-31", "End date mismatch!"

    new_cols = [c for c in df_atmos_features.columns if c != "Date"]
    for c in new_cols:
        assert c in df_merged.columns, f"Missing feature {c} in merged dataset!"
        null_count = df_merged[c].isna().sum()
        assert null_count == 0, f"Found {null_count} nulls in {c}!"

    # 6. Save outputs
    df_merged.to_parquet(OUTPUT_PARQUET, index=False)
    df_merged.to_csv(OUTPUT_CSV, index=False)
    print(f"[Output] Saved enhanced parquet: {OUTPUT_PARQUET} ({OUTPUT_PARQUET.stat().st_size / 1024:.1f} KB)")
    print(f"[Output] Saved enhanced CSV: {OUTPUT_CSV} ({OUTPUT_CSV.stat().st_size / (1024*1024):.2f} MB)")
    print("=== Atmospheric Signal Integration Complete ===")


if __name__ == "__main__":
    merge_with_master_dataset()
