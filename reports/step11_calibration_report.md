# Step 11 Calibration Report

Calibration methods are selected before 2025 evaluation using 2024 validation evidence: sigmoid and isotonic are fit on the first 2024 half and compared on the second half by Brier score, then the selected method is refit on 2024. No 2025 or 2026 labels enter calibration.

- **onset**: `isotonic`; test Brier=0.1187; test log loss=0.5832.
- **false_onset**: `sigmoid`; test Brier=0.0850; test log loss=0.3236.
- **dry_spell_5d**: `isotonic`; test Brier=0.1387; test log loss=0.8023.
- **severe_break_7d**: `sigmoid`; test Brier=0.1341; test log loss=0.3954.
- **heavy_rain**: `sigmoid`; test Brier=0.0443; test log loss=0.1444.
- **revival**: `sigmoid`; test Brier=0.0433; test log loss=0.1443.
- **dry_spell**: `sigmoid`; test Brier=0.1520; test log loss=0.4610.
- **dry_spell**: `sigmoid`; test Brier=0.1434; test log loss=0.4423.
- **dry_spell**: `sigmoid`; test Brier=0.1194; test log loss=0.3731.
- **severe_break**: `sigmoid`; test Brier=0.1304; test log loss=0.4108.
- **severe_break**: `sigmoid`; test Brier=0.1306; test log loss=0.4246.
- **severe_break**: `sigmoid`; test Brier=0.1183; test log loss=0.3792.
- **heavy_rain**: `isotonic`; test Brier=0.0464; test log loss=0.1523.
- **heavy_rain**: `sigmoid`; test Brier=0.0439; test log loss=0.1417.
- **heavy_rain**: `isotonic`; test Brier=0.0478; test log loss=0.3465.
- **revival**: `sigmoid`; test Brier=0.0508; test log loss=0.1665.
- **revival**: `sigmoid`; test Brier=0.0372; test log loss=0.1226.
- **revival**: `isotonic`; test Brier=0.0382; test log loss=0.2382.