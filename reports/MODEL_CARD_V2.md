# VARSHASENTINEL Model Card V2

V2 uses train 2020–2023, 2024 calibration/selection, and untouched 2025 testing with a 37-day temporal purge. Features are as-of local weather, ENSO/IOD/MJO, atmospheric circulation where historically available, seasonality, coordinates, and district/zone controls. Current 2026 atmospheric-dependent inference is unavailable when source fields are absent.

## onset
- Model: `logistic_local`
- Calibration: `isotonic`
- Baseline decision: `MODEL_SELECTED`
- Test Brier: `0.1187`
- Test ROC-AUC: `0.7632`
- Test PR-AUC: `0.3143`
- Release: `PRODUCTION_V2`
- Spatial resolution: district-inherited; not local downscaling

## false_onset
- Model: `xgb_full`
- Calibration: `sigmoid`
- Baseline decision: `BASELINE_PREFERRED`
- Test Brier: `0.0850`
- Test ROC-AUC: `0.4940`
- Test PR-AUC: `0.0878`
- Release: `BASELINE_PREFERRED`
- Spatial resolution: district-inherited; not local downscaling

## dry_spell_5d
- Model: `logistic_local`
- Calibration: `isotonic`
- Baseline decision: `MODEL_SELECTED`
- Test Brier: `0.1387`
- Test ROC-AUC: `0.8351`
- Test PR-AUC: `0.9367`
- Release: `PRODUCTION_V2`
- Spatial resolution: district-inherited; not local downscaling

## severe_break_7d
- Model: `logistic_local`
- Calibration: `sigmoid`
- Baseline decision: `MODEL_SELECTED`
- Test Brier: `0.1341`
- Test ROC-AUC: `0.8790`
- Test PR-AUC: `0.9432`
- Release: `PRODUCTION_V2`
- Spatial resolution: district-inherited; not local downscaling

## heavy_rain
- Model: `logistic_local`
- Calibration: `sigmoid`
- Baseline decision: `BASELINE_PREFERRED`
- Test Brier: `0.0443`
- Test ROC-AUC: `0.9308`
- Test PR-AUC: `0.4232`
- Release: `BASELINE_PREFERRED`
- Spatial resolution: district-inherited; not local downscaling

## revival
- Model: `xgb_full`
- Calibration: `sigmoid`
- Baseline decision: `MODEL_SELECTED`
- Test Brier: `0.0433`
- Test ROC-AUC: `0.9316`
- Test PR-AUC: `0.5420`
- Release: `PRODUCTION_V2`
- Spatial resolution: district-inherited; not local downscaling

## dry_spell
- Model: `logistic_local`
- Calibration: `sigmoid`
- Baseline decision: `MODEL_SELECTED`
- Test Brier: `0.1520`
- Test ROC-AUC: `0.8477`
- Test PR-AUC: `0.9211`
- Release: `PRODUCTION_V2`
- Spatial resolution: district-inherited; not local downscaling

## dry_spell
- Model: `logistic_local`
- Calibration: `sigmoid`
- Baseline decision: `MODEL_SELECTED`
- Test Brier: `0.1434`
- Test ROC-AUC: `0.8644`
- Test PR-AUC: `0.9285`
- Release: `PRODUCTION_V2`
- Spatial resolution: district-inherited; not local downscaling

## dry_spell
- Model: `logistic_local`
- Calibration: `sigmoid`
- Baseline decision: `MODEL_SELECTED`
- Test Brier: `0.1194`
- Test ROC-AUC: `0.8897`
- Test PR-AUC: `0.9582`
- Release: `PRODUCTION_V2`
- Spatial resolution: district-inherited; not local downscaling

## severe_break
- Model: `logistic_local`
- Calibration: `sigmoid`
- Baseline decision: `MODEL_SELECTED`
- Test Brier: `0.1304`
- Test ROC-AUC: `0.8864`
- Test PR-AUC: `0.8926`
- Release: `PRODUCTION_V2`
- Spatial resolution: district-inherited; not local downscaling

## severe_break
- Model: `logistic_local`
- Calibration: `sigmoid`
- Baseline decision: `MODEL_SELECTED`
- Test Brier: `0.1306`
- Test ROC-AUC: `0.8849`
- Test PR-AUC: `0.8653`
- Release: `PRODUCTION_V2`
- Spatial resolution: district-inherited; not local downscaling

## severe_break
- Model: `logistic_local`
- Calibration: `sigmoid`
- Baseline decision: `MODEL_SELECTED`
- Test Brier: `0.1183`
- Test ROC-AUC: `0.9029`
- Test PR-AUC: `0.9256`
- Release: `PRODUCTION_V2`
- Spatial resolution: district-inherited; not local downscaling

## heavy_rain
- Model: `xgb_full`
- Calibration: `isotonic`
- Baseline decision: `MODEL_SELECTED`
- Test Brier: `0.0464`
- Test ROC-AUC: `0.9335`
- Test PR-AUC: `0.4809`
- Release: `PRODUCTION_V2`
- Spatial resolution: district-inherited; not local downscaling

## heavy_rain
- Model: `logistic_local`
- Calibration: `sigmoid`
- Baseline decision: `MODEL_SELECTED`
- Test Brier: `0.0439`
- Test ROC-AUC: `0.9349`
- Test PR-AUC: `0.4206`
- Release: `PRODUCTION_V2`
- Spatial resolution: district-inherited; not local downscaling

## heavy_rain
- Model: `xgb_atmospheric`
- Calibration: `isotonic`
- Baseline decision: `BASELINE_PREFERRED`
- Test Brier: `0.0478`
- Test ROC-AUC: `0.9469`
- Test PR-AUC: `0.5379`
- Release: `BASELINE_PREFERRED`
- Spatial resolution: district-inherited; not local downscaling

## revival
- Model: `xgb_full`
- Calibration: `sigmoid`
- Baseline decision: `MODEL_SELECTED`
- Test Brier: `0.0508`
- Test ROC-AUC: `0.9423`
- Test PR-AUC: `0.6452`
- Release: `PRODUCTION_V2`
- Spatial resolution: district-inherited; not local downscaling

## revival
- Model: `xgb_atmospheric`
- Calibration: `sigmoid`
- Baseline decision: `MODEL_SELECTED`
- Test Brier: `0.0372`
- Test ROC-AUC: `0.9421`
- Test PR-AUC: `0.4694`
- Release: `PRODUCTION_V2`
- Spatial resolution: district-inherited; not local downscaling

## revival
- Model: `xgb_atmospheric`
- Calibration: `isotonic`
- Baseline decision: `MODEL_SELECTED`
- Test Brier: `0.0382`
- Test ROC-AUC: `0.9419`
- Test PR-AUC: `0.5536`
- Release: `PRODUCTION_V2`
- Spatial resolution: district-inherited; not local downscaling
