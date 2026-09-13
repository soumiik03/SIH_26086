# Step 9 Forecast Trace

## Representative Panchayat

`Bandapani` (`gp_109796`) → Madarihat → Alipurduar

## Trace

| Stage | Value/source |
| --- | --- |
| Reference date | `2026-09-08` (`data_timestamp=2026-09-08T00:00:00Z`) |
| Raw current observation | District-level observation is consumed by `AsOfFeatureBuilder` / spatial forecast generation; the checked artifact records the reference date and applicability metadata |
| Derived features | Core dry/severe baseline feature vectors were available; atmospheric/horizon features were unavailable for the checked artifact |
| Model selected | `VARSHASENTINEL_FORECAST_ENGINE_v1.2`; dry/severe baseline heads; horizon artifact metadata identifies calibrated Platt-sigmoid models |
| Raw probability | Model output is cleaned/clipped to `[0,1]` and rounded to four decimals by `ForecastEngine.predict()` |
| Calibrated probability | `dry_spell_5d=0.9773`, `severe_break_7d=0.9971`; onset, false onset, heavy rain, revival are null with explicit applicability status |
| API probability | `forecast_service._forecast_probabilities()` preserves these decimal values and nulls; no percent conversion occurs in the API |
| Risk category | `dry_spell_risk=VERY_HIGH`, `severe_break_risk=VERY_HIGH`; overall `VERY_HIGH` under unchanged thresholds; unavailable heads are not LOW after the fix |
| 7–30 outlook | All three horizons contain null probabilities with `UNAVAILABLE` applicability for this artifact |
| Advisory | Backend expert system returns an explicit incomplete-forecast `WAIT`; frontend displays backend action and never manufactures SOW |

## Why this Panchayat is high risk

The high overall state is explained by the two valid applicable probabilities: 0.9773 dry-spell probability and 0.9971 severe-break probability. Missing onset/heavy/revival values are not evidence of low risk. They are represented as unavailable.

## Trace limitation

The current checked artifact does not include the full raw rainfall/RH/MJO/ENSO/IOD/U850/V850/MSLP feature row. Those values must be emitted by the feature-builder/model execution trace at generation time for a complete physical-input audit. This report therefore does not invent them.
