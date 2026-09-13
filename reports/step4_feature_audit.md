# VARSHASENTINEL (SIH26086) — Step 4 Feature Audit Report

**Subsystem**: Feature Engineering & Atmospheric Signal Integration  
**Date**: September 2026  
**Status**: Step 4A Audit Complete  

---

## 1. Executive Summary

This audit assesses all input features currently present in the VARSHASENTINEL modeling pipeline (`data/processed/varshasentinel_master_with_iod.parquet`). 

The current system captures planetary boundary teleconnections (ENSO, IOD, MJO), surface agrometeorological parameters (rainfall, temperature, relative humidity, solar radiation, VPD), and derived rolling hydrological indicators. However, **atmospheric circulation predictors are completely absent** from the dataset. There are currently no winds ($u, v$ components or speed), no pressure variables (MSLP or surface pressure), no geopotential heights, and no synoptic pressure gradients.

This confirms the critical scientific gap highlighted in Problem Statement SIH26086:
> *"The system must bridge the gap between global climate teleconnections and hyper-local weather outcomes by pairing global planetary boundary conditions with regional atmospheric data."*

---

## 2. Complete Inventory of Existing Features

The master dataset contains **26 modeling features** across 8 functional categories:

| # | Category | Feature Column | Data Type | Physical Meaning & Units | Range in Master Dataset |
|---|---|---|---|---|---|
| 1 | **ENSO Teleconnection** | `Nino34_Anomaly` | Float | Sea Surface Temperature anomaly in Niño 3.4 region (5°N–5°S, 170°W–120°W) [°C] | -1.49°C to +1.87°C |
| 2 | **IOD Teleconnection** | `iod_dmi` | Float | Indian Ocean Dipole Mode Index: $\text{SST}_{\text{anom}}(\text{WTIO}) - \text{SST}_{\text{anom}}(\text{SETIO})$ [°C] | -1.54°C to +1.89°C |
| 3 | **IOD Teleconnection** | `iod_positive_flag` | Binary | Binary flag for Positive IOD phase ($> +0.40^\circ\text{C}$) | 0 or 1 |
| 4 | **IOD Teleconnection** | `iod_negative_flag` | Binary | Binary flag for Negative IOD phase ($< -0.40^\circ\text{C}$) | 0 or 1 |
| 5 | **IOD Teleconnection** | `iod_dmi_lag7` | Float | Point-in-time 7-day lagged IOD DMI [°C] | -1.54°C to +1.89°C |
| 6 | **IOD Teleconnection** | `iod_dmi_lag14` | Float | Point-in-time 14-day lagged IOD DMI [°C] | -1.54°C to +1.89°C |
| 7 | **MJO Teleconnection** | `MJO_Phase` | Integer | Real-time Multivariate MJO active octant (1 to 8) | 1 to 8 |
| 8 | **MJO Teleconnection** | `MJO_Amplitude` | Float | Wheeler-Hendon RMM amplitude $\sqrt{\text{RMM1}^2 + \text{RMM2}^2}$ | 0.30 to 2.20 |
| 9 | **MJO Teleconnection** | `mjo_phase_sin` | Float | Cyclic transformation: $\sin(2\pi \cdot \text{MJO\_Phase} / 8)$ | -1.00 to +1.00 |
| 10 | **MJO Teleconnection** | `mjo_phase_cos` | Float | Cyclic transformation: $\cos(2\pi \cdot \text{MJO\_Phase} / 8)$ | -1.00 to +1.00 |
| 11 | **Rainfall Predictors** | `Rainfall_Observed_mm` | Float | Daily 24h cumulative surface precipitation [mm] | 0.00 to 389.64 mm |
| 12 | **Rainfall Predictors** | `rolling_rain_3d_mm` | Float | 3-day backward rolling precipitation sum [mm] | 0.00 to 587.20 mm |
| 13 | **Rainfall Predictors** | `Rolling_Rainfall_7d_mm` | Float | 7-day backward rolling precipitation sum [mm] | 0.00 to 892.40 mm |
| 14 | **Rainfall Predictors** | `rolling_rain_15d_mm` | Float | 15-day backward rolling precipitation sum [mm] | 0.00 to 1,085.10 mm |
| 15 | **Rainfall Predictors** | `Rolling_Rainfall_30d_mm` | Float | 30-day backward rolling precipitation sum [mm] | 0.00 to 1,153.55 mm |
| 16 | **Rainfall Predictors** | `Dry_Spell_Days_Streak` | Integer | Consecutive days with daily precipitation $< 2.5\text{ mm}$ [days] | 0 to 208 days |
| 17 | **Rainfall Predictors** | `Drought_Stress_Index` | Float | Root-zone soil moisture deficit & moisture stress proxy | 0.00 to 1.00 |
| 18 | **Rainfall Predictors** | `Waterlogging_Risk_Index` | Float | Topographic accumulation & soil saturation flood proxy | 0.00 to 1.00 |
| 19 | **Temperature Predictors**| `Tmax_C` | Float | Daily maximum 2-meter air temperature [°C] | 15.20°C to 47.54°C |
| 20 | **Temperature Predictors**| `Tmin_C` | Float | Daily minimum 2-meter air temperature [°C] | 7.80°C to 32.24°C |
| 21 | **Temperature Predictors**| `dtr_c` | Float | Diurnal Temperature Range ($T_{max} - T_{min}$) [°C] | 0.20°C to 23.40°C |
| 22 | **Humidity / VPD** | `Relative_Humidity_pct` | Float | Daily mean surface relative humidity [%] | 22.0% to 99.0% |
| 23 | **Humidity / VPD** | `vpd_kpa` | Float | Vapour Pressure Deficit from Tetens formulation [kPa] | 0.05 to 4.85 kPa |
| 24 | **Temporal Predictors** | `day_of_year` | Integer | Calendar day of year (1 to 366) | 1 to 366 |
| 25 | **Temporal Predictors** | `doy_sin` | Float | Annual seasonal cycle component: $\sin(2\pi \cdot \text{DOY} / 365.25)$ | -1.00 to +1.00 |
| 26 | **Temporal Predictors** | `doy_cos` | Float | Annual seasonal cycle component: $\cos(2\pi \cdot \text{DOY} / 365.25)$ | -1.00 to +1.00 |

