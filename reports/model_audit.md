# VARSHASENTINEL (SIH26086) — Comprehensive Model Audit Report

**Project**: VARSHASENTINEL — Hyperlocal Monsoon Intelligence System for West Bengal  
**Lead Engineer**: Lead ML & Climate-Data Engineer  
**Audit Date**: September 2026  
**Document**: `reports/model_audit.md`  
**Status**: Completed ML Architecture & Code Audit  

---

## 1. Executive Summary

This report provides a forensic audit of the existing machine learning implementation across the three regional notebooks:
* [`gangetic_alluvial_zone.ipynb`](file:///j:/Projects/Web/SIH_26086/SIH_26086/gangetic_alluvial_zone.ipynb)
* [`red_laterite_zone.ipynb`](file:///j:/Projects/Web/SIH_26086/SIH_26086/red_laterite_zone.ipynb)
* [`terai_teesta_zone.ipynb`](file:///j:/Projects/Web/SIH_26086/SIH_26086/terai_teesta_zone.ipynb)

The audit evaluates the mathematical algorithms, input features, target formulation, validation methodology, leakage risks, and persistence status. It establishes an exact roadmap to reuse the valid tabular machine learning infrastructure while re-orienting the prediction objectives from static crop classification to the **6 core probabilistic monsoon events** mandated by SIH26086.

---

## 2. Answers to the 10 Core Audit Questions

### 1. Which model/algorithm is currently being used?
Two supervised machine learning classification algorithms are implemented and benchmarked in parallel across all three notebooks:
1. **`sklearn.ensemble.RandomForestClassifier()`**: An ensemble of 100 decorrelated decision trees using bootstrap aggregating (bagging) with Gini impurity splitting.
2. **`xgboost.XGBClassifier()`**: A gradient boosted decision tree (GBDT) ensemble optimizing multi-class logarithmic loss via sequential gradient descent in functional space.
*Both models run with default hyperparameter configurations.*

### 2. Which features are being used?
Across all three zones, exactly **14 features** are fed into the feature matrix $\mathbf{X}$:
1. `District` (Categorical, encoded to integers $0, 1, 2, 3$ via `LabelEncoder()`)
2. `Latitude` (Float, centroid latitude)
3. `Longitude` (Float, centroid longitude)
4. `Rainfall_Observed_mm` (Float, daily 24h precipitation)
5. `Tmax_C` (Float, daily maximum temperature)
6. `Tmin_C` (Float, daily minimum temperature)
7. `Relative_Humidity_pct` (Float, surface relative humidity)
8. `Solar_Radiation_MJm2` (Float, surface solar irradiance)
9. `MJO_Phase` (Integer, 1 through 8)
10. `MJO_Amplitude` (Float, Real-time Multivariate MJO strength)
11. `Nino34_Anomaly` (Float, Oceanic Niño Index SST anomaly)
12. `Dry_Spell_Days_Streak` (Integer, consecutive days with rainfall $< 2.5\text{ mm}$)
13. `Rolling_Rainfall_7d_mm` (Float, 7-day backward cumulative precipitation)
14. `Rolling_Rainfall_30d_mm` (Float, 30-day backward cumulative precipitation)

*Note on Dropped Columns*:
* All notebooks drop `Zone` (invariant constant) and `Date` (string timestamp).
* Notebooks also drop their respective zone index: `Active_Crop_Cycle` (Gangetic), `Drought_Stress_Index` (Red Laterite), and `Waterlogging_Risk_Index` (Terai-Teesta).

### 3. What exactly is the current target?
The target variable is `Target_Crops` — a **discrete categorical multi-class label** representing the dominant crop active in the field on that calendar day:
* **Gangetic Alluvial**: 3 Classes — `Potato` (0), `Jute` (1), `Aman_Rice` (2)
* **Red Laterite**: 4 Classes — `Pulses_Arhar` (0), `Millets_Ragi` (1), `Maize` (2), `Upland_Rice` (3)
* **Terai-Teesta**: 3 Classes — `Pineapple` (0), `Tea` (1), `Wetland_Rice` (2)

### 4. Where is the trained model saved?
**The models are NOT saved to disk anywhere.**
* There are **no serialization calls** (`joblib.dump()`, `pickle.dump()`, `xgb.save_model()`, or `onnx.export()`) in any notebook.
* The models existed strictly in volatile memory during the execution of the Google Colab session.
* Only the textual outputs of `accuracy_score` and `classification_report` were saved in the `.ipynb` execution metadata.

### 5. What metrics were obtained?
The existing models achieved near-perfect evaluation scores on the random test splits:

| Agro-Climatic Zone | Algorithm | Accuracy | Macro Avg F1 | Weighted Avg F1 |
| :--- | :--- | :---: | :---: | :---: |
| **Gangetic Alluvial** | Random Forest | **93.33%** | 0.93 | 0.93 |
| | XGBoost | **95.90%** | 0.96 | 0.96 |
| **Red Laterite** | Random Forest | **97.38%** | 0.98 | 0.97 |
| | XGBoost | **98.35%** | 0.97 | 0.98 |
| **Terai-Teesta** | Random Forest | **99.43%** | 0.99 | 0.99 |
| | XGBoost | **99.77%** | 1.00 | 1.00 |

### 6. What train/test splitting method was used?
The code used `train_test_split(X, y, test_size=0.2, random_state=45)`.
* This is an **unstratified, random shuffle split** dividing 8,768 records into:
  * Training set: **7,014 records (80%)**
  * Test set: **1,754 records (20%)**
* Observations from all 6 years (2020 through 2025) are thoroughly shuffled together.

### 7. Is there any possible data leakage?
**YES. Severe Temporal and Autoregressive Data Leakage exists in the current evaluation:**
1. **Temporal Shuffling Leakage**: In a continuous time-series, day $t-1$ and day $t+1$ leak directly into the training set while day $t$ is evaluated in the test set. Atmospheric processes possess high persistence and memory; random shuffling allows the tree models to "interpolate" between yesterday and tomorrow rather than "forecast".
2. **Rolling Window Leakage**: Features `Rolling_Rainfall_7d_mm` and `Rolling_Rainfall_30d_mm` look backward 7 and 30 days. When day $t$ is in the test set, day $t-1$ in the training set already contains 6 of the same 7 days and 29 of the same 30 days. This creates massive informational leakage between train and test distributions.
3. **Calendar-Target Determinism**: In Gangetic Alluvial, the crops follow strict calendar months (e.g., Nov–Feb is 100% Potato, Mar–Jun is 100% Jute, Jul–Oct is 100% Aman Rice). Because temperature ($T_{max}, T_{min}$) and solar radiation follow seasonal solar cycles, the model simply learns the calendar month from temperature, producing artificial accuracies ($>95\%$) that do not reflect true meteorological predictive power.

### 8. What prediction output does the current model produce?
The current model invokes `y_pred = model.predict(X_test)`.
* **Output Format**: A 1-D array of discrete integer class labels ($[0, 1, 2]$ or $[0, 1, 2, 3]$).
* **Semantic Meaning**: "Given today's weather, which crop is cultivated?"
* **Gap**: It produces zero probabilistic hazard estimates and zero forward-looking event predictions.

### 9. Which parts of the existing model can be reused?
1. **Algorithm Architecture**: `XGBClassifier` and `RandomForestClassifier` are the optimal, industry-standard algorithms for tabular climate features. They capture non-linear thresholds (e.g. convective triggers, RH thresholds) without requiring massive neural network parameters.
2. **Feature Curation & Pipeline**: The existing 14 features (`Rainfall`, `Tmax`, `Tmin`, `RH`, `Solar`, `MJO_Phase`, `MJO_Amplitude`, `Nino34_Anomaly`, `Dry_Spell_Days_Streak`, `Rolling_Rainfall_7d/30d`, `Coordinates`) represent physical meteorological parameters that should be preserved.
3. **Regional Zonation Concept**: Structuring the models by the 3 distinct agro-ecological zones (Alluvial, Laterite, Terai) accurately reflects the microclimatic realities of West Bengal.
4. **Agro-Advisory Integration**: The existing crop classifier can be preserved as the downstream **Agro-Advisory / Crop Impact Layer** of VARSHASENTINEL (mapping forecasted monsoon events to crop damage risk).

### 10. Which parts must change to satisfy SIH26086?
1. **Prediction Objective**: Re-orient targets from static crop classification to the **6 core monsoon events**.
2. **Validation Rigor**: Replace random `train_test_split` with **Temporal Walk-Forward Splitting** (Train on 2020–2023, Validate on 2024, Test on out-of-sample 2025) or `TimeSeriesSplit`.
3. **Inference Output**: Switch from deterministic `.predict()` to calibrated probabilities via `.predict_proba()`.
4. **Model Serialization**: Save all trained model artifacts to disk (`models/zone_event_xgb.joblib`) with versioning.
5. **Feature Augmentation**: Ingest missing IOD ($DMI$), Diurnal Temperature Range ($DTR$), and cyclical $\sin/\cos$ calendar/MJO encodings.

---

## 3. Comparison Against Required Probabilistic Outputs

| Required VARSHASENTINEL Output | Supported by Existing Model? | Current Capability | Necessary Transformation |
| :--- | :---: | :--- | :--- |
| **$P(\text{onset})$** | ❌ No | Predicts crop labels only | Train binary classifier on `target_onset_window_14d` using `.predict_proba()` |
| **$P(\text{false onset})$** | ❌ No | Predicts crop labels only | Train conditional binary classifier on early surges collapsing within 10 days |
| **$P(\text{dry spell 5d})$** | ❌ No | Measures current streak only; does not forecast | Train forward-looking binary classifier on `target_dry_spell_5d_14d` |
| **$P(\text{dry spell 7d})$** | ❌ No | Measures current streak only; does not forecast | Train forward-looking binary classifier on `target_dry_spell_7d_21d` |
| **$P(\text{heavy rainfall})$** | ❌ No | Measures daily rainfall; does not forecast | Train binary hazard classifier on $\ge 64.5\text{ mm}$ (or 3d $\ge 150\text{ mm}$) |
| **$P(\text{revival})$** | ❌ No | Predicts crop labels only | Train conditional classifier for break termination during active dry spells |

### Probabilistic Support Assessment:
* **Can the existing algorithms output probabilities?**
  **YES.** Both `RandomForestClassifier` and `XGBClassifier` natively support `.predict_proba(X)`.
  * In `RandomForestClassifier`, `.predict_proba()` computes the fraction of trees voting for class $k$.
  * In `XGBClassifier`, setting `objective='binary:logistic'` outputs the true sigmoid probability:
    $$P(Y=1|\mathbf{x}) = \frac{1}{1 + e^{-\hat{y}(\mathbf{x})}}$$
  * When paired with `sklearn.calibration.CalibratedClassifierCV` (Platt scaling or Isotonic regression), these models produce calibrated, statistically reliable risk probabilities ($0.0\%$ to $100.0\%$).

---

## 4. Architectural Transformation Blueprint

```
EXISTING WORKFLOW (Crop Recommendation)
┌───────────────────────────┐
│ 14 Daily Features         │
│ (Temp, Rain, MJO, ENSO)   │
└─────────────┬─────────────┘
              ▼
┌───────────────────────────┐
│ Random Train/Test Split   │ ◄── [LEAKAGE: Shuffled Time-Series]
└─────────────┬─────────────┘
              ▼
┌───────────────────────────┐
│ RFC / XGBoost Classifier  │
└─────────────┬─────────────┘
              ▼
┌───────────────────────────┐
│ Hard Labels: .predict()   │ ──► "Potato" / "Jute" / "Aman_Rice"
└───────────────────────────┘

───────────────────────────────────────────────────────────────────

VARSHASENTINEL TARGET WORKFLOW (Monsoon Hazard Intelligence)
┌─────────────────────────────────────────────────────────────────┐
│ Enhanced Feature Store: 14 Base Features + DTR + VPD + IOD +   │
│ Cyclical DOY/MJO Encodings + 3d/7d/15d/30d Memory              │
└────────────────────────────────┬────────────────────────────────┘
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ Temporal Walk-Forward Split (Train: 2020-2023, Test: 2024-2025) │
└────────────────────────────────┬────────────────────────────────┘
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ Multi-Head Calibrated XGBoost & Random Forest Classifiers       │
└────────────────────────────────┬────────────────────────────────┘
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ Probabilistic Risk Vector: .predict_proba()                     │
│ ├── P(Monsoon Onset within 14d)                                │
│ ├── P(False Onset Surge Failure)                               │
│ ├── P(5-Day Dry Spell / Break in 7-14d)                        │
│ ├── P(7-Day Severe Break in 7-21d)                             │
│ ├── P(Heavy Rainfall / Flood Hazard in 7d)                     │
│ └── P(Dry Spell Revival within 7d)                             │
└────────────────────────────────┬────────────────────────────────┘
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│ Downstream Agro-Advisory (Existing Crop Models Mapped to Risk)  │
└─────────────────────────────────────────────────────────────────┘
```
