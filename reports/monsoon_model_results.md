# VARSHASENTINEL (SIH26086) — Monsoon Prediction Model Performance

**Evaluation Standard**: Out-of-Sample Temporal Walk-Forward Splitting
- **Training Period**: 2020–2023 (17,536 records across 12 districts)
- **Validation Period**: 2024 (4,392 records)
- **Test Period**: 2025 (4,376 records — Completely Unseen Out-of-Sample)

## 1. Primary Performance Table

| Target Event | Target Column | Total Pos Rate | Val Brier | Test Brier | Test ROC-AUC | Test PR-AUC | Test F1 | Test Recall |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Monsoon Onset (14-Day Window)** | `target_onset_window_14d` | 4.11% | 0.0483 | 0.0499 | 0.9568 | 0.3931 | 0.4403 | 0.5222 |
| **False Onset Surge Failure** | `target_false_onset_flag` | 0.32% | 0.0043 | 0.0059 | 0.9182 | 0.0344 | 0.0 | 0.0 |
| **5-Day Dry Spell / Break (14-Day Lead)** | `target_dry_spell_5d_14d` | 31.15% | 0.0632 | 0.0641 | 0.9778 | 0.9518 | 0.8801 | 0.9696 |
| **7-Day Severe Break (21-Day Lead)** | `target_dry_spell_7d_21d` | 27.51% | 0.0859 | 0.0693 | 0.9753 | 0.9394 | 0.8349 | 0.9614 |
| **Heavy Rainfall / Flood Hazard (7-Day Lead)** | `target_heavy_rain_7d` | 6.25% | 0.0855 | 0.0895 | 0.9268 | 0.3835 | 0.5282 | 0.7589 |
| **Dry Spell Revival (7-Day Lead)** | `target_revival_7d` | 4.6% | 0.07 | 0.0708 | 0.9257 | 0.4386 | 0.4764 | 0.5353 |

## 2. Metric Interpretations & Scientific Highlights

1. **Brier Score (Lower is Better)**: Measures probability calibration error. A Brier score below 0.10 indicates high reliability in probabilistic hazard forecasting.
2. **PR-AUC vs ROC-AUC**: For highly imbalanced events (e.g. False Onset or Heavy Rainfall), Precision-Recall AUC (PR-AUC) provides the true measure of operational alert fidelity without being distorted by the vast number of non-event true negatives.
3. **Zero Temporal Leakage**: Unlike previous unstratified 93–99% random shuffle scores, these metrics represent genuine forward-looking predictive generalization on the out-of-sample 2025 monsoon season.
