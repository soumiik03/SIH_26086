# Step 10 Single-Panchayat Forecast Trace

## Selected record

- Panchayat: Bandapani (`gp_109796`)
- Block: Madarihat
- District: Alipurduar
- Reference date / data as of: `2026-09-08`
- Current system date: `2026-09-13`
- Freshness: `CURRENT`

The complete machine-readable trace is [step10_forecast_trace.json](step10_forecast_trace.json).

## Exact production feature vector

The baseline/IOD vector contains 26/31 ordered fields. The selected current vector is:

| Feature | Value |
| --- | ---: |
| Latitude / Longitude | 26.49 / 89.53 |
| Rainfall observed | 7.18 mm |
| Tmax / Tmin | 30.48 / 24.57 °C |
| Relative humidity | 87.8% |
| Solar radiation | 17.99 MJ/m² |
| MJO phase / amplitude | 7 / 0.8527 |
| Niño3.4 anomaly | 2.52 |
| Dry-spell streak | 0 days |
| Rolling rainfall 3d / 7d / 15d / 30d | 39.18 / 74.88 / 234.36 / 337.28 mm |
| DTR / VPD | 5.91 °C / 0.4485 kPa |
| IOD DMI / lag7 / lag14 | 0.22 / 0.17 / 0.18 |
| IOD flags | positive 0, negative 0 |
| DOY / sine / cosine | 251 / -0.9232 / -0.3844 |
| MJO sine / cosine | -0.7071 / 0.7071 |
| District / zone encoding | 0 / 2 |

Atmospheric fields (`u850`, `v850`, wind, MSLP, gradients, and rolling/lagged atmospheric fields) are absent from the 2026 source row. `ForecastEngine.prepare_feature_vectors()` therefore returns `df_atmos=None` for the current record. It does not substitute 2025 values or the historical atmospheric defaults for a 2026 observation.

## Model trace

| Event | Artifact | Status | Production probability |
| --- | --- | --- | ---: |
| Onset | `models/iod_enhanced/target_onset_window_14d_xgb.joblib` | OUT_OF_SEASON | unavailable |
| False onset | `models/atmospheric_enhanced/target_false_onset_flag_xgb.joblib` | OUT_OF_SEASON | unavailable |
| 5-day dry spell | `models/target_dry_spell_5d_14d_xgb.joblib` | APPLICABLE | 0.9773 |
| 7-day severe break | `models/target_dry_spell_7d_21d_xgb.joblib` | APPLICABLE | 0.9971 |
| Heavy rain | `models/atmospheric_enhanced/target_heavy_rain_7d_xgb.joblib` | UNAVAILABLE | unavailable |
| Revival | `models/atmospheric_enhanced/target_revival_7d_xgb.joblib` | UNAVAILABLE | unavailable |

For the two applicable baseline heads, direct artifact inspection shows `model` and `base_model` are both `XGBClassifier` objects and produce the same values. These selected artifacts do not contain a `CalibratedClassifierCV` wrapper. Therefore the 0.9773 and 0.9971 values are raw XGBoost probabilities rounded to four decimals by the engine, not independently verifiable Platt-calibrated probabilities.

Atmospheric heads are not called because their required feature matrix is unavailable. This is a data-availability state, not a zero prediction.

## Classification and propagation

The unchanged thresholds classify 0.9773 and 0.9971 as `VERY_HIGH`. Missing head values classify as `UNAVAILABLE`. Overall risk is `VERY_HIGH` because valid applicable dry-spell/severe-break heads are very high. The state is inherited from Alipurduar to its Blocks and safe Panchayats with `NONE_DISTRICT_INHERITED`.

## 7–30 day output

All three horizons and all four events are `UNAVAILABLE` because the horizon feature matrix requires the missing atmospheric fields. The backend and frontend preserve nulls and applicability status; no valid 0% is produced.

## Advisory

The crop-neutral forecast endpoint has no crop context, so the expert system returns backend action `WAIT` with the `CROP_CONTEXT_REQUIRED` rule/headline. The crop-specific advisory endpoint requires a crop; with missing current forecast inputs it returns a deterministic incomplete-forecast `WAIT`. The frontend displays the backend action and does not generate `SOW`.
