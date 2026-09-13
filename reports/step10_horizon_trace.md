# Step 10 7–30 Day Horizon Forensic Trace

## Selected record

Bandapani (`gp_109796`), Alipurduar, reference date `2026-09-08`.

## Model contract

The horizon artifacts are under `models/horizon_7_30d/`. Each is a dictionary containing:

- a `CalibratedClassifierCV` model;
- a raw base-model path;
- `calibration_method: platt_sigmoid`;
- 38 feature names in explicit metadata order;
- train 2020–2023, validation/calibration 2024, test 2025.

## Output matrix

| Horizon | Dry spell | Severe break | Heavy rain | Revival |
| --- | --- | --- | --- | --- |
| 7–14 days | null / UNAVAILABLE | null / UNAVAILABLE | null / UNAVAILABLE | null / UNAVAILABLE |
| 15–21 days | null / UNAVAILABLE | null / UNAVAILABLE | null / UNAVAILABLE | null / UNAVAILABLE |
| 22–30 days | null / UNAVAILABLE | null / UNAVAILABLE | null / UNAVAILABLE | null / UNAVAILABLE |

The distinction is intentional:

- `OUT_OF_SEASON` is used when the reference month is not in the event's declared applicability months.
- `UNAVAILABLE` is used when the event is seasonally applicable but the required atmospheric feature matrix is unavailable.
- `0.0` would mean a valid model prediction numerically equal to zero; none of the current horizon outputs are that state.

## Root cause

`AsOfFeatureBuilder` creates the current surface/climate vector but does not receive current `u850`, `v850`, wind, MSLP, or derived atmospheric fields. `ForecastEngine.prepare_feature_vectors()` sets `df_atmos=None`; `prepare_horizon_feature_vector()` consequently returns `None`. `_predict_horizon_outlook()` then sets each event's probability to `None` and applicability to `UNAVAILABLE` without calling the horizon model.

This is correct missing-input behavior. The previous frontend chart's null-to-zero conversion was a confirmed UI bug and has been removed.

## API/frontend path

`to_forecast_response()` preserves the nested outlook values and applicability states. `ProbabilityCard` renders `Data unavailable` or `Out of season`; `TrendChart` preserves null data points and labels the chart `Data unavailable` when no numeric values exist. No percentage scaling is applied before a model output exists.

## No fabricated repair

No current atmospheric values, horizon probabilities, previous-year values, means, or synthetic values were introduced. The required next data operation is a controlled update of current atmospheric source data followed by a new as-of feature build and forecast run.
