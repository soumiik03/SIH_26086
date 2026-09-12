# VARSHASENTINEL (SIH26086) — Historical IOD / DMI Dataset Audit & Integration Protocol

**Subsystem**: Macro-Climatological Teleconnection Foundations  
**Target Outlook**: 7–30 Day Probabilistic Monsoon Prediction  
**Status**: Authoritative Scientific Data Ingestion & Audit Complete  
**Date**: September 2026  

---

## 1. Executive Summary & Provenance

To satisfy the SIH26086 scientific requirement for coupled macro-climate drivers without fabricating or interpolating synthetic values, an authoritative search was conducted across international meteorological and oceanographic agencies (**NOAA**, **Australian Bureau of Meteorology (BoM)**, and **JAMSTEC**).

Two official datasets were identified, acquired, and preserved in their raw original formats:

1. **Primary Operational Source**: **Australian Bureau of Meteorology (BoM)** Weekly Indian Ocean Dipole (IOD) Index.
   - *Source URL*: `http://www.bom.gov.au/clim_data/IDCK000072/iod_1.txt`
   - *Local Raw File*: [`data/raw/climate_indices/bom_iod_weekly_raw.txt`](file:///j:/Projects/Web/SIH_26086/SIH_26086/data/raw/climate_indices/bom_iod_weekly_raw.txt) (21,979 bytes)
2. **Benchmark Historical Source**: **NOAA Physical Sciences Laboratory (PSL)** Monthly Dipole Mode Index (DMI) based on Met Office HadISST1.1.
   - *Source URL*: `https://psl.noaa.gov/data/timeseries/month/data/dmi.had.long.csv` (and `.data`)
   - *Local Raw Files*: [`data/raw/climate_indices/noaa_dmi_hadisst_monthly_raw.csv`](file:///j:/Projects/Web/SIH_26086/SIH_26086/data/raw/climate_indices/noaa_dmi_hadisst_monthly_raw.csv) (39,650 bytes) and [`data/raw/climate_indices/noaa_dmi_hadisst_monthly_raw.data`](file:///j:/Projects/Web/SIH_26086/SIH_26086/data/raw/climate_indices/noaa_dmi_hadisst_monthly_raw.data) (19,861 bytes)

---

## 2. Dataset Specifications & Verification Matrix

| Dimension / Attribute | Australian Bureau of Meteorology (BoM) | NOAA Physical Sciences Laboratory (PSL) |
| :--- | :--- | :--- |
| **Index Name** | Indian Ocean Dipole (IOD) Index / DMI | Dipole Mode Index (DMI) |
| **Institution** | Australian Bureau of Meteorology (BoM) | NOAA PSL / Met Office Hadley Centre |
| **Underlying SST Dataset** | BoM Operational OISST / ACCESS-S analysis | HadISST1.1 (1° $\times$ 1° reconstructed SST) |
| **Definition / Formula** | $\text{SST}_{\text{anom}}(\text{WTIO}) - \text{SST}_{\text{anom}}(\text{SETIO})$ | $\text{SST}_{\text{anom}}(\text{WTIO}) - \text{SST}_{\text{anom}}(\text{SETIO})$ |
| **Western Pole (WTIO)** | 50°E to 70°E, 10°S to 10°N | 50°E to 70°E, 10°S to 10°N |
| **Eastern Pole (SETIO)** | 90°E to 110°E, 10°S to 0° (Equator) | 90°E to 110°E, 10°S to 0° (Equator) |
| **Temporal Resolution** | **Weekly** (7-day periods ending Sunday) | **Monthly** (Calendar month averages) |
| **Published Date Range** | **2008-07-28 to 2026-09-06** (Active) | **1870-01-01 to 2026-05-01** (Active) |
| **Total Records** | **943 consecutive weeks** | **1,884 months** (1,877 valid, 7 future placeholders) |
| **Missing Values** | **0 (Zero missing values)** | **0 in 1870–2026-05** (-9999 for unreleased months) |
| **Units** | Degrees Celsius (°C) anomaly | Degrees Celsius (°C) anomaly |
| **Phase Thresholds** | Positive: $> +0.4^\circ\text{C}$; Negative: $< -0.4^\circ\text{C}$ | Positive: $> +0.4^\circ\text{C}$; Negative: $< -0.4^\circ\text{C}$ |
| **Mean / Std Dev** | Mean: $+0.049^\circ\text{C}$, Std: $0.540^\circ\text{C}$ | Mean: $-0.232^\circ\text{C}$, Std: $0.346^\circ\text{C}$ |
| **Observed Min / Max** | Min: $-1.94^\circ\text{C}$, Max: $+1.93^\circ\text{C}$ | Min: $-1.634^\circ\text{C}$, Max: $+1.279^\circ\text{C}$ |

---

## 3. Comparison Against Master Dataset Coverage

The existing master modeling dataset (`data/processed/varshasentinel_master_dataset.csv`) contains:
- **Date Range**: `2020-01-01` to `2025-12-31` (2,192 consecutive days per district).
- **Districts Covered**: 12 West Bengal districts (26,304 total rows).
- **Existing Climate Drivers**: `Nino34_Anomaly` (daily/monthly), `MJO_Phase`, `MJO_Amplitude` (daily).

### Coverage Alignment Results:
1. **BoM Weekly IOD Dataset**:
   - Master dataset period requires: `2020-01-01` to `2025-12-31`.
   - BoM records span: `2019-12-30` to `2026-01-04` (**314 continuous, unbroken weeks**).
   - **Coverage**: **100.0% complete**. Zero missing weeks or missing values.
2. **NOAA PSL Monthly DMI Dataset**:
   - Master dataset period requires: `2020-01-01` to `2025-12-31`.
   - NOAA records span: `2020-01-01` to `2025-12-01` (**72 continuous, unbroken calendar months**).
   - **Coverage**: **100.0% complete**. Zero missing months or missing values.

---

## 4. Assessment of Temporal Resolution for 7–30 Day Outlooks

### 4.1 Physical Oceanic Dynamics vs Atmospheric Timescales
- Unlike atmospheric waves (such as the MJO, which exhibit rapid phase transitions on 3–5 day timescales and are measured daily), the Indian Ocean Dipole is an **ocean-basin coupled mode**.
- Sea Surface Temperature anomalies in the tropical Indian Ocean are governed by high-thermal-inertia upper-ocean heat content, thermocline depth variations, and equatorial ocean wave dynamics (Kelvin and Rossby waves).
- As established in climatological literature (Saji et al., 1999; Webster et al., 1999; Ashok et al., 2001), tropical Indian Ocean SST anomalies exhibit high temporal persistence, with 14-day to 30-day autocorrelation exceeding $0.85$.
- Consequently, international operational centers (BoM, NOAA CPC, ECMWF) do not monitor or forecast daily fluctuating DMI noise; they utilize **weekly running means or monthly indices** to isolate the authentic low-frequency oceanic signal.

### 4.2 Why BoM Weekly IOD is Superior to Monthly NOAA DMI for VARSHASENTINEL
1. **Resolution Alignment with Sub-Seasonal Window (7–30 Days)**:
   - A weekly index updates every 7 days. This allows the model to register dipole intensification or decay during the critical 14-to-30-day pre-onset and active monsoon phases.
2. **Publication Latency & Operational Usability**:
   - **BoM Weekly**: Published every Tuesday/Wednesday for the week ending Sunday (latency: **2–3 days**).
   - **NOAA Monthly**: Published around the 15th to 20th of the *following* month (latency: **15–20 days**).
   - A monthly latency of 15–20 days would render real-time June monsoon onset prediction severely lagged (June SST anomaly would only be known in mid-July). In contrast, the BoM weekly product is operationally actionable for a 7–30 day outlook.

**Conclusion**: The **BoM Weekly IOD dataset** is selected as the primary operational driver, with NOAA Monthly serving as a historical baseline benchmark.

---

## 5. Leakage-Safe Merging Protocol (As-of Forward-Fill)

To prevent lookahead data leakage in both historical model evaluation and real-time inference, the merging protocol must strictly respect the publication timeline.

### 5.1 The Anti-Leakage Rules:
1. **No Lookahead Alignment**:
   - A weekly DMI value representing the week from day $t-6$ to day $t$ cannot be assumed known on day $t-6$ or day $t-3$.
   - It is only available at time $t + \text{latency}$ (where operational latency $\delta \approx 2\text{ days}$).
2. **Deterministic "As-Of" Join (Point-in-Time)**:
   - For each calendar date $D$ in the master dataset:
     $$\text{IOD\_DMI}(D) = \text{DMI}_{\text{weekly}} \quad \text{where} \quad \text{end\_date} + \delta \le D$$
   - The value is held constant (**zero-order hold / forward fill**) until the next published week becomes available.
3. **No Interpolation or Smoothing Across Gaps**:
   - Per requirement 5, values between weekly releases must **NOT** be linearly or spline-interpolated using future points, as that would introduce future information into past dates.

---

## 6. Proposed Feature Architecture for Future Ingestion

When approved for integration into the feature matrix, the following leakage-safe features should be generated:

1. `iod_dmi_observed`: The most recent published weekly DMI anomaly (°C).
2. `iod_phase_cat`: Categorical phase:
   - `+1` (Positive IOD: $\text{DMI} > +0.4^\circ\text{C}$) — associated with enhanced monsoon rainfall and delayed withdrawal.
   - `0` (Neutral IOD: $-0.4 \le \text{DMI} \le +0.4^\circ\text{C}$) — standard baseline.
   - `-1` (Negative IOD: $\text{DMI} < -0.4^\circ\text{C}$) — associated with suppressed monsoon rainfall and frequent break spells.
3. `iod_dmi_trend_14d`: $\Delta \text{DMI}_{14d} = \text{DMI}_{t} - \text{DMI}_{t-14}$ (measures rapid oceanic warming or cooling in the western/eastern poles).
4. `enso_iod_interaction`: Product interaction term:
   $$\text{interaction} = \text{Nino34\_Anomaly} \times \text{iod\_dmi\_observed}$$
   *(Captures non-linear compounding events, such as canonical El Niño + Positive IOD or La Niña + Negative IOD).*

---

## 7. Compliance Verification

- `WEST_BENGAL.shp`: **100% UNTOUCHED**.
- `Village_Gram_Panchayat_Mapping_...xlsx`: **100% UNTOUCHED**.
- `west_bengal_blocks.geojson`: **100% UNTOUCHED**.
- `west_bengal_panchayats_safe.geojson`: **100% UNTOUCHED**.
- Synthetic boundaries or fake coordinates: **ZERO GENERATED**.
- Interpolation / fabrication of missing dates: **ZERO APPLIED**.
- Models retrained: **NONE (Frozen per instructions)**.
