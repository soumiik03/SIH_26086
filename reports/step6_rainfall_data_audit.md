# Step 6 Rainfall Data Audit

## Finding

The repository contains rainfall time series at a district-representative scale only. It does not contain a station network, gridded rainfall product, satellite precipitation files, or Panchayat/block rainfall observations.

The existing rainfall input is therefore not sufficient to calculate a defensible local Panchayat rainfall anomaly.

## Existing rainfall sources

| Source | Provider/provenance | Location | Spatial resolution | Temporal resolution | Coverage | Missingness | Units | Observation type | Local anomaly suitability |
|---|---|---|---|---|---|---:|---|---|---|
| `data/raw/weather/gangetic_alluvial_zone_2020_2025.csv` | Provider not machine-documented; repository describes blended/reanalysis-derived data | 4 district representative coordinates | One coordinate per district; no grid resolution | Daily | 2020-01-01 to 2025-12-31 | 0 rainfall nulls | `Rainfall_Observed_mm` | District representative proxy; measurement support not documented | No |
| `data/raw/weather/red_laterite_zone_2020_2025.csv` | Provider not machine-documented; repository describes blended/reanalysis-derived data | 4 district representative coordinates | One coordinate per district; no grid resolution | Daily | 2020-01-01 to 2025-12-31 | 0 rainfall nulls | `Rainfall_Observed_mm` | District representative proxy; measurement support not documented | No |
| `data/raw/weather/terai_teesta_zone_2020_2025.csv` | Provider not machine-documented; repository describes blended/reanalysis-derived data | 4 district representative coordinates | One coordinate per district; no grid resolution | Daily | 2020-01-01 to 2025-12-31 | 0 rainfall nulls | `Rainfall_Observed_mm` | District representative proxy; measurement support not documented | No |

The three files contain 26,304 rows in total and 12 unique district/coordinate combinations. Each district has one rainfall value per day. Latitude and longitude identify the representative district coordinate; they do not identify an observation footprint or a Panchayat rainfall measurement.

No rainfall-related file under `data/spatial/` contains rainfall values. The spatial files contain administrative boundaries and terrain attributes. NOAA atmospheric files under `data/raw/atmospheric/` contain circulation variables, not precipitation.

## Existing derived rainfall features

The processed datasets contain regional/district-proxy features including:

- `Rainfall_Observed_mm`
- `Rolling_Rainfall_7d_mm`
- `Rolling_Rainfall_30d_mm`
- `rolling_rain_3d_mm`
- `rolling_rain_15d_mm`
- `Dry_Spell_Days_Streak`
- `Drought_Stress_Index`
- `Waterlogging_Risk_Index`

These remain regional observation features. They must not be relabeled as local Panchayat rainfall.

## Data-quality caveat

The repository documentation calls the files estimated/blended or reanalysis-derived but does not include a provider identifier, station identifier, grid coordinates, algorithm version, or publication metadata. The rainfall files are therefore usable as existing model inputs at their current regional scale, but not as traceable local ground truth.

## Audit conclusion

No real local rainfall observations are currently available in the repository. No synthetic Panchayat rainfall, geographic noise, centroid-extracted rainfall, or administrative-ID rainfall feature was created.
