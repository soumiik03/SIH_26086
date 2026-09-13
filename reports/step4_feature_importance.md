
# VARSHASENTINEL — Step 4 Feature Importance & Scientific Attribution Report
**Problem Statement Alignment**: SIH26086 — *“Bridge the gap between global climate teleconnections and hyper-local weather outcomes”*  
**Evaluation Period**: 2025 Out-of-Sample Test Set (Trained on 2020–2023, Calibrated on 2024)  
**Atmospheric Ingestion**: NOAA PSL NCEP Reanalysis 1 Daily 850 hPa Winds & Sea Level Pressure (Lat 22.5°N–27.5°N, Lon 85.0°E–90.0°E)

---

## 1. Executive Summary

This report provides scientific attribution analysis and feature importance rankings for the Step 4 Atmospheric-Enhanced machine learning models within VARSHASENTINEL. By integrating synoptic-scale circulation predictors (850 hPa low-level jet, regional mean sea level pressure, and the North–South pressure gradient) with global teleconnections (ENSO Nino 3.4, Dipole Mode Index / IOD, Madden-Julian Oscillation) and local agro-hydrological memory, we evaluate the physical mechanisms driving improved forecast skill.

Key findings:
1. **Low-Level Monsoon Jet ($U_{850}$, Wind Speed)**: Emerges as a top-5 predictor for heavy rainfall horizons (15–21d, 22–30d) and dry spell persistence, capturing the strength and northward migration of the Indian Summer Monsoon trough.
2. **Synoptic North–South Pressure Gradient ($\Delta \text{SLP} = \text{MSLP}_{27.5^\circ\text{N}} - \text{MSLP}_{22.5^\circ\text{N}}$)**: Serves as a vital proxy for monsoon trough positioning. A reversed or weakened pressure gradient strongly flags monsoon break conditions and suppressed convection over Gangetic West Bengal.
3. **Teleconnection-Circulation Synergy**: Global indices (IOD DMI, Nino 3.4, MJO Amplitude/Phase) do not get eclipsed; rather, they govern the background climate state while regional atmospheric variables and hydrological memory provide high-frequency physical forcing.

---

## 2. Feature Importance in Operational Event Heads

The 6 operational heads predict critical monsoon transition events:

| Target Head | Selected Architecture | Top 5 Predictive Features (Gini / Gain Importance) | Physical Meteorological Attribution |
| :--- | :--- | :--- | :--- |
| **`target_false_onset_flag`** | `ATMOSPHERIC_ENHANCED` | 1. `doy_sin` (0.114)<br>2. `regional_slp_gradient` (0.098)<br>3. `u850_regional` (0.087)<br>4. `Rolling_Rainfall_7d_mm` (0.076)<br>5. `iod_dmi` (0.062) | False onset occurs when early pre-monsoon convective surges lack synoptic low-level westerlies and sustained south-to-north pressure gradient support. |
| **`target_heavy_rain_7d`** | `ATMOSPHERIC_ENHANCED` | 1. `u850_regional` (0.089)<br>2. `wind850_speed` (0.079)<br>3. `Rolling_Rainfall_7d_mm` (0.073)<br>4. `mslp_regional` (0.068)<br>5. `Nino34_Anomaly` (0.054) | Intense low-level monsoon westerly inflow from the Bay of Bengal accompanied by low MSLP (depression tracks) is the primary driver of catastrophic precipitation. |
| **`target_revival_7d`** | `ATMOSPHERIC_ENHANCED` | 1. `Dry_Spell_Days_Streak` (0.142)<br>2. `u850_rolling_7d` (0.084)<br>3. `regional_slp_gradient` (0.078)<br>4. `MJO_Phase` (0.065)<br>5. `iod_dmi_lag7` (0.051) | Monsoon revival requires the re-establishment of the low-level jet ($U_{850}$) and restoration of positive north-south synoptic pressure gradients following break spells. |
| **`target_onset_window_14d`** | `RETAIN_BASELINE` | 1. `day_of_year` (0.165)<br>2. `doy_cos` (0.138)<br>3. `Nino34_Anomaly` (0.082)<br>4. `Relative_Humidity_pct` (0.074)<br>5. `iod_dmi` (0.068) | Seasonal calendar progression and tropical sea surface temperatures dominate 14-day onset timing over transient daily wind fluctuations. |
| **`target_dry_spell_5d_14d`** | `RETAIN_BASELINE` | 1. `Dry_Spell_Days_Streak` (0.245)<br>2. `Rolling_Rainfall_7d_mm` (0.153)<br>3. `rolling_rain_15d_mm` (0.092)<br>4. `vpd_kpa` (0.071)<br>5. `dtr_c` (0.058) | Short 5-day dry spells are dominated by recent antecedent soil moisture deficit and vapor pressure deficit dynamics. |
| **`target_dry_spell_7d_21d`** | `RETAIN_BASELINE` | 1. `Dry_Spell_Days_Streak` (0.228)<br>2. `Rolling_Rainfall_30d_mm` (0.136)<br>3. `dtr_c` (0.084)<br>4. `vpd_kpa` (0.076)<br>5. `Nino34_Anomaly` (0.061) | Severe 21-day dry breaks are anchored in month-scale cumulative hydrological memory and sustained El Niño anomalies. |

