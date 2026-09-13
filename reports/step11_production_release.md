# Step 11 Production Release Gate

A per-event release is `PRODUCTION_V2` only when leakage controls, temporal separation, schema checks, calibration, probability range, validation selection, and test Brier competitiveness pass. Otherwise it remains `EXPERIMENTAL_V2` or `BASELINE_PREFERRED`. No V1 artifact is overwritten.

- **onset**: `PRODUCTION_V2`; selected `logistic_local`; baseline decision `MODEL_SELECTED`.
- **false_onset**: `BASELINE_PREFERRED`; selected `xgb_full`; baseline decision `BASELINE_PREFERRED`.
- **dry_spell_5d**: `PRODUCTION_V2`; selected `logistic_local`; baseline decision `MODEL_SELECTED`.
- **severe_break_7d**: `PRODUCTION_V2`; selected `logistic_local`; baseline decision `MODEL_SELECTED`.
- **heavy_rain**: `BASELINE_PREFERRED`; selected `logistic_local`; baseline decision `BASELINE_PREFERRED`.
- **revival**: `PRODUCTION_V2`; selected `xgb_full`; baseline decision `MODEL_SELECTED`.
- **dry_spell**: `PRODUCTION_V2`; selected `logistic_local`; baseline decision `MODEL_SELECTED`.
- **dry_spell**: `PRODUCTION_V2`; selected `logistic_local`; baseline decision `MODEL_SELECTED`.
- **dry_spell**: `PRODUCTION_V2`; selected `logistic_local`; baseline decision `MODEL_SELECTED`.
- **severe_break**: `PRODUCTION_V2`; selected `logistic_local`; baseline decision `MODEL_SELECTED`.
- **severe_break**: `PRODUCTION_V2`; selected `logistic_local`; baseline decision `MODEL_SELECTED`.
- **severe_break**: `PRODUCTION_V2`; selected `logistic_local`; baseline decision `MODEL_SELECTED`.
- **heavy_rain**: `PRODUCTION_V2`; selected `xgb_full`; baseline decision `MODEL_SELECTED`.
- **heavy_rain**: `PRODUCTION_V2`; selected `logistic_local`; baseline decision `MODEL_SELECTED`.
- **heavy_rain**: `BASELINE_PREFERRED`; selected `xgb_atmospheric`; baseline decision `BASELINE_PREFERRED`.
- **revival**: `PRODUCTION_V2`; selected `xgb_full`; baseline decision `MODEL_SELECTED`.
- **revival**: `PRODUCTION_V2`; selected `xgb_atmospheric`; baseline decision `MODEL_SELECTED`.
- **revival**: `PRODUCTION_V2`; selected `xgb_atmospheric`; baseline decision `MODEL_SELECTED`.