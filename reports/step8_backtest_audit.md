# Step 8 backtest audit

## Existing support

Before Step 8, `backend/routes/backtest.py` exposed `GET /api/backtest` but always returned HTTP 501 with an honest "not implemented" message. There was no callable historical replay service.

## Available data and targets

The real dataset `data/processed/varshasentinel_master_with_atmospheric_signals.parquet` contains 26,304 daily district rows from 2020-01-01 through 2025-12-31, including the existing six target columns. The replay uses the untouched 2025 test rows: 4,380 records and 11 existing `target_false_onset_flag` events.

The target definitions are preserved from `src/generate_monsoon_targets.py`: onset within the existing 14-day window, false-onset collapse, 5-day dry spell, 7-day severe break, heavy rain, and revival. No alternate replay target is created.

## Model artifacts

`src/forecast_engine.py` loads the production baseline, IOD-enhanced, atmospheric-enhanced, and calibrated 7–30 day artifacts. Their metadata records training 2020–2023, calibration 2024, and test 2025. The replay uses the same head routing and model artifact paths.

## Leakage risks and controls

- Target and label columns are removed from the prediction frame.
- `Target_Crops` and `Active_Crop_Cycle` are excluded from model inputs.
- Existing IOD 3-day and atmospheric 1-day operational lag metadata is preserved.
- Historical labels and future rainfall are joined only after forecast probabilities and advisory evaluation.
- No replay outcome is used to tune thresholds, models, calibration, or case selection.
- Demonstration cases use fixed predeclared thresholds and deterministic sorting.

## Missing/limited information

The historical daily dataset is district-level. It does not contain historical block or Panchayat observations, so replay locations are reported at district/zone level. Only 11 false-onset events exist in 2025, and no 2025 actual false-onset event met the predeclared high-probability threshold of 0.40; the API reports no Case A rather than manufacturing one.
