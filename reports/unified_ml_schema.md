# VARSHASENTINEL (SIH26086) — Unified ML Schema Specification

**Project**: VARSHASENTINEL — Hyperlocal Monsoon Intelligence System for West Bengal  
**Lead Engineer**: Lead ML & Climate-Data Engineer  
**Audit Date**: September 2026  
**Status**: Architecture & Schema Standard Complete  

---

## 1. Schema Design Principles

The proposed **Unified ML Schema** achieves three objectives:
1. **Harmonizes the 3 regional files** into a single master tabular dataset while preserving zone-specific risk indices (`Drought_Stress_Index` and `Waterlogging_Risk_Index`).
2. **Injects derived agrometeorological features** (Diurnal Temperature Range, Vapor Pressure Deficit, Cyclical Temporal & MJO Encodings) to provide physical signals required for sub-seasonal forecasting.
3. **Appends explicit, scientifically-derived target columns** for the 5 core monsoon events at 7–30 day lead horizons.

---

## 2. Full Unified Schema Specification

| Group | Field Name | Data Type | Units / Range | Nullable? | Description / Engineering Logic |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **Index** | `date` | `DATE` | `2020-01-01` to `2025-12-31` | No | Calendar date of observation |
| **Index** | `district_id` | `VARCHAR(32)` | 12 distinct districts | No | Standardized snake_case district identifier |
| **Index** | `zone_id` | `VARCHAR(32)` | 3 zones | No | `gangetic_alluvial`, `red_laterite`, `terai_teesta` |
| **Spatial** | `latitude` | `FLOAT32` | 22.0°N to 27.0°N | No | District centroid latitude |
| **Spatial** | `longitude` | `FLOAT32` | 86.0°E to 90.0°E | No | District centroid longitude |
| **Calendar** | `day_of_year` | `INT16` | 1 to 366 | No | Day number within the calendar year |
| **Calendar** | `doy_sin` | `FLOAT32` | -1.0 to 1.0 | No | $\sin(2\pi \times \text{day\_of\_year} / 365.25)$ (Cyclical seasonal phase) |
| **Calendar** | `doy_cos` | `FLOAT32` | -1.0 to 1.0 | No | $\cos(2\pi \times \text{day\_of\_year} / 365.25)$ (Cyclical seasonal phase) |
| **Calendar** | `monsoon_season_flag`| `INT8` | 0 or 1 | No | 1 if date is between June 1 and September 30, else 0 |
| **Surface** | `rainfall_observed_mm`| `FLOAT32`| $\ge 0.0$ mm | No | Daily accumulated precipitation |
| **Surface** | `tmax_c` | `FLOAT32` | 10.0°C to 50.0°C | No | Daily maximum 2-meter air temperature (clamped) |
| **Surface** | `tmin_c` | `FLOAT32` | 5.0°C to 35.0°C | No | Daily minimum 2-meter air temperature |
| **Surface** | `dtr_c` | `FLOAT32` | $\ge 0.5$°C | No | Diurnal Temperature Range ($T_{max} - T_{min}$) |
| **Surface** | `rh_pct` | `FLOAT32` | 15.0% to 100.0% | No | Daily mean surface relative humidity |
| **Surface** | `solar_rad_mjm2` | `FLOAT32` | 0.0 to 35.0 MJ/m² | No | Surface solar radiation downwelling |
| **Surface** | `vpd_kpa` | `FLOAT32` | $\ge 0.0$ kPa | No | Vapor Pressure Deficit (computed from $T_{mean}$ and $RH$) |
| **Memory** | `dry_spell_streak` | `INT16` | $\ge 0$ days | No | Consecutive days with rainfall $< 2.5$ mm (IMD rule) |
| **Memory** | `rolling_rain_3d_mm` | `FLOAT32`| $\ge 0.0$ mm | No | 3-day trailing rainfall sum ($\sum_{k=0}^2 R_{t-k}$) |
| **Memory** | `rolling_rain_7d_mm` | `FLOAT32`| $\ge 0.0$ mm | No | 7-day trailing rainfall sum |
| **Memory** | `rolling_rain_15d_mm`| `FLOAT32`| $\ge 0.0$ mm | No | 15-day trailing rainfall sum |
| **Memory** | `rolling_rain_30d_mm`| `FLOAT32`| $\ge 0.0$ mm | No | 30-day trailing rainfall sum |
| **Climate** | `mjo_phase` | `INT8` | 1 to 8 | No | Active Madden-Julian Oscillation phase |
| **Climate** | `mjo_phase_sin` | `FLOAT32` | -1.0 to 1.0 | No | $\sin(2\pi \times \text{mjo\_phase} / 8)$ (Cyclical phase) |
| **Climate** | `mjo_phase_cos` | `FLOAT32` | -1.0 to 1.0 | No | $\cos(2\pi \times \text{mjo\_phase} / 8)$ (Cyclical phase) |
| **Climate** | `mjo_amplitude` | `FLOAT32` | $\ge 0.0$ | No | Real-time Multivariate MJO amplitude strength |
| **Climate** | `nino34_anomaly` | `FLOAT32` | -3.0°C to +3.0°C | No | Central Pacific SST anomaly (ENSO signal) |
| **Climate** | `dmi_iod_anomaly` | `FLOAT32` | -2.0°C to +2.0°C | Yes | Dipole Mode Index (IOD signal; to be ingested) |
| **Zonal Risk**| `drought_stress_idx`| `FLOAT32` | 0.0 to 1.0 | No | 0.0 for non-laterite zones unless mapped from soil deficit |
| **Zonal Risk**| `waterlog_risk_idx` | `FLOAT32` | 0.0 to 1.0 | No | 0.0 for non-terai zones unless mapped from drainage excess |
| **Legacy** | `active_crop_cycle` | `VARCHAR(32)`| Category | Yes | Cropping rotation stage (preserved for agro-advisory) |
| **Target 1** | `target_onset_window_14d` | `INT8` | 0 or 1 | No | **1** if seasonal monsoon onset occurs within next 14 days |
| **Target 2** | `target_false_onset_flag` | `INT8` | 0 or 1 | No | **1** if current onset surge will collapse into break within 10d |
| **Target 3** | `target_dry_spell_5d_14d` | `INT8` | 0 or 1 | No | **1** if $\ge 5$-day dry spell begins within next 14 days |
| **Target 4** | `target_dry_spell_7d_21d` | `INT8` | 0 or 1 | No | **1** if $\ge 7$-day severe break begins within next 21 days |
| **Target 5** | `target_heavy_rain_7d` | `INT8` | 0 or 1 | No | **1** if daily rain $\ge 64.5$ mm occurs in next 7 days |
| **Target 6** | `target_revival_7d` | `INT8` | 0 or 1 | No | **1** if active dry spell terminates with $\ge 5$ mm rain in next 7d |

---

## 3. Storage & Partitioning Strategy

* **File Format**: Standard Parquet (`master_varshasentinel_features_targets.parquet`) and partitioned CSV by zone (`data/processed/`).
* **Compression**: `snappy` or `zstd`.
* **Primary Key**: `(district_id, date)`.
* **Sorting Order**: `district_id ASC, date ASC` (strictly chronological per time series).