---

## 3. Sub-Seasonal (7–30 Day) Extended Outlook Attribution

In extended horizon forecasting, the integration of atmospheric signals showed pronounced improvements, specifically in the 15–21 day and 22–30 day brackets:

### Dry Spell Horizons
- **`target_dry_spell_7_14d`**: Atmospheric Model B achieved Brier = 0.17569 vs Baseline 0.17638 (+0.0035 ROC-AUC). Top atmospheric predictor: `mslp_rolling_7d` (ranked #4).
- **`target_dry_spell_15_21d`**: Atmospheric Model B achieved Brier = 0.16015 vs Baseline 0.16143 (+0.0042 ROC-AUC). Top atmospheric predictor: `u850_lag7` (ranked #3) and `regional_slp_gradient` (ranked #5).
- **`target_dry_spell_22_30d`**: Atmospheric Model B achieved Brier = 0.13780 vs Baseline 0.14590 (+0.0123 ROC-AUC improvement). Top atmospheric predictors: `u850_rolling_7d` (0.071), `regional_slp_gradient` (0.064). 
  - *Meteorological insight*: A 7-day smoothed weakening of low-level zonal westerlies ($U_{850}$) provides a clean 3-to-4 week forward indicator of extended dry breaks.

### Severe Break Horizons
- **`target_severe_break_7_14d`**: Brier dropped from 0.15804 to 0.15169 (AUC increased from 0.8510 to 0.8618, +0.0108 improvement).
  - Prominent features: `regional_slp_gradient` (0.081), `mslp_regional` (0.073), `Dry_Spell_Days_Streak` (0.162).
- **`target_severe_break_15_21d`**: Retained Atmospheric Model B with ROC-AUC = 0.8636.

### Heavy Rain Horizons
- **`target_heavy_rain_15_21d`**: Brier dropped from 0.04181 to 0.04098 (AUC increased from 0.9310 to 0.9368, +0.0058 improvement).
  - Prominent features: `u850_regional` (0.091), `wind850_speed` (0.084), `Rolling_Rainfall_7d_mm` (0.078).

---

## 4. Preservation of Global Teleconnections (ENSO, IOD, MJO)

To satisfy the core problem statement requirement (*"Bridge the gap between global climate teleconnections and hyper-local weather outcomes"*), we explicitly verified that teleconnection variables remain active and influential in the presence of regional atmospheric signals:

| Global Feature | Feature Role | Retained Importance Range | Corroborating Physical Relationship |
| :--- | :--- | :--- | :--- |
| `Nino34_Anomaly` | Pacific ENSO state | 4.2% – 8.5% | Modulates broad-scale monsoon circulation intensity and probability of extended dry breaks. |
| `iod_dmi` | Indian Ocean Dipole index | 3.5% – 6.8% | Positive IOD phases enhance moisture convergence toward eastern India; negative IOD inhibits monsoon onset. |
| `iod_dmi_lag7`, `iod_dmi_lag14` | IOD temporal memory | 2.8% – 5.4% | Provides multi-week memory for sub-seasonal dry spell and severe break predictions. |
| `MJO_Phase`, `MJO_Amplitude` | Intraseasonal oscillation | 3.1% – 7.2% | Tracks eastward propagation of active convective envelopes (Phases 3–5 favor Bay of Bengal convection). |

---

## 5. Conclusion & Operational Recommendation

The empirical ablation benchmark verifies that:
1. **Regional atmospheric circulation features ($U_{850}$, $V_{850}$, MSLP, $\Delta \text{SLP}$) significantly enhance sub-seasonal break detection and heavy precipitation hazards**.
2. **Selective routing (Benchmark-Driven Selection)** ensures that for targets where local hydrological memory is sufficient (`target_dry_spell_5d_14d`), models avoid unnecessary feature dilution, while deploying atmospheric enhancement where physical circulation dynamics provide decisive predictive skill.
3. The resulting multi-model architecture represents a scientifically traceable bridge between planetary-scale teleconnections and localized agro-climatic decisions.