---

## 3. Existing Spatial Metadata

- **Entities**: 12 West Bengal districts covering 3 distinct agro-climatic zones:
  - *Terai-Teesta Zone*: Alipurduar, Cooch Behar, Jalpaiguri, Siliguri Foothills
  - *Gangetic Alluvial Zone*: Hooghly, Murshidabad, Nadia, Purba Bardhaman
  - *Red & Laterite Zone*: Bankura, Birbhum (Suri), Jhargram, Purulia
- **Coordinate Extents**:
  - Latitude: 21.86°N to 26.99°N
  - Longitude: 85.82°E to 89.88°E
- **Spatial Granularity**: District-level centroid time series, inherited by Blocks and Panchayats (`downscaling_method = NONE_DISTRICT_INHERITED`).

---

## 4. Circulation Variables Already Present

**Status: ZERO.**  
A full inspection of `src/`, `data/`, and `models/` confirms that no atmospheric circulation variables are currently ingested or engineered:
- Zonal winds ($u$): None
- Meridional winds ($v$): None
- Wind speed / direction: None
- Sea-level pressure (SLP / MSLP): None
- Geopotential height: None
- Pressure gradients: None

---

## 5. Exact Missing PS-Relevant Atmospheric Predictors

To fulfill Problem Statement SIH26086, the following core atmospheric circulation signals are required:

1. **850 hPa Zonal Wind ($U_{850}$)**:
   - *Physical Role*: Directly measures the strength of the Indian Summer Monsoon Low-Level Jet (LLJ) across the Bay of Bengal into eastern India. Strong westerly/southwesterly flow marks monsoon onset and active spells; weakening or easterly anomalies signify break conditions.
2. **850 hPa Meridional Wind ($V_{850}$)**:
   - *Physical Role*: Quantifies cross-equatorial southerly moisture advection from the Bay of Bengal into the Gangetic plains and Sub-Himalayan West Bengal. Essential for distinguishing genuine onset from false onset and predicting heavy downpours.
3. **850 hPa Wind Speed ($WS_{850} = \sqrt{u^2 + v^2}$)**:
   - *Physical Role*: Scalar kinematic intensity of the monsoon current.
4. **Mean Sea Level Pressure ($MSLP$)**:
   - *Physical Role*: Indicates the regional synoptic pressure regime, low-pressure depressions, and the presence of the Monsoon Trough over Bengal.
5. **Regional Synoptic Pressure Gradient ($\Delta SLP$)**:
   - *Physical Role*: The north-south pressure differential ($\text{SLP}_{\text{Sub-Himalayan}} - \text{SLP}_{\text{Gangetic}}$). A negative gradient (trough over central Gangetic Bengal) drives active monsoon convergence; a positive or reversed gradient (trough shifting north to the foothills) is the textbook meteorological signature of a **Monsoon Break**.
6. **Circulation Temporal Memory (Lags & Rolling Means)**:
   - *Physical Role*: 7-day lags and 7-day rolling means ($U_{850,\text{lag7}}$, $MSLP_{\text{lag7}}$, $U_{850,\text{roll7}}$, $MSLP_{\text{roll7}}$) provide the sub-seasonal inertia required for 7–30 day outlooks.
