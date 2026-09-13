# Step 11 Baseline Comparison

The routing table contains global climatology, district-month climatology, recent-state baselines, logistic candidates, and XGBoost candidates. Candidate selection uses only validation Brier score with validation climatology protection. The untouched 2025 test is used only for the release decision and reporting. A model is not promoted when a valid baseline has a lower test Brier, discrimination fails, or validation protection fails.

- **onset **: selected `logistic_local`; decision `MODEL_SELECTED`; validation Brier `0.0137`; test Brier `0.1187`; best baseline test Brier `0.1263`.
- **false_onset **: selected `xgb_full`; decision `BASELINE_PREFERRED`; validation Brier `0.0356`; test Brier `0.0850`; best baseline test Brier `0.0846`.
- **dry_spell_5d **: selected `logistic_local`; decision `MODEL_SELECTED`; validation Brier `0.0887`; test Brier `0.1387`; best baseline test Brier `0.1400`.
- **severe_break_7d **: selected `logistic_local`; decision `MODEL_SELECTED`; validation Brier `0.1218`; test Brier `0.1341`; best baseline test Brier `0.1410`.
- **heavy_rain **: selected `logistic_local`; decision `BASELINE_PREFERRED`; validation Brier `0.0569`; test Brier `0.0443`; best baseline test Brier `0.0422`.
- **revival **: selected `xgb_full`; decision `MODEL_SELECTED`; validation Brier `0.0428`; test Brier `0.0433`; best baseline test Brier `0.0625`.
- **dry_spell 7_14d**: selected `logistic_local`; decision `MODEL_SELECTED`; validation Brier `0.1102`; test Brier `0.1520`; best baseline test Brier `0.1608`.
- **dry_spell 15_21d**: selected `logistic_local`; decision `MODEL_SELECTED`; validation Brier `0.1030`; test Brier `0.1434`; best baseline test Brier `0.1552`.
- **dry_spell 22_30d**: selected `logistic_local`; decision `MODEL_SELECTED`; validation Brier `0.0809`; test Brier `0.1194`; best baseline test Brier `0.1246`.
- **severe_break 7_14d**: selected `logistic_local`; decision `MODEL_SELECTED`; validation Brier `0.1294`; test Brier `0.1304`; best baseline test Brier `0.1322`.
- **severe_break 15_21d**: selected `logistic_local`; decision `MODEL_SELECTED`; validation Brier `0.1242`; test Brier `0.1306`; best baseline test Brier `0.1391`.
- **severe_break 22_30d**: selected `logistic_local`; decision `MODEL_SELECTED`; validation Brier `0.1039`; test Brier `0.1183`; best baseline test Brier `0.1273`.
- **heavy_rain 7_14d**: selected `xgb_full`; decision `MODEL_SELECTED`; validation Brier `0.0531`; test Brier `0.0464`; best baseline test Brier `0.0468`.
- **heavy_rain 15_21d**: selected `logistic_local`; decision `MODEL_SELECTED`; validation Brier `0.0483`; test Brier `0.0439`; best baseline test Brier `0.0444`.
- **heavy_rain 22_30d**: selected `xgb_atmospheric`; decision `BASELINE_PREFERRED`; validation Brier `0.0455`; test Brier `0.0478`; best baseline test Brier `0.0448`.
- **revival 7_14d**: selected `xgb_full`; decision `MODEL_SELECTED`; validation Brier `0.0384`; test Brier `0.0508`; best baseline test Brier `0.0758`.
- **revival 15_21d**: selected `xgb_atmospheric`; decision `MODEL_SELECTED`; validation Brier `0.0358`; test Brier `0.0372`; best baseline test Brier `0.0491`.
- **revival 22_30d**: selected `xgb_atmospheric`; decision `MODEL_SELECTED`; validation Brier `0.0299`; test Brier `0.0382`; best baseline test Brier `0.0609`.