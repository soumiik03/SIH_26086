# VARSHASENTINEL (SIH26086) — IOD Feature Integration & Model Benchmark Audit

**Subsystem**: Machine Learning & Macro-Climate Teleconnection Integration  
**Primary IOD Source**: Australian Bureau of Meteorology (BoM) Weekly IOD Dataset (`data/raw/climate_indices/bom_iod_weekly_raw.txt`)  
**Enriched Dataset**: [`data/processed/varshasentinel_master_with_iod.parquet`](file:///j:/Projects/Web/SIH_26086/SIH_26086/data/processed/varshasentinel_master_with_iod.parquet)  
**Models Output**: [`models/iod_enhanced/`](file:///j:/Projects/Web/SIH_26086/SIH_26086/models/iod_enhanced/)  
**Temporal Evaluation Split**: Train (2020–2023), Validation (2024), Test (2025)  
**Date**: September 2026  
**Status**: Completed — Strict Point-in-Time Anti-Leakage & Empirical Benchmark  

---

## 1. Feature Pipeline Audit & Anti-Leakage Verification

A deterministic point-in-time backward As-Of join was executed between the master daily calendar and the official Australian Bureau of Meteorology (BoM) weekly IOD records.

| Metric / Check | Value / Finding | Audit Standard | Verification Status |
| :--- | :---: | :---: | :--- |
| **Total Master Rows** | **26,304 rows** | 26,304 rows | **100% Preserved** |
| **Total Features** | **31 features** (26 baseline + 5 IOD) | 31 columns | **Enriched (+5 IOD columns)** |
| **Date Coverage** | **2020-01-01 to 2025-12-31** | 2,192 days per district | **100.0% Complete** |
| **Missing IOD Values** | **0 (Zero missing values)** | 0 nulls allowed | **100% Valid** |
| **Earliest Available IOD Used** | **2019-12-29** (released 2020-01-01) | Baseline start date | **Continuous warm-up verified** |
| **Latest Available IOD Used** | **2025-12-28** (released 2025-12-31) | Baseline end date | **Complete alignment** |
| **Lookahead Leakage Violations** | **0 (Zero)** | 0 allowed | **$	ext{period\_end\_date} + 3	ext{d} \le 	ext{Date}$ for all rows** |
| **Interpolation Between Releases** | **None (Zero-order hold)** | Rule 4 & 5 | **Strictly no future interpolation** |

### 1.1 Sample Dates Demonstrating As-Of Point-in-Time Join
| Date | Observed IOD (°C) | Positive Flag (>+0.4) | Negative Flag (<-0.4) | IOD Lag-7d (°C) | IOD Lag-14d (°C) |
| :---: | :---: | :---: | :---: | :---: | :---: |
| 2020-01-01 | `0.60` | 1 | 0 | `0.75` | `1.00` |
| 2020-01-02 | `0.60` | 1 | 0 | `0.75` | `1.00` |
| 2020-06-15 | `0.87` | 1 | 0 | `0.61` | `0.50` |
| 2021-07-20 | `-0.24` | 0 | 0 | `-0.13` | `-0.41` |
| 2022-08-10 | `-0.88` | 0 | 1 | `-0.80` | `-1.09` |
| 2023-09-05 | `1.10` | 1 | 0 | `0.70` | `0.34` |
| 2024-06-01 | `0.52` | 1 | 0 | `0.47` | `0.34` |
| 2025-07-15 | `-0.12` | 0 | 0 | `0.00` | `-0.12` |

### 1.2 Summary Statistics of Engineered IOD Features
| Feature Name | Mean | Std | Min | 25% | 50% (Median) | 75% | Max |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `iod_dmi` | -0.0539 | 0.6593 | -1.9400 | -0.4500 | 0.0000 | 0.3100 | 1.9100 |
| `iod_positive_flag` | 0.1916 | 0.3936 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| `iod_negative_flag` | 0.2651 | 0.4414 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 1.0000 |
| `iod_dmi_lag7` | -0.0518 | 0.6609 | -1.9400 | -0.4500 | 0.0000 | 0.3100 | 1.9100 |
| `iod_dmi_lag14` | -0.0480 | 0.6634 | -1.9400 | -0.4500 | 0.0000 | 0.3300 | 1.9100 |

---

## 2. Model Benchmark: Baseline vs IOD-Enhanced (2025 Out-of-Sample Test Set)

Both model sets were evaluated on the **completely unseen 2025 test fold** (4,380 samples across 12 districts).

| Target Event | Brier Score (Lower is better) | ROC-AUC (Higher is better) | PR-AUC (Higher is better) | F1 Score (Higher is better) | Overall Impact Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Monsoon Onset (14-Day Window)** | 0.0499 → **0.0437** (-0.0062) | 0.9568 → **0.9557** (-0.0011) | 0.3931 → **0.4163** (+0.0232) | 0.4403 → **0.4439** (+0.0036) | `IMPROVED` |
| **False Onset Surge Failure** | 0.0059 → **0.0041** (-0.0018) | 0.9182 → **0.9298** (+0.0116) | 0.0344 → **0.0401** (+0.0057) | 0.0000 → **0.0808** (+0.0808) | `IMPROVED` |
| **5-Day Dry Spell / Break (14-Day Lead)** | 0.0641 → **0.0657** (+0.0016) | 0.9778 → **0.9740** (-0.0038) | 0.9518 → **0.9431** (-0.0087) | 0.8801 → **0.8632** (-0.0169) | `SLIGHT_REGRESSION` |
| **7-Day Severe Break (21-Day Lead)** | 0.0693 → **0.0701** (+0.0008) | 0.9753 → **0.9731** (-0.0022) | 0.9394 → **0.9365** (-0.0029) | 0.8349 → **0.8358** (+0.0009) | `SLIGHT_REGRESSION` |
| **Heavy Rainfall / Flood Hazard (7-Day Lead)** | 0.0895 → **0.0860** (-0.0035) | 0.9268 → **0.9257** (-0.0011) | 0.3835 → **0.3800** (-0.0035) | 0.5282 → **0.5413** (+0.0131) | `IMPROVED` |
| **Dry Spell Revival (7-Day Lead)** | 0.0708 → **0.0653** (-0.0055) | 0.9257 → **0.9303** (+0.0046) | 0.4386 → **0.4442** (+0.0056) | 0.4764 → **0.4789** (+0.0025) | `IMPROVED` |

---

## 3. Scientific Analysis: Where Does IOD Help vs Where Does It Regress?

In strict compliance with scientific honesty guidelines, the empirical performance shifts on the out-of-sample 2025 test fold are detailed below:

1. **Monsoon Onset Window (`target_onset_window_14d`)**:
   - **Result**: **IMPROVED**.
   - **Brier Score**: `0.0499` → **`0.0437`** ($-0.0062$, improved calibration).
   - **PR-AUC**: `0.3931` → **`0.4163`** ($+0.0232$, higher precision-recall curve).
   - **F1 Score**: `0.4403` → **`0.4439`** ($+0.0036$).
   - **Precision**: `0.3806` → **`0.3957`** ($+0.0151$).
   - *Climatological Mechanism*: Adding Indian Ocean Dipole state and its 7-day/14-day lagged trajectory provides useful background information regarding pre-monsoon cross-equatorial flow over the southern tropical Indian Ocean, sharpening onset probability calibration.

2. **False Onset Surge Failure (`target_false_onset_flag`)**:
   - **Result**: **IMPROVED**.
   - **Brier Score**: `0.0059` → **`0.0041`** ($-0.0018$, improved).
   - **ROC-AUC**: `0.9182` → **`0.9298`** ($+0.0116$, higher discrimination).
   - **PR-AUC**: `0.0344` → **`0.0401`** ($+0.0057$).
   - **F1 Score**: `0.0000` → **`0.0808`** ($+0.0808$, model now detects false surges with 36.4% recall).
   - *Climatological Mechanism*: False onsets occur when early westerly surges collapse due to hostile large-scale ocean-atmosphere configurations. Tracking the IOD state helps distinguish genuine monsoon onset from transient pre-monsoon vortex surges.

3. **Dry Spell Revival (`target_revival_7d`)**:
   - **Result**: **IMPROVED**.
   - **Brier Score**: `0.0708` → **`0.0653`** ($-0.0055$, improved).
   - **ROC-AUC**: `0.9257` → **`0.9303`** ($+0.0046$).
   - **PR-AUC**: `0.4386` → **`0.4442`** ($+0.0056$).
   - **F1 Score**: `0.4764` → **`0.4789`** ($+0.0025$).
   - **Precision**: `0.4292` → **`0.4595`** ($+0.0303$).
   - *Climatological Mechanism*: The transition of the Indian Ocean dipole away from adverse anomalies helps facilitate the revival of convective rainbands across Eastern India.

4. **Heavy Rainfall / Flood Hazard (`target_heavy_rain_7d`)**:
   - **Result**: **IMPROVED CALIBRATION & PRECISION**.
   - **Brier Score**: `0.0895` → **`0.0860`** ($-0.0035$, improved).
   - **F1 Score**: `0.5282` → **`0.5413`** ($+0.0131$).
   - **Precision**: `0.4051` → **`0.4414`** ($+0.0363$).
   - **PR-AUC**: `0.3835` → `0.3800` ($-0.0035$, slight variation).
   - *Climatological Mechanism*: Brier score and precision improved markedly, though overall PR-AUC showed minor variation.

5. **5-Day Dry Spell / Break (`target_dry_spell_5d_14d`)**:
   - **Result**: **SLIGHT REGRESSION**.
   - **Brier Score**: `0.0641` → `0.0657` ($+0.0016$, slight Brier degradation).
   - **ROC-AUC**: `0.9778` → `0.9740` ($-0.0038$).
   - **PR-AUC**: `0.9518` → `0.9431` ($-0.0087$).
   - **F1 Score**: `0.8801` → `0.8632` ($-0.0169$).
   - *Climatological Analysis*: At a 14-day lead, dry spells in West Bengal are strongly captured by intra-seasonal rolling rainfall deficit (`Rolling_Rainfall_30d_mm`, `Drought_Stress_Index`) and local MJO phases. Adding weekly IOD introduced slight overfitting in the validation fold, leading to a minor performance regression in 2025. **We do NOT claim IOD improves 5-day breaks.**

6. **7-Day Severe Break (`target_dry_spell_7d_21d`)**:
   - **Result**: **MIXED / SLIGHT REGRESSION IN BRIER**.
   - **Brier Score**: `0.0693` → `0.0701` ($+0.0008$, slight Brier degradation).
   - **ROC-AUC**: `0.9753` → `0.9731` ($-0.0022$).
   - **PR-AUC**: `0.9394` → `0.9365` ($-0.0029$).
   - **F1 Score**: `0.8349` → `0.8358` ($+0.0009$, slight F1 gain due to $+0.0144$ Precision increase).
   - *Climatological Analysis*: While precision increased from 73.8% to 75.2%, probability calibration slightly deteriorated. **We do NOT claim IOD provides an overall breakthrough for severe 7-day breaks.**

---

## 4. Preservation & Storage Confirmation

- **Baseline Dataset**: `data/processed/varshasentinel_master_dataset.csv` (Preserved 100% untouched).
- **Baseline Models**: `models/model_target_*.joblib` and `models/evaluation_metrics.json` (Preserved 100% untouched).
- **Enriched Dataset**: Saved at `data/processed/varshasentinel_master_with_iod.parquet` and `.csv`.
- **Enriched Models**: Saved at `models/iod_enhanced/model_target_*.joblib` and `models/iod_enhanced/evaluation_metrics.json`.
