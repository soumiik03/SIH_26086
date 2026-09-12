# VARSHASENTINEL (SIH26086) — Missing Data & Climate Driver Gap Report

**Project**: VARSHASENTINEL — Hyperlocal Monsoon Intelligence System for West Bengal  
**Lead Engineer**: Lead ML & Climate-Data Engineer  
**Audit Date**: September 2026  
**Status**: Gap Analysis Completed  

---

## 1. Executive Summary

While the existing repository contains 26,304 clean, gap-free daily records of surface weather, MJO, and ENSO across 12 West Bengal districts (2020–2025), significant scientific gaps exist between the **current data** and the **operational requirements for 7–30 day probabilistic monsoon forecasting**.

This report outlines:
1. Missing climate teleconnections (IOD)
2. Missing dynamic atmospheric variables (Tropospheric winds, MSLP)
3. Missing spatial granularity (Block/Panchayat downscaling proxies)
4. Missing target variables (The 5 core monsoon prediction events)
5. Temporal baseline limitations (Need for climatological normals)

---

## 2. Teleconnection & Large-Scale Driver Gaps

| Climate Driver | In Existing Data? | Importance to West Bengal Monsoon | Scientific Impact of Absence |
| :--- | :---: | :--- | :--- |
| **ENSO (Niño 3.4 Anomaly)** | ✅ **YES** | Modulates inter-annual monsoon strength. Warm phase (El Niño) suppresses; Cold phase (La Niña) enhances. | Already present. Captures macro-scale Walker circulation shift. |
| **MJO (Phase & Amplitude)** | ✅ **YES** | Primary driver of 30–60 day intra-seasonal monsoon oscillations (active vs. break spells). | Already present. MJO phases 4–6 enhance Bay of Bengal convection. |
| **Indian Ocean Dipole (IOD / DMI)** | ❌ **MISSING** | **Critical driver of Bay of Bengal monsoonal depressions**. A positive IOD can counteract El Niño and deliver excess rainfall to Eastern India, while a negative IOD precipitates severe dry breaks. | **High Impact**: Forecasts cannot distinguish between IOD-compensated monsoon years and full-scale drought years. |
| **Equatorial Indian Ocean Oscillation (EQUINOO)** | ❌ **MISSING** | Atmospheric counterpart to IOD; directly controls zonal wind anomalies over the central equatorial Indian Ocean. | Moderate Impact: Can be partially proxied by IOD + MJO. |

---

## 3. Dynamic Atmospheric & Hydrological Parameter Gaps

For scientifically defensible 7–30 day forecasting, surface observations alone are insufficient because monsoon breaks and heavy precipitation events originate in the mid-to-lower troposphere:

### 3.1 Missing Upper-Air Dynamics
1. **Low-Level Zonal Wind ($U_{850}$ at 850 hPa)**:
   * *Role*: The low-level monsoon westerly jet (Findlater Jet). Kinetic energy at 850 hPa over the Arabian Sea and Bay of Bengal is IMD's primary dynamical criterion for declaring monsoon onset over peninsular and eastern India.
   * *Status*: ❌ **Missing** from all 3 files.
2. **Tropical Easterly Jet ($U_{200}$ at 200 hPa)**:
   * *Role*: Upper tropospheric easterlies indicate the seasonal establishment of the Tibetan anticyclone.
   * *Status*: ❌ **Missing**.
3. **Mean Sea Level Pressure (MSLP) & Pressure Gradient**:
   * *Role*: The North-South pressure gradient between the Head Bay of Bengal and southern peninsula dictates the positioning of the **Monsoon Trough**. When the trough shifts northward to the Himalayan foothills, Gangetic Bengal suffers a severe "Break Monsoon", while the Terai-Teesta zone experiences catastrophic flash floods.
   * *Status*: ❌ **Missing**.

### 3.2 Missing Land Surface & Hydrological State
1. **Soil Moisture (0–10 cm and 10–40 cm root zone)**:
   * *Role*: Crucial for land-atmosphere coupling and moisture recycling during dry spell revival.
   * *Current Status*: Only indirect proxies exist (`Rolling_Rainfall_7d_mm`, `Dry_Spell_Days_Streak`, `Drought_Stress_Index`).
2. **Potential Evapotranspiration (PET) / Vapor Pressure Deficit (VPD)**:
   * *Role*: Quantifies atmospheric water demand for accurate crop water stress and false onset validation.
   * *Current Status*: Missing (can be computed using Penman-Monteith from existing $T_{max}, T_{min}, RH,$ and Solar Radiation).

---

## 4. Missing Target Ground Truth Labels

Currently, the three notebooks only contain labels for `Target_Crops` (e.g. Potato, Jute, Aman Rice, Pineapple, Tea). **None of the 5 required monsoon prediction targets are labeled in the existing data**:

```
Current Labels in Repo:
  └── Target_Crops (Agricultural suitability only)

Required Targets for VARSHASENTINEL:
  ├── 1. Monsoon Onset (Binary event / Day of Onset per district)
  ├── 2. False Onset (Binary risk flag)
  ├── 3. 5-Day Dry Spell / Break (Multi-day forward hazard probability)
  ├── 4. 7-Day Severe Dry Spell (Multi-day forward hazard probability)
  ├── 5. Heavy Rainfall / Waterlogging Risk (Binary hazard flag)
  └── 6. Dry Spell Revival (Event termination flag)
```

These target series must be algorithmically computed from the daily rainfall and atmospheric observations using IMD-aligned agrometeorological rules before any predictive ML model can be trained.

---

## 5. Spatial & Temporal Resolution Limitations

### 5.1 Spatial Resolution
* **Current**: District centroid level (1 coordinate pair per district, 12 districts total across West Bengal).
* **Missing**: Sub-district, block, and gram-panchayat resolution.
* **Path Forward for VARSHASENTINEL**:
  * Phase 1: Establish verified district-level probabilistic models using the 12 districts.
  * Phase 2: Ingest high-resolution gridded data (e.g. IMD $0.25^\circ \times 0.25^\circ$ or ERA5 $0.1^\circ$) to downscale risk to block/panchayat levels using the ML Downscaling component shown in the project architecture.

### 5.2 Temporal Horizon
* **Current**: 2020-01-01 to 2025-12-31 (6 years).
* **Limitation**: While 2,192 continuous days per district are excellent for daily weather modeling, 6 years capture only 6 summer monsoon seasons (June–September 2020, 2021, 2022, 2023, 2024, 2025). This yields only 6 annual onset events per district (72 total onset samples across 12 districts).
* **Defensible ML Strategy**:
  1. Train rolling intra-seasonal event models (dry spells, heavy rainfall, revival) directly on the full 26,304 daily rows (where hundreds of events occur).
  2. For onset and false onset, use the 72 district-season instances augmented with strict physics-informed meteorological indicators rather than overparameterized deep networks.
