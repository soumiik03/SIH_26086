# STEP 11 MODEL REBUILD REPORT

## Executive summary

V2 was rebuilt in an isolated `models/v2/` directory with leakage-safe future targets, temporal purge gaps, historical baselines, logistic and XGBoost candidates, 2024-only calibration, untouched 2025 testing, probability distributions, reliability diagnostics, and versioned manifests.

## Results

- `onset`: `PRODUCTION_V2`, selected `logistic_local`, test Brier `0.1187` versus climatology `0.1276`.
- `false_onset`: `BASELINE_PREFERRED`, selected `xgb_full`, test Brier `0.0850` versus climatology `0.0861`.
- `dry_spell_5d`: `PRODUCTION_V2`, selected `logistic_local`, test Brier `0.1387` versus climatology `0.1400`.
- `severe_break_7d`: `PRODUCTION_V2`, selected `logistic_local`, test Brier `0.1341` versus climatology `0.1410`.
- `heavy_rain`: `BASELINE_PREFERRED`, selected `logistic_local`, test Brier `0.0443` versus climatology `0.0606`.
- `revival`: `PRODUCTION_V2`, selected `xgb_full`, test Brier `0.0433` versus climatology `0.0625`.
- `dry_spell`: `PRODUCTION_V2`, selected `logistic_local`, test Brier `0.1520` versus climatology `0.1623`.
- `dry_spell`: `PRODUCTION_V2`, selected `logistic_local`, test Brier `0.1434` versus climatology `0.1552`.
- `dry_spell`: `PRODUCTION_V2`, selected `logistic_local`, test Brier `0.1194` versus climatology `0.1297`.
- `severe_break`: `PRODUCTION_V2`, selected `logistic_local`, test Brier `0.1304` versus climatology `0.1322`.
- `severe_break`: `PRODUCTION_V2`, selected `logistic_local`, test Brier `0.1306` versus climatology `0.1391`.
- `severe_break`: `PRODUCTION_V2`, selected `logistic_local`, test Brier `0.1183` versus climatology `0.1273`.
- `heavy_rain`: `PRODUCTION_V2`, selected `xgb_full`, test Brier `0.0464` versus climatology `0.0663`.
- `heavy_rain`: `PRODUCTION_V2`, selected `logistic_local`, test Brier `0.0439` versus climatology `0.0602`.
- `heavy_rain`: `BASELINE_PREFERRED`, selected `xgb_atmospheric`, test Brier `0.0478` versus climatology `0.0686`.
- `revival`: `PRODUCTION_V2`, selected `xgb_full`, test Brier `0.0508` versus climatology `0.0758`.
- `revival`: `PRODUCTION_V2`, selected `xgb_atmospheric`, test Brier `0.0372` versus climatology `0.0491`.
- `revival`: `PRODUCTION_V2`, selected `xgb_atmospheric`, test Brier `0.0382` versus climatology `0.0609`.

## Limitations

The current 2026 source lacks atmospheric fields; no atmospheric or 7–30 day probability is fabricated. Spatial output remains `NONE_DISTRICT_INHERITED`. See the detailed Step 11 reports for target leakage, calibration, temporal validation, distributions, routing, and release decisions.
