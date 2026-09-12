# VARSHASENTINEL (SIH26086) — Data Quality & Integrity Report

**Project**: VARSHASENTINEL — Hyperlocal Monsoon Intelligence System for West Bengal  
**Lead Engineer**: Lead ML & Climate-Data Engineer  
**Audit Date**: September 2026  
**Status**: Forensic Audit Completed  

---

## 1. Quality Audit Summary

A forensic automated audit of all 26,304 records across the three agro-climatic datasets was executed. The audit evaluated:
1. Null/Missing value incidence
2. Duplicate row and compound key (`District`, `Date`) uniqueness
3. Mathematical correctness of derived hydrometeorological features
4. Physical and thermodynamic consistency of surface parameters ($T_{max} \ge T_{min}$, boundary conditions for Relative Humidity, Solar Radiation, and Rainfall)

```
╔══════════════════════════════════════════════════════════════════════════════════════╗
║ TOTAL RECORDS AUDITED: 26,304 (8,768 per file × 3 files)                             ║
║ COMPLETENESS: 100.0% (0 null / 0 empty cells)                                        ║
║ DUPLICATE KEYS: 0 collisions (Every District has strictly 2,192 consecutive days)   ║
║ MATHEMATICAL INTEGRITY (Rolling 7d & 30d): 100.0% Match (0 calculation errors)      ║
║ DRY SPELL LOGIC: 100.0% Match with IMD 2.5mm Rainy-Day Criterion                     ║
║ PHYSICAL INCONSISTENCIES: 149 rows with Tmax < Tmin (Terai: 145, Gangetic: 4)         ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
```

---

## 2. Deep-Dive Quality Findings by Parameter

### 2.1 Missing Values & Compound Keys
* **Result**: **0 missing values across all 18 features**.
* **Key Integrity**: The compound key `(District, Date)` has zero collisions. All 12 districts span every single calendar day between January 1, 2020 and December 31, 2025 without a single dropped day (leap years 2020 and 2024 are correctly populated with 366 days).

### 2.2 Mathematical Verification of Derived Rolling Features
* **Rolling 7-Day Rainfall (`Rolling_Rainfall_7d_mm`)**: Verified against $\sum_{k=0}^{6} Rainfall_{t-k}$. Mismatches: **0 / 26,304 (100% exact match)**.
* **Rolling 30-Day Rainfall (`Rolling_Rainfall_30d_mm`)**: Verified against $\sum_{k=0}^{29} Rainfall_{t-k}$. Mismatches: **0 / 26,304 (100% exact match)**.
* **Dry Spell Days Streak (`Dry_Spell_Days_Streak`)**: 
  * Audited against the official **India Meteorological Department (IMD)** agrometeorological standard: A "Rainy Day" is strictly defined as daily rainfall $\ge 2.5\text{ mm}$.
  * Trace rainfall ($< 2.5\text{ mm}$) does NOT terminate a dry spell streak.
  * Formula: 
    $$\text{Streak}_t = \begin{cases} 0 & \text{if } Rainfall_t \ge 2.5\text{ mm} \\ \text{Streak}_{t-1} + 1 & \text{if } Rainfall_t < 2.5\text{ mm} \end{cases}$$
  * **Result**: **0 mismatches across all 26,304 rows** when evaluated with the IMD $2.5\text{ mm}$ criterion. The feature calculation is scientifically and mathematically verified.

### 2.3 Thermodynamic Inversions & Physical Anomalies

#### Anomaly A: Thermodynamic Inversions ($T_{max} < T_{min}$)
By thermodynamic definition, the daily maximum air temperature ($T_{max}$) must be strictly greater than or equal to the daily minimum air temperature ($T_{min}$).
* **Red Laterite Zone**: **0 violations** (Physically pristine).
* **Gangetic Alluvial Zone**: **4 violations** ($0.045\%$ of zone data):
  1. `Purba Bardhaman` (2021-07-16): $T_{max} = 30.23^\circ\text{C}, T_{min} = 31.33^\circ\text{C}$ ($\Delta = -1.10^\circ\text{C}$)
  2. `Nadia` (2022-06-02): $T_{max} = 24.97^\circ\text{C}, T_{min} = 27.13^\circ\text{C}$ ($\Delta = -2.16^\circ\text{C}$)
  3. `Murshidabad` (2021-06-12): $T_{max} = 23.66^\circ\text{C}, T_{min} = 27.02^\circ\text{C}$ ($\Delta = -3.36^\circ\text{C}$)
  4. `Murshidabad` (2022-08-21): $T_{max} = 27.42^\circ\text{C}, T_{min} = 28.92^\circ\text{C}$ ($\Delta = -1.50^\circ\text{C}$)
