# VARSHASENTINEL (SIH26086) — Data Inventory Report

**Project**: VARSHASENTINEL — Hyperlocal Monsoon Intelligence System for West Bengal  
**Lead Engineer**: Lead ML & Climate-Data Engineer  
**Audit Date**: September 2026  
**Status**: Comprehensive Baseline Audit Complete  

---

## 1. Executive Summary

This inventory audits all existing tabular datasets present in the repository. The project currently possesses three distinct CSV datasets organized by West Bengal Agro-Climatic Zones covering **January 1, 2020 through December 31, 2025** (6 full meteorological years, 2,192 days per district, exactly 8,768 records per zone, 26,304 total records).

Each dataset contains surface agrometeorological variables, two macro-climate teleconnections (MJO and ENSO), derived rolling hydrological memory metrics, and zone-specific stress/cropping indices.

---

## 2. Dataset-by-Dataset Inventory

### Dataset 1: Gangetic Alluvial Zone
* **Filename**: [`gangetic_alluvial_zone_2020_2025.csv`](file:///j:/Projects/Web/SIH_26086/SIH_26086/gangetic_alluvial_zone_2020_2025.csv)
* **Agro-Climatic Zone**: Gangetic New Alluvial Zone (Central & Southern West Bengal Plains)
* **Estimated Data Provenance**: Blended Numerical Weather Prediction (NWP) / Reanalysis downscaled with agrometeorological station coordinates.
* **Temporal Coverage**: 2020-01-01 to 2025-12-31 (Daily time-step, continuous, 2,192 days).
* **Spatial Resolution & Entities**: 4 Districts (1 centroid coordinate pair per district):
  * *Purba Bardhaman* (Lat: 23.25°N, Lon: 87.85°E) — 2,192 rows
  * *Hooghly* (Lat: 22.88°N, Lon: 87.78°E) — 2,192 rows
  * *Nadia* (Lat: 23.40°N, Lon: 88.50°E) — 2,192 rows
  * *Murshidabad* (Lat: 24.10°N, Lon: 88.25°E) — 2,192 rows
* **Total Records / Rows**: 8,768 rows × 18 columns
* **File Size**: ~1.22 MB
* **Column Breakdown**:
  1. `Date` (YYYY-MM-DD): Observation timestamp
  2. `Zone` (Categorical): "Gangetic_New_Alluvial_Zone"
  3. `District` (Categorical): District name
  4. `Latitude` (Float): Centroid latitude (°N)
  5. `Longitude` (Float): Centroid longitude (°E)
  6. `Rainfall_Observed_mm` (Float): Daily 24h accumulated rainfall (0.00 to 110.27 mm, Mean: 2.46 mm)
  7. `Tmax_C` (Float): Daily maximum temperature (17.25°C to 44.01°C, Mean: 31.69°C)
  8. `Tmin_C` (Float): Daily minimum temperature (8.01°C to 32.24°C, Mean: 20.01°C)
  9. `Relative_Humidity_pct` (Float): Daily mean relative humidity (33.10% to 99.00%, Mean: 57.46%)
  10. `Solar_Radiation_MJm2` (Float): Daily surface insolation (4.00 to 26.00 MJ/m², Mean: 18.74 MJ/m²)
  11. `MJO_Phase` (Integer): Madden-Julian Oscillation phase (1 to 8, Mean: 4.57)
  12. `MJO_Amplitude` (Float): MJO amplitude strength (0.30 to 2.20, Mean: 1.23)
  13. `Nino34_Anomaly` (Float): Oceanic Niño Index 3.4 SST anomaly (-1.49°C to +1.87°C, Mean: -0.12°C)
  14. `Dry_Spell_Days_Streak` (Integer): Streak of consecutive days with rainfall < 2.5 mm (0 to 208 days)
  15. `Target_Crops` (Categorical): Crop label (Potato: 2,888; Jute: 2,928; Aman_Rice: 2,952)
  16. `Rolling_Rainfall_7d_mm` (Float): 7-day rolling precipitation sum (0.00 to 227.39 mm, Mean: 17.20 mm)
  17. `Rolling_Rainfall_30d_mm` (Float): 30-day rolling precipitation sum (0.00 to 459.66 mm, Mean: 73.65 mm)
  18. `Active_Crop_Cycle` (Categorical): Cropping calendar phase (`Rabi_Potato_Boro`: 2,888; `PreMonsoon_Fallow`: 2,208; `Kharif_Aman_Jute`: 3,672)
* **Missing Value Rate**: 0.0% (Zero missing cells)
* **Duplicate Rows**: 0 exact duplicates; 0 (District, Date) key collisions
* **Modelling Suitability**: **Suitable for Meteorological Feature Extraction & Temporal Modeling** (after correcting 4 minor $T_{max} < T_{min}$ inversions and removing crop target proxies).

---

### Dataset 2: Red Laterite Zone
* **Filename**: [`red_laterite_zone_2020_2025.csv`](file:///j:/Projects/Web/SIH_26086/SIH_26086/red_laterite_zone_2020_2025.csv)
* **Agro-Climatic Zone**: Red & Laterite Zone (Western Plateau Fringe / Drought-Prone Drylands)
* **Estimated Data Provenance**: Gridded agromet observation/reanalysis blended with local terrain parameters.
* **Temporal Coverage**: 2020-01-01 to 2025-12-31 (Daily continuous, 2,192 days).
* **Spatial Resolution & Entities**: 4 Districts:
  * *Purulia* (Lat: 23.33°N, Lon: 86.36°E) — 2,192 rows
  * *Bankura* (Lat: 23.23°N, Lon: 87.07°E) — 2,192 rows
  * *Jhargram* (Lat: 22.45°N, Lon: 86.98°E) — 2,192 rows
  * *Birbhum (Suri)* (Lat: 23.91°N, Lon: 87.53°E) — 2,192 rows
* **Total Records / Rows**: 8,768 rows × 18 columns
* **File Size**: ~1.07 MB
* **Column Breakdown**: Same 17 baseline columns as Gangetic, with Column 18 replaced by:
  * `Drought_Stress_Index` (Float, 0.00 to 1.00, Mean: 0.49, Std: 0.42): Physical proxy representing root-zone water deficit and heat stress.
  * `Target_Crops` (Categorical): `Pulses_Arhar`: 4,091; `Millets_Ragi`: 2,556; `Maize`: 1,995; `Upland_Rice`: 126
  * Temperature Regime: High heat stress — $T_{max}$ up to 47.54°C (Mean: 35.36°C)
  * Rainfall: Deficit regime — Daily mean 1.32 mm (Max 63.26 mm)
* **Missing Value Rate**: 0.0% (Zero missing cells)
* **Duplicate Rows**: 0 exact duplicates; 0 (District, Date) key collisions
* **Modelling Suitability**: **Highly Suitable for Baseline Modelling** (Clean physical bounds, realistic thermal and precipitation extremes, 0 physics violations).

---

### Dataset 3: Terai-Teesta Zone
* **Filename**: [`terai_teesta_zone_2020_2025.csv`](file:///j:/Projects/Web/SIH_26086/SIH_26086/terai_teesta_zone_2020_2025.csv)
* **Agro-Climatic Zone**: Terai-Teesta Zone (Sub-Himalayan Foothills / Flood & Waterlogging Prone)
* **Estimated Data Provenance**: High-precipitation sub-Himalayan agromet series.
* **Temporal Coverage**: 2020-01-01 to 2025-12-31 (Daily continuous, 2,192 days).
* **Spatial Resolution & Entities**: 4 Districts:
  * *Jalpaiguri* (Lat: 26.54°N, Lon: 88.72°E) — 2,192 rows
  * *Alipurduar* (Lat: 26.49°N, Lon: 89.53°E) — 2,192 rows
  * *Cooch Behar* (Lat: 26.32°N, Lon: 89.45°E) — 2,192 rows
  * *Siliguri Foothills* (Lat: 26.71°N, Lon: 88.43°E) — 2,192 rows
* **Total Records / Rows**: 8,768 rows × 18 columns
* **File Size**: ~1.10 MB
* **Column Breakdown**: Same 17 baseline columns, with Column 18 replaced by:
  * `Waterlogging_Risk_Index` (Float, 0.00 to 1.00, Mean: 0.27, Std: 0.31): Hydrological accumulation index indicating soil saturation and flood inundation risk.
  * `Target_Crops` (Categorical): `Pineapple`: 5,334; `Tea`: 1,457; `Wetland_Rice`: 1,977
  * Rainfall Regime: Hyper-intense precipitation — Mean daily 6.82 mm, single-day peak of 389.64 mm, 30-day cumulative up to 1,153.55 mm.
* **Missing Value Rate**: 0.0% (Zero missing cells)
* **Duplicate Rows**: 0 exact duplicates; 0 (District, Date) key collisions
* **Modelling Suitability**: **Requires Preprocessing Before Modelling** (Contains 145 days with $T_{max} < T_{min}$ and an extreme artifact of $T_{max} = -9.29^\circ\text{C}$ in July due to unconstrained precipitation-cooling adjustment).

---

## 3. Comparative Inventory Matrix

| Attribute | Gangetic Alluvial | Red Laterite | Terai Teesta | Full Project Aggregation |
| :--- | :--- | :--- | :--- | :--- |
| **Total Rows** | 8,768 | 8,768 | 8,768 | **26,304** |
| **Total Districts** | 4 | 4 | 4 | **12 Districts** |
| **Time Span** | 2020 to 2025 (6 yr) | 2020 to 2025 (6 yr) | 2020 to 2025 (6 yr) | **2020-01-01 to 2025-12-31** |
| **Daily Completeness** | 100% | 100% | 100% | **100% (No missing dates)** |
| **Rainfall Feature** | 0.0 – 110.3 mm | 0.0 – 63.3 mm | 0.0 – 389.6 mm | **Span: 0.0 to 389.6 mm** |
| **Heat / Temp Range** | 8.0°C to 44.0°C | 8.8°C to 47.5°C | -9.3°C to 41.5°C | **Microclimate extremes captured** |
| **Teleconnections** | MJO (Phase/Amp), ENSO | MJO (Phase/Amp), ENSO | MJO (Phase/Amp), ENSO | **Synchronized global signals** |
| **Hydrological Memory** | 7d/30d Rain, Dry Streak | 7d/30d Rain, Dry Streak | 7d/30d Rain, Dry Streak | **Continuous rolling metrics** |
| **Current Target Col** | `Target_Crops` (3 classes) | `Target_Crops` (4 classes) | `Target_Crops` (3 classes) | **Crop labels (Must derive monsoon targets)** |
