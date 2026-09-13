# Step 10 Feature Distribution Shift Diagnostic

This is a feature distribution shift diagnostic, not a formal out-of-distribution detector. Training reference is 2020–2023 from `data/processed/varshasentinel_master_with_atmospheric_signals.parquet`; validation is 2024; test is 2025; current is the Bandapani/Alipurduar vector built as of 2026-09-08.

## Current feature availability

The baseline and IOD schemas are complete for the current record. All nine atmospheric fields required by the atmospheric and horizon schemas are missing. Consequently, atmospheric and horizon models are not evaluated for this current record.

## Baseline/IOD distribution summary

The table reports current value, training min/max, training mean, median, standard deviation, selected 5th/25th/75th/95th percentiles, and the empirical percentile of the current value within the 2020–2023 training rows.

| Feature | Current | Train min | P5 | P25 | Median | P75 | P95 | Train max | Mean | SD | Current pct |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Latitude | 26.49 | 22.45 | 22.45 | 23.25 | 23.66 | 26.36 | 26.71 | 26.71 | 24.38 | 1.561 | 83.3 |
| Longitude | 89.53 | 86.36 | 86.36 | 87.41 | 88.05 | 88.56 | 89.53 | 89.53 | 88.04 | 0.928 | 100.0 |
| Rainfall_Observed_mm | 7.18 | 0 | 0 | 0 | 0 | 0 | 26.06 | 220.1 | 3.682 | 13.04 | 88.5 |
| Tmax_C | 30.48 | 12.44 | 23.03 | 27.40 | 31.83 | 36.71 | 41.78 | 47.54 | 32.08 | 5.844 | 42.6 |
| Tmin_C | 24.57 | 7.76 | 10.99 | 14.20 | 19.99 | 25.78 | 29.01 | 32.68 | 19.99 | 6.158 | 68.9 |
| Relative_Humidity_pct | 87.8 | 31.8 | 41.2 | 45.9 | 51.4 | 69.5 | 86.2 | 99.0 | 57.77 | 15.18 | 96.2 |
| Solar_Radiation_MJm2 | 17.99 | 4 | 7.72 | 16.21 | 20.41 | 21.80 | 23.10 | 26 | 18.57 | 4.606 | 32.6 |
| MJO_Phase | 7 | 1 | 1 | 3 | 5 | 6 | 8 | 8 | 4.536 | 2.254 | 88.1 |
| MJO_Amplitude | 0.8527 | 0.301 | 0.399 | 0.758 | 1.232 | 1.716 | 2.112 | 2.199 | 1.242 | 0.552 | 29.6 |
| Nino34_Anomaly | 2.52 | -1.493 | -1.346 | -1.121 | -0.799 | -0.409 | 1.698 | 1.868 | -0.364 | 1.064 | 100.0 |
| Dry_Spell_Days_Streak | 0 | 0 | 0 | 2 | 8 | 28 | 84 | 169 | 20.60 | 28.52 | 13.7 |
| Rolling_Rainfall_7d_mm | 74.88 | 0 | 0 | 0 | 0 | 30.99 | 130.7 | 474.2 | 25.77 | 49.03 | 88.7 |
| Rolling_Rainfall_30d_mm | 337.28 | 0 | 0 | 0.88 | 41.22 | 131.3 | 521.7 | 1153.6 | 110.37 | 171.15 | 90.1 |
| Drought_Stress_Index | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0.163 | 0.334 | 75.6 |
| Waterlogging_Risk_Index | 0 | 0 | 0 | 0 | 0 | 0.034 | 0.686 | 1 | 0.092 | 0.223 | 67.4 |
| dtr_c | 5.91 | 0.5 | 7.126 | 10.41 | 12.25 | 14.05 | 16.55 | 21.23 | 12.10 | 2.950 | 3.3 |
| vpd_kpa | 0.4485 | 0.0202 | 0.6642 | 1.127 | 1.364 | 1.613 | 1.960 | 2.525 | 1.352 | 0.392 | 2.7 |
| day_of_year | 251 | 1 | 19 | 92 | 183 | 274 | 347 | 366 | 183.1 | 105.4 | 68.7 |
| doy_sin | -0.9232 | -1 | -0.988 | -0.704 | -0.004 | 0.707 | 0.987 | 1 | 0 | 0.707 | 12.3 |
| doy_cos | -0.3844 | -1 | -0.987 | -0.708 | 0.001 | 0.703 | 0.987 | 1 | 0 | 0.707 | 37.5 |
| mjo_phase_sin | -0.7071 | -1 | -1 | -0.707 | 0 | 0.707 | 1 | 1 | -0.021 | 0.709 | 38.5 |
| mjo_phase_cos | 0.7071 | -1 | -1 | -0.707 | 0 | 0.707 | 1 | 1 | -0.017 | 0.705 | 63.9 |
| rolling_rain_3d_mm | 39.18 | 0 | 0 | 0 | 0 | 8.742 | 63.53 | 322.3 | 11.05 | 26.24 | 90.4 |
| rolling_rain_15d_mm | 234.36 | 0 | 0 | 0 | 16.22 | 66.51 | 266.1 | 687.3 | 55.21 | 92.49 | 93.8 |
| iod_dmi | 0.22 | -1.45 | -1.09 | -0.45 | 0.020 | 0.34 | 1.51 | 1.91 | -0.004 | 0.676 | 71.4 |
| iod_positive_flag | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0.214 | 0.410 | 78.6 |
| iod_negative_flag | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0.268 | 0.443 | 73.2 |
| iod_dmi_lag7 | 0.17 | -1.45 | -1.09 | -0.45 | 0.020 | 0.34 | 1.51 | 1.91 | -0.006 | 0.674 | 67.1 |
| iod_dmi_lag14 | 0.18 | -1.45 | -1.09 | -0.45 | 0.020 | 0.34 | 1.51 | 1.91 | -0.008 | 0.671 | 67.6 |

Encoded district/zone columns are schema values rather than continuous scientific measurements: current Alipurduar is encoded as district `0`, zone `2`.

## Atmospheric feature status

| Feature | Current | Training coverage | Status |
| --- | --- | --- | --- |
| u850_regional | unavailable | present | current atmospheric source absent |
| v850_regional | unavailable | present | current atmospheric source absent |
| wind850_speed | unavailable | present | current atmospheric source absent |
| mslp_regional | unavailable | present | current atmospheric source absent |
| regional_slp_gradient | unavailable | present | current atmospheric source absent |
| u850_lag7 | unavailable | present | current atmospheric source absent |
| mslp_lag7 | unavailable | present | current atmospheric source absent |
| u850_rolling_7d | unavailable | present | current atmospheric source absent |
| mslp_rolling_7d | unavailable | present | current atmospheric source absent |

## Interpretation

The strongest shift diagnostics are Niño3.4 at the 100th training percentile, humidity at the 96.2nd percentile, and several rainfall rolling values above the 88th percentile. These are diagnostic observations, not proof of model invalidity. The more decisive operational limitation is missing current atmospheric input, which prevents atmospheric and horizon evaluation. No imputation or stale-year substitution was performed.