* **Terai-Teesta Zone**: **145 violations** ($1.65\%$ of zone data).
  * Clustered during intense monsoon months (June–September) during heavy rainfall days.
  * Inversion magnitude reaches up to $9.24^\circ\text{C}$ (e.g. 2022-08-07 in Jalpaiguri: $T_{max} = 17.53^\circ\text{C}, T_{min} = 26.77^\circ\text{C}$).

#### Anomaly B: Severe Unclipped Outlier in Terai-Teesta
* **Record**: Row 6027 in [`terai_teesta_zone_2020_2025.csv`](file:///j:/Projects/Web/SIH_26086/SIH_26086/terai_teesta_zone_2020_2025.csv)
* **Date**: `2024-07-01`, District: `Cooch_Behar`
* **Values**: $T_{max} = -9.29^\circ\text{C}$, $T_{min} = 26.87^\circ\text{C}$, $\text{Rainfall} = 389.64\text{ mm}$, $RH = 88.3\%$.
* **Diagnostic Cause**: In downscaling or synthesis scripts, evaporative cooling and cloud radiative forcing are frequently modeled as a negative linear or power function of precipitation ($T_{max}^{adj} = T_{max}^{base} - \alpha \times \text{Rainfall}$). When extreme precipitation ($389.64\text{ mm}$) occurred, the absence of a physical bounding guardrail ($\max(T_{max}^{adj}, T_{min})$) forced $T_{max}$ into deep negative territory ($-9.29^\circ\text{C}$) in tropical lowland Bengal in midsummer.

---

## 3. Readiness Status Classification

Based on these findings, the datasets are classified as follows:

| Dataset | Status | Detailed Rationale & Action Required |
| :--- | :---: | :--- |
| [`red_laterite_zone_2020_2025.csv`](file:///j:/Projects/Web/SIH_26086/SIH_26086/red_laterite_zone_2020_2025.csv) | ✅ **Ready** | 100% complete, zero mathematical errors, zero thermodynamic inversions, clean distribution extremes. Ready for feature store integration. |
| [`gangetic_alluvial_zone_2020_2025.csv`](file:///j:/Projects/Web/SIH_26086/SIH_26086/gangetic_alluvial_zone_2020_2025.csv) | ⚠️ **Needs Preprocessing** | 99.95% clean. 4 isolated days require temperature inversion correction (swap or set $T_{max} = \max(T_{max}, T_{min})$ or interpolate from adjacent days). |
| [`terai_teesta_zone_2020_2025.csv`](file:///j:/Projects/Web/SIH_26086/SIH_26086/terai_teesta_zone_2020_2025.csv) | ⚠️ **Needs Preprocessing** | 145 temperature inversion days and 1 extreme negative artifact ($-9.29^\circ\text{C}$) require systematic physical rectification (clamping diurnal temperature range $\text{DTR} \ge 0.5^\circ\text{C}$). |
| **Monsoon Event Ground Truth Targets** | ❌ **Missing** | The 5 required prediction targets (`onset`, `false_onset`, `dry_spell_5d`, `heavy_rainfall`, `revival`) are NOT present in any dataset. They must be algorithmically synthesized using meteorological ground truth logic. |
| **Indian Ocean Dipole (IOD / DMI)** | ❌ **Missing** | Crucial climate driver of Indian summer monsoon variability missing from all 3 files. Must be integrated. |

---

## 4. Remediation Protocol for Preprocessing

Before using these datasets in model training:
1. **Physical Temperature Clamping**:
   For any record where $T_{max} < T_{min}$:
   $$\text{Mean\_Temp} = \frac{T_{max} + T_{min}}{2}$$
   $$T_{min}^{clean} = \min(T_{max}, T_{min})$$
   $$T_{max}^{clean} = \max(T_{max}, T_{min}) + \epsilon \quad (\text{where } \epsilon = 0.5^\circ\text{C})$$
2. **Sub-Zero Outlier Removal**:
   For Cooch Behar on 2024-07-01 ($T_{max} = -9.29^\circ\text{C}$), set $T_{max} = T_{min} + 1.2^\circ\text{C} = 28.07^\circ\text{C}$ (reflecting typical heavily overcast monsoon daytime suppression in North Bengal).
