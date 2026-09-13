# Step 11 Model Routing

| Event | Horizon | Selected model | Decision | Calibration | Validation Brier | Test Brier | Test PR-AUC | Test ROC-AUC | Release | Artifact |
|---|---|---|---|---|---:|---:|---:|---:|---|---|
| onset | - | logistic_local | MODEL_SELECTED | isotonic | 0.0137 | 0.1187 | 0.3143 | 0.7632 | PRODUCTION_V2 | `models\v2\onset\model.joblib` |
| false_onset | - | xgb_full | BASELINE_PREFERRED | sigmoid | 0.0356 | 0.0850 | 0.0878 | 0.4940 | BASELINE_PREFERRED | `models\v2\false_onset\model.joblib` |
| dry_spell_5d | - | logistic_local | MODEL_SELECTED | isotonic | 0.0887 | 0.1387 | 0.9367 | 0.8351 | PRODUCTION_V2 | `models\v2\dry_spell_5d\model.joblib` |
| severe_break_7d | - | logistic_local | MODEL_SELECTED | sigmoid | 0.1218 | 0.1341 | 0.9432 | 0.8790 | PRODUCTION_V2 | `models\v2\severe_break_7d\model.joblib` |
| heavy_rain | - | logistic_local | BASELINE_PREFERRED | sigmoid | 0.0569 | 0.0443 | 0.4232 | 0.9308 | BASELINE_PREFERRED | `models\v2\heavy_rain\model.joblib` |
| revival | - | xgb_full | MODEL_SELECTED | sigmoid | 0.0428 | 0.0433 | 0.5420 | 0.9316 | PRODUCTION_V2 | `models\v2\revival\model.joblib` |
| dry_spell | 7_14d | logistic_local | MODEL_SELECTED | sigmoid | 0.1102 | 0.1520 | 0.9211 | 0.8477 | PRODUCTION_V2 | `models\v2\horizon_7_14d\dry_spell\model.joblib` |
| dry_spell | 15_21d | logistic_local | MODEL_SELECTED | sigmoid | 0.1030 | 0.1434 | 0.9285 | 0.8644 | PRODUCTION_V2 | `models\v2\horizon_15_21d\dry_spell\model.joblib` |
| dry_spell | 22_30d | logistic_local | MODEL_SELECTED | sigmoid | 0.0809 | 0.1194 | 0.9582 | 0.8897 | PRODUCTION_V2 | `models\v2\horizon_22_30d\dry_spell\model.joblib` |
| severe_break | 7_14d | logistic_local | MODEL_SELECTED | sigmoid | 0.1294 | 0.1304 | 0.8926 | 0.8864 | PRODUCTION_V2 | `models\v2\horizon_7_14d\severe_break\model.joblib` |
| severe_break | 15_21d | logistic_local | MODEL_SELECTED | sigmoid | 0.1242 | 0.1306 | 0.8653 | 0.8849 | PRODUCTION_V2 | `models\v2\horizon_15_21d\severe_break\model.joblib` |
| severe_break | 22_30d | logistic_local | MODEL_SELECTED | sigmoid | 0.1039 | 0.1183 | 0.9256 | 0.9029 | PRODUCTION_V2 | `models\v2\horizon_22_30d\severe_break\model.joblib` |
| heavy_rain | 7_14d | xgb_full | MODEL_SELECTED | isotonic | 0.0531 | 0.0464 | 0.4809 | 0.9335 | PRODUCTION_V2 | `models\v2\horizon_7_14d\heavy_rain\model.joblib` |
| heavy_rain | 15_21d | logistic_local | MODEL_SELECTED | sigmoid | 0.0483 | 0.0439 | 0.4206 | 0.9349 | PRODUCTION_V2 | `models\v2\horizon_15_21d\heavy_rain\model.joblib` |
| heavy_rain | 22_30d | xgb_atmospheric | BASELINE_PREFERRED | isotonic | 0.0455 | 0.0478 | 0.5379 | 0.9469 | BASELINE_PREFERRED | `models\v2\horizon_22_30d\heavy_rain\model.joblib` |
| revival | 7_14d | xgb_full | MODEL_SELECTED | sigmoid | 0.0384 | 0.0508 | 0.6452 | 0.9423 | PRODUCTION_V2 | `models\v2\horizon_7_14d\revival\model.joblib` |
| revival | 15_21d | xgb_atmospheric | MODEL_SELECTED | sigmoid | 0.0358 | 0.0372 | 0.4694 | 0.9421 | PRODUCTION_V2 | `models\v2\horizon_15_21d\revival\model.joblib` |
| revival | 22_30d | xgb_atmospheric | MODEL_SELECTED | isotonic | 0.0299 | 0.0382 | 0.5536 | 0.9419 | PRODUCTION_V2 | `models\v2\horizon_22_30d\revival\model.joblib` |