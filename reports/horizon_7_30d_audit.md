# VARSHASENTINEL Horizon 7–30 Day Scientific Audit

## Scope and status

This is an isolated statistical outlook experiment. It does not replace the
existing six-head engine, models, benchmark results, spatial layers, or API.
It is not a dynamical NWP or subseasonal-to-seasonal forecast: no future NWP,
ensemble atmospheric field, or forecast precipitation field is used. The
appropriate interpretation is a probabilistic statistical outlook based on
the observation and climate state available on the reference date.

## Exact target definitions

Each row has a forecast/reference date `t`. A window label `a_b` means that an
event starts on one of the calendar observations `t+a` through `t+b`, inclusive.
The windows are non-overlapping: 7–14, 15–21, and 22–30 days after `t`.

| Event | Target definition for each window |
| --- | --- |
| Dry spell | A run of at least five consecutive daily rainfall observations below 2.5 mm, with the run start in the window. |
| Severe break | A run of at least seven consecutive daily rainfall observations below 2.5 mm, with the run start in the window. |
| Heavy rainfall | A daily rainfall observation at least 64.5 mm, or a 3-day rainfall total at least 150 mm, with the event start in the window. |
| Revival | The reference row has an active dry spell (`Dry_Spell_Days_Streak >= 3`) and, within the window, a day with rainfall at least 5 mm followed by a day with rainfall at least 2.5 mm. |

The existing onset and false-onset targets were not changed. Target values are
created only from future rainfall observations. A target is `NA`, not zero,
when the future observations required to complete the event definition are not
available at the end of the district time series.

## Feature availability and leakage prevention

Features are the numeric columns in the existing IOD-enriched master dataset
that describe the reference date or earlier: location, observed weather,
rolling/as-of aggregates, derived weather features, teleconnection state, and
IOD fields. Date/identifier fields, all existing targets, all new targets, and
columns containing future/target markers are excluded from the feature schema.

The BoM IOD value is retained only under the established 3-day publication-lag
rule. The new metadata records `iod_publication_lag_days: 3`. The audit test
checks `iod_available_date >= iod_period_end_date + 3 days` and
`iod_available_date <= reference date` when release metadata is supplied.
No future rainfall or weather value is interpolated into a feature.

## Temporal protocol

- Training: 2020–2023
- Validation: 2024
- Test: 2025

There is no random train/test split. Decision thresholds are selected from the
validation set only. The final reported metrics use the untouched 2025 test
set. Complete-label filtering leaves 17,532 training rows, 4,392 validation
rows, and 4,380 test rows for every horizon head.

## Model architecture and calibration

Each of the 12 event×horizon heads is an independent `XGBClassifier` with 120
trees, maximum depth 5, learning rate 0.08, 0.85 row and feature subsampling,
and bounded class weighting. Platt/sigmoid calibration is fit on the 2024
validation fold only. Raw and calibrated artifacts are saved separately under
`models/horizon_7_30d/`. Reliability-bin data for each calibrated model is
stored in `reports/horizon_7_30d_metrics.json`.

## 2025 test results

`Brier` is lower-is-better; ROC-AUC and PR-AUC are ranking metrics. F1,
precision, and recall use the threshold selected on validation data. `Rate` is
the positive-event rate in the test set. `Clim Brier` is a constant forecast
equal to the training prevalence, evaluated on the same test rows.

| Target | Brier | Clim Brier | ROC-AUC | PR-AUC | F1 | Precision | Recall | Rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| dry spell 7–14d | 0.1250 | 0.1612 | 0.8109 | 0.9322 | 0.8978 | 0.8376 | 0.9674 | 0.7984 |
| dry spell 15–21d | 0.1473 | 0.1838 | 0.7618 | 0.8888 | 0.8804 | 0.8011 | 0.9772 | 0.7603 |
| dry spell 22–30d | 0.1637 | 0.1792 | 0.6771 | 0.8394 | 0.8770 | 0.8008 | 0.9692 | 0.7719 |
| severe break 7–14d | 0.1256 | 0.2145 | 0.8444 | 0.8889 | 0.8874 | 0.8716 | 0.9038 | 0.6909 |
| severe break 15–21d | 0.1579 | 0.2323 | 0.7818 | 0.7860 | 0.8549 | 0.8039 | 0.9127 | 0.6432 |
| severe break 22–30d | 0.1662 | 0.2285 | 0.7455 | 0.7745 | 0.8570 | 0.8033 | 0.9184 | 0.6630 |
| heavy rainfall 7–14d | 0.0418 | 0.0644 | 0.9366 | 0.4647 | 0.5802 | 0.4514 | 0.8119 | 0.0692 |
| heavy rainfall 15–21d | 0.0383 | 0.0579 | 0.9358 | 0.4799 | 0.5501 | 0.4106 | 0.8333 | 0.0616 |
| heavy rainfall 22–30d | 0.0403 | 0.0680 | 0.9424 | 0.5621 | 0.6474 | 0.5588 | 0.7695 | 0.0733 |
| revival 7–14d | 0.0354 | 0.0489 | 0.9467 | 0.4882 | 0.5158 | 0.4441 | 0.6150 | 0.0516 |
| revival 15–21d | 0.0311 | 0.0398 | 0.9377 | 0.3804 | 0.4178 | 0.2974 | 0.7017 | 0.0413 |
| revival 22–30d | 0.0386 | 0.0569 | 0.9516 | 0.5435 | 0.5606 | 0.4283 | 0.8113 | 0.0605 |

The dry-spell and severe-break heads have lower test Brier scores than their
climatology baselines. The heavy-rain and revival heads do not: their Brier
scores are slightly higher than climatology, so this work does not claim
calibration improvement for those events. Ranking performance is strong but
does not by itself establish reliable probabilities.

## Limitations and next scientific steps

1. The source observations are daily historical station/zone records, not
   forecast atmospheric fields. These outputs must remain labelled statistical
   outlooks and `EXPERIMENTAL_OBSERVATION_STATE`.
2. Event prevalence is highly imbalanced for heavy rainfall and revival; PR-AUC
   and reliability diagrams should be considered alongside Brier score.
3. The 2025 test period is one held-out year. Multi-year rolling-origin tests
   and uncertainty intervals are still needed.
4. The 15–30 day skill may partly reflect persistence and seasonal structure;
   it should not be interpreted as independent weather predictability.
5. Genuine 7–30 day operational forecasting requires point-in-time forecast
   predictors, such as verified ensemble/NWP or S2S atmospheric fields, with
   their own issuance-time and revision audit.

