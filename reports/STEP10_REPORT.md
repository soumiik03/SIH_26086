# STEP 10 — Scientific Validation Summary

## 1. Executive summary

The current red map is data-backed by two valid, very high applicable baseline outputs, not by a frontend color bug or a single global forecast. Bandapani's current values are 0.9773 for 5-day dry spell and 0.9971 for 7-day severe break. Both exceed the unchanged 0.75 VERY_HIGH threshold.

The other short-horizon values are not valid zeroes: onset and false onset are out of season in September; heavy rain and revival are unavailable because current 2026 atmospheric fields are absent. The 7–30 day outlook is unavailable for the same missing atmospheric feature matrix.

## 2. Current observed problem

The UI's prior `0%` display for missing values was a representation defect. The backend and frontend now preserve null/applicability states. The current regenerated artifact uses `UNAVAILABLE` for affected heads and unavailable advisory content.

## 3. Forecast trace

See `step10_forecast_trace.json` and `step10_forecast_trace.md`. The exact current vector includes 2026-09-08 rainfall, surface weather, MJO, IOD, Niño3.4, and derived rainfall features. Atmospheric fields are absent.

## 4. Feature distribution analysis

See `step10_feature_shift.md`. Current Niño3.4 is above the 2020–2023 training maximum; humidity and rainfall rolling values are high but within training ranges. This is a distribution-shift diagnostic, not an OOD determination.

## 5. Model output analysis

The baseline dry/severe artifacts produce raw XGBoost probabilities 0.9773238301 and 0.9971175194. The engine rounds to 0.9773 and 0.9971. The API preserves those decimals.

## 6. Calibration analysis

Atmospheric and horizon artifacts contain `CalibratedClassifierCV`/Platt metadata. The selected baseline dry/severe and IOD artifacts currently load as plain `XGBClassifier` objects. This contradicts repository claims that those selected artifacts are calibrated. It is a confirmed artifact provenance issue requiring a controlled model release, but no retraining/recalibration was performed because Step 10 forbids it.

## 7. 7–30 day horizon analysis

See `step10_horizon_trace.md`. All horizon events are null/UNAVAILABLE, not 0%. The models are not called when the required current atmospheric feature matrix is absent.

## 8. Risk thresholds

See `step10_risk_threshold_audit.md`. Thresholds were not changed. Missing heads are UNAVAILABLE; valid dry/severe outputs are VERY_HIGH.

## 9. Spatial analysis

See `step10_spatial_risk_diagnostic.csv` and `.md`. All 12 districts have distinct dry/severe values, and all Blocks/Panchayats inherit their own district state. No global probability or synthetic variation was found.

## 10. Advisory analysis

See `step10_advisory_trace.md`. Crop-neutral `/api/forecast` returns backend WAIT with crop-context-required semantics. Crop-specific advisory rules remain backend-owned and do not default missing inputs to SOW.

## 11. Current-data analysis

The common valid current date is 2026-09-08. Current raw weather exists through 2026-09-10; MJO through 2026-09-11; IOD availability through 2026-09-09; Niño3.4 availability through 2026-09-01. No stale 2025 atmospheric fallback is used for 2026.

## 12. Confirmed bugs

- Missing risk heads previously became LOW.
- Missing spatial advisory probabilities previously became zero inputs.
- Missing frontend probabilities previously rendered as 0%.
- Missing frontend advisory previously fell back to SOW.
- Existing tests incorrectly required all API probabilities to be non-null despite explicit applicability states.

## 13. Fixes

The first four defects were fixed; tests were updated to assert explicit unavailable states. Current artifacts were regenerated from the real 2026-09-08 reference date.

## 14. Expected behaviors

The red map is expected for the current valid dry/severe model outputs. September onset/false-onset unavailability is expected. Null horizon values are expected while atmospheric fields are unavailable.

## 15–16. Data and scientific limitations

Current atmospheric inputs are missing. The selected baseline/IOD artifacts have unresolved calibration provenance. Spatial probabilities remain district-inherited, not validated Panchayat-scale rainfall downscaling.

## 17. Test results

- `pytest -q`: **143 passed**, 3 environment/cache warnings.
- `python -m unittest discover -s tests -q`: **118 passed**.
- `npm run build`: **PASS**.

## 18. PS alignment

See `step10_ps_alignment.md`. Current atmospheric-dependent and 7–30 day capabilities are marked PARTIAL for the present data state; no unsupported COMPLETE claim is made for local downscaling.
