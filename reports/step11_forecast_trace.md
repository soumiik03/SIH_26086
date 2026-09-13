# Step 11 Current 2026 V2 Forecast Trace

This trace uses the real current observation already recorded by Step 10; it does not generate a synthetic input or replace missing fields with zero/default weather.

## Selected location

- Panchayat: Bandapani (`gp_109796`)
- Block: Madarihat
- District: Alipurduar
- Reference date / data as of: `2026-09-08` / `2026-09-08`

## Current features

| Feature | Value |
|---|---:|
| `Latitude` | 26.49 |
| `Longitude` | 89.53 |
| `Rainfall_Observed_mm` | 7.18 |
| `Tmax_C` | 30.48 |
| `Tmin_C` | 24.57 |
| `Relative_Humidity_pct` | 87.8 |
| `Solar_Radiation_MJm2` | 17.99 |
| `MJO_Phase` | 7 |
| `MJO_Amplitude` | 0.8527 |
| `Nino34_Anomaly` | 2.52 |
| `Dry_Spell_Days_Streak` | 0 |
| `Rolling_Rainfall_7d_mm` | 74.88 |
| `Rolling_Rainfall_30d_mm` | 337.28 |
| `Drought_Stress_Index` | 0.0 |
| `Waterlogging_Risk_Index` | 0.0 |
| `dtr_c` | 5.91 |
| `vpd_kpa` | 0.4485 |
| `day_of_year` | 251 |
| `doy_sin` | -0.9232 |
| `doy_cos` | -0.3844 |
| `mjo_phase_sin` | -0.7071 |
| `mjo_phase_cos` | 0.7071 |
| `rolling_rain_3d_mm` | 39.18 |
| `rolling_rain_15d_mm` | 234.36 |
| `iod_dmi` | 0.22 |
| `iod_positive_flag` | 0 |
| `iod_negative_flag` | 0 |
| `iod_dmi_lag7` | 0.17 |
| `iod_dmi_lag14` | 0.18 |
| `District_Encoded` | 0 |
| `Zone_Encoded` | 2 |

## V2 current forecast trace

- Engine: `VARSHASENTINEL_V2_STEP11`
- Short-horizon status: `EXPERIMENTAL_OBSERVATION_STATE`

| Event | Applicability | Probability | Model status |
|---|---|---:|---|
| onset | `OUT_OF_SEASON` | unavailable | `PRODUCTION_V2` |
| false_onset | `OUT_OF_SEASON` | unavailable | `BASELINE_PREFERRED` |
| dry_spell_5d | `APPLICABLE` | 0.773946 | `PRODUCTION_V2` |
| severe_break_7d | `APPLICABLE` | 0.417110 | `PRODUCTION_V2` |
| heavy_rain | `BASELINE_PREFERRED` | 0.091667 | `BASELINE_PREFERRED` |
| revival | `UNAVAILABLE` | unavailable | `PRODUCTION_V2` |

## Statistical 7–30 day outlook

- Status: `STATISTICAL_7_30_DAY_OUTLOOK`
- Disclaimer: Statistical probabilistic outlook based on available climate and observation-state information; not an NWP/S2S forecast.

| Period | Event | Applicability | Probability |
|---|---|---|---:|
| 7_14d | dry_spell | `APPLICABLE` | 0.622403 |
| 7_14d | severe_break | `APPLICABLE` | 0.260492 |
| 7_14d | heavy_rain | `UNAVAILABLE` | unavailable |
| 7_14d | revival | `UNAVAILABLE` | unavailable |
| 15_21d | dry_spell | `APPLICABLE` | 0.766521 |
| 15_21d | severe_break | `APPLICABLE` | 0.436951 |
| 15_21d | heavy_rain | `APPLICABLE` | 0.245159 |
| 15_21d | revival | `UNAVAILABLE` | unavailable |
| 22_30d | dry_spell | `APPLICABLE` | 0.952518 |
| 22_30d | severe_break | `APPLICABLE` | 0.764835 |
| 22_30d | heavy_rain | `BASELINE_PREFERRED` | 0.061806 |
| 22_30d | revival | `UNAVAILABLE` | unavailable |

## Interpretation boundary

`UNAVAILABLE` and `OUT_OF_SEASON` are preserved as explicit states. No missing atmospheric field is converted to zero, and no V2 probability is promoted as a backend production response by this trace alone.

Machine-readable copy: [step11_forecast_trace.json](step11_forecast_trace.json)
