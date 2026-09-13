# Step 10 Forecast Model and Data Forensic Audit

## Executive finding

The current red map is not caused by one global probability, a frontend percentage conversion, or missing values becoming high risk. The regenerated current artifact shows district-specific dry-spell and severe-break probabilities, and every district has a valid high applicable state for at least those two heads.

The current result has four separate causes:

1. September is outside the onset and false-onset seasonal windows.
2. The 2026 current source contains surface weather and climate-index data but no atmospheric circulation fields.
3. Therefore atmospheric operational heads and all 7–30 day horizon heads are unavailable, not 0%.
4. The two baseline dry/break models do produce very high raw probabilities, which legitimately classify as `VERY_HIGH` under the unchanged thresholds.

## Production routing and artifacts

| Event | Production artifact | Schema | Calibration wrapper present in artifact |
| --- | --- | ---: | --- |
| Onset | `models/iod_enhanced/target_onset_window_14d_xgb.joblib` | 31 | No; XGBClassifier |
| False onset | `models/atmospheric_enhanced/target_false_onset_flag_xgb.joblib` | 40 | Yes; CalibratedClassifierCV |
| Dry spell 5d | `models/target_dry_spell_5d_14d_xgb.joblib` | 26 | No; XGBClassifier |
| Severe break 7d | `models/target_dry_spell_7d_21d_xgb.joblib` | 26 | No; XGBClassifier |
| Heavy rain | `models/atmospheric_enhanced/target_heavy_rain_7d_xgb.joblib` | 40 | Yes; CalibratedClassifierCV |
| Revival | `models/atmospheric_enhanced/target_revival_7d_xgb.joblib` | 40 | Yes; CalibratedClassifierCV |

All 12 horizon artifacts are dictionaries containing a `CalibratedClassifierCV` model, a raw base-model path, `platt_sigmoid` metadata, and a 38-field atmospheric feature schema. The production engine passes the exact metadata-defined order.

The selected baseline and IOD artifacts conflict with repository claims that all production outputs are calibrated: the saved artifacts are plain XGBoost classifiers. This is a confirmed model-artifact/calibration provenance issue, but it was not repaired because the Step 10 rules prohibit retraining or recalibrating production models without an approved model release.

## Feature construction

`AsOfFeatureBuilder` uses `data/raw/weather/wb_districts_2026_daily.csv`, BoM MJO, BoM IOD with a three-day publication lag, and NOAA CPC Niño 3.4 monthly data. The common valid 2026 date is 2026-09-08. The 2026 weather file runs through 2026-09-10; MJO runs through 2026-09-11; IOD availability runs through 2026-09-09; Niño availability runs through 2026-09-01.

The 2026 weather file has no `u850`, `v850`, wind, MSLP, or atmospheric-gradient columns. The builder correctly leaves those features missing. The engine only retains historical atmospheric defaults for non-2026 observations, so the current 2026 path does not copy 2025 atmospheric values.

## Calibration and scaling

- Engine probabilities are bounded to `[0,1]` and rounded to four decimals.
- API serialization preserves decimal probabilities and nulls.
- Frontend percentage rendering multiplies once for presentation only.
- Risk classification uses decimal probabilities before frontend formatting.
- No double percentage conversion was found.
- No null-to-zero conversion remains in the audited frontend graph/probability components.

## Horizon result

The horizon models are not reached for the current record because `prepare_horizon_feature_vector()` returns `None` when atmospheric fields are missing. The engine writes `UNAVAILABLE` applicability and null probability for every horizon/event. This is correct handling of unavailable input, not a valid all-zero forecast.

## Root-cause classification

| Observation | Classification |
| --- | --- |
| 97.73% dry-spell / 99.71% severe-break | Expected model output, subject to calibration provenance limitation |
| Red overall map | Expected from valid district-inherited high dry/severe states |
| Onset/false onset null in September | Expected seasonal applicability |
| Atmospheric heads unavailable | Data limitation: missing 2026 atmospheric source fields |
| Horizon heads unavailable | Data limitation propagated correctly |
| Previously missing head risk shown as LOW | Confirmed implementation bug; fixed |
| Previously missing advisory treated as normal/zero inputs | Confirmed implementation bug; fixed |
| Previously null graph values displayed as 0% | Confirmed UI representation bug; fixed |
| Baseline/IOD artifacts lack calibration wrapper | Confirmed artifact provenance issue; not repaired under no-retraining rule |

## Fixes made

- Explicit `UNAVAILABLE` risk classification and map color.
- API risk levels recomputed from preserved probabilities rather than stale artifact head labels.
- Null advisory inputs no longer become zero or normal operations.
- Frontend no longer converts null forecast values to 0% or missing advisory to SOW.
- Current artifacts regenerated from the real 2026-09-08 as-of date.
- Regression tests updated and added.

## Scientific limitations

- Current 2026 atmospheric data are absent, so no atmospheric operational or horizon probability can be scientifically generated.
- Baseline/IOD production artifact provenance must be resolved by a controlled model-release process before calling those outputs calibrated.
- Spatial output remains district-inherited; it is not validated local rainfall downscaling.
