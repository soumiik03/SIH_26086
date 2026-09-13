# Step 8 PS alignment

| SIH26086 Requirement | Status | Evidence |
|---|---|---|
| False-onset prediction | COMPLETE | Production false-onset artifact replayed over 2025 test rows. |
| Monsoon onset prediction | COMPLETE | Existing onset head evaluated in the same replay. |
| Dry-spell prediction | COMPLETE | Existing 5-day dry-spell head evaluated. |
| Break prediction | COMPLETE | Existing 7-day severe-break head evaluated. |
| Probabilistic forecast | COMPLETE | Probabilities come from production calibrated artifacts and remain bounded. |
| Historical validation | COMPLETE | 4,380 real 2025 rows evaluated against existing targets. |
| Agricultural decision support | COMPLETE | Step 7 deterministic advisory runs after each forecast. |
| SOW / WAIT decision | COMPLETE | Advisory action and rule ID are recorded. |
| Explainable advisory | COMPLETE | Rule, reasons, validity, and risk factors are preserved. |
| 7–30 day outlook | COMPLETE | Existing statistical outlook is replayed and returned per case. |
| Temporal validation | COMPLETE | Train 2020–2023, calibration 2024, replay/test 2025. |
| No future leakage | COMPLETE | Target/future fields are excluded before prediction and revealed afterward only. |
| Reproducible replay | COMPLETE | Cached deterministic batch replay with recorded artifacts and configuration. |
| Real historical data | COMPLETE | Existing production feature/target parquet is used. |
| No fabricated cases | COMPLETE | Fixed criteria; unavailable Case A is reported rather than invented. |
