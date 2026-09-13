# STEP 6 — LOCAL RAINFALL ANOMALY + HYPERLOCAL PRECIPITATION BEHAVIOR

## Executive conclusion

The repository does not contain real local rainfall information at Block or Panchayat scale. It contains 12 district-representative daily rainfall series, with one coordinate per district. These data are useful for regional temporal event modeling but cannot support a scientifically defensible local rainfall anomaly or validated Panchayat-level rainfall downscaling.

Production routing therefore remains:

```text
downscaling_method = NONE_DISTRICT_INHERITED
```

No synthetic Panchayat rainfall, geographic noise, centroid-extracted rainfall, or visually motivated probability variation was introduced.

## 1. Existing rainfall data audit

See `reports/step6_rainfall_data_audit.md`.

The current data comprise three zone CSVs covering 2020–2025, with 26,304 rows and 12 unique district coordinates. No station IDs, grid-cell identifiers, spatial support metadata, or Panchayat/block rainfall observations are present.

## 2. New rainfall source investigation

Authoritative candidates investigated:

- IMD daily 0.25° gauge-derived gridded rainfall
- NASA GPM IMERG V07B Final 0.1° precipitation
- NASA IMERG Early/Late products
- ERA5 0.25° reanalysis precipitation

## 3. Selected source and justification

IMERG V07B Final daily accumulation is selected as the future evaluation candidate because it covers 2020–2025 at 0.1° resolution and provides daily precipitation suitable for target-compatible aggregation. It is not treated as Panchayat ground truth.

## 4. Spatial resolution

Current production rainfall: one representative coordinate per district, with no stated measurement footprint.

Selected candidate: IMERG V07B Final, 0.1° × 0.1°.

## 5. Temporal resolution

Current production rainfall: daily.

Selected candidate: half-hourly source with daily accumulation products.

## 6. Availability latency

The new provenance utility implements:

```text
availability_timestamp <= forecast_reference_timestamp
```

IMERG Final is documented with approximately 3.5 months latency. Historical replay must use that availability timestamp and must not use later revised values at earlier forecast times.

## 7. Spatial aggregation methodology

No spatial aggregation was executed because no candidate rainfall files are present locally.

The required future method is area-weighted intersection of rainfall grid cells with official Block and safe Panchayat polygons. Centroid-only extraction is explicitly rejected.

## 8. Climatology methodology

No local rainfall climatology was constructed. A future implementation must calculate training-period-only climatology for historical model training and must not use 2025 test information in the baseline.

## 9. Local rainfall features

No local rainfall features were added. Existing rainfall-memory features remain explicitly regional/district-proxy features.

## 10. Local anomaly methodology

Not implemented because a local rainfall field and validated baseline are absent. No local anomaly was fabricated from district rainfall.

## 11. Leakage controls

- Added explicit timestamp availability helpers.
- Added tests for observation/publication/forecast ordering.
- Existing IOD as-of controls remain intact.
- Existing temporal train/calibration/test splits remain intact.
- No future rainfall values were used to create new historical features.

## 12. Temporal validation

The existing production split remains:

- Train: 2020–2023
- Calibration: 2024
- Test: 2025

No local-rainfall model was trained because the required source is absent.

## 13. Spatial validation

Not implemented. A spatial holdout cannot be scientifically performed without local rainfall observations or a validated spatial product.

## 14. Baseline metrics

The existing Step 4/Step 5 benchmark remains the baseline. Representative selected-model metrics include:

| Head | Test Brier | ROC-AUC | PR-AUC | Climatology Brier |
|---|---:|---:|---:|---:|
| Onset | 0.0303 | 0.9557 | 0.4163 | 0.0394 |
| False onset | 0.0025 | 0.9298 | 0.0401 | 0.0025 |
| 5-day dry spell | 0.0662 | 0.9740 | 0.9431 | 0.2190 |
| Severe break | 0.0686 | 0.9731 | 0.9365 | 0.2008 |
| Heavy rain | 0.0390 | 0.9214 | 0.3642 | 0.0545 |
| Revival | 0.0273 | 0.9315 | 0.4469 | 0.0374 |

## 15. Enhanced metrics

Not available. No local rainfall-enhanced model was trained, so no improvement claim is made.

## 16. Calibration results

Existing production calibration remains validation-only. No local rainfall calibration was performed.

## 17. Feature importance

Existing rainfall-memory importance is documented in `reports/step6_feature_importance.md`. It represents regional/district-proxy rainfall features, not local rainfall.

## 18. Production routing decisions

All events and horizons retain the current routing:

```text
RETAIN_CURRENT_MODEL
downscaling_method = NONE_DISTRICT_INHERITED
```

There is insufficient evidence to promote a local rainfall model.

## 19. Spatial output changes

No rainfall-based spatial probability changes were made. Existing spatial artifacts remain district-inherited.

## 20. API verification

Existing API contracts remain unchanged for the current endpoints. Nullable out-of-season horizon probabilities remain preserved. No new local rainfall fields were added to the API.

## 21. Tests

Added rainfall provenance and availability tests covering:

- Source metadata
- District versus local spatial support
- Availability latency
- No local rainfall artifact claim
- Existing `NONE_DISTRICT_INHERITED` routing

Existing forecast, horizon, spatial, and API schema tests remain applicable.

## 22. Frontend build

The frontend was not modified. The previously verified production build remains the reference build. No frontend redesign or integration was performed in Step 6.

## 23. PS alignment

See `reports/step6_ps_alignment.md`.

The project partially satisfies hyperlocal precipitation behavior because the administrative spatial output exists, but it does not yet have real local rainfall evidence sufficient to claim validated Panchayat-level precipitation prediction.

## 24. Remaining limitations

- No traceable local station network is present.
- Current rainfall source provenance is incomplete.
- IMERG and IMD candidate products have not yet been downloaded and validated against local observations.
- No area-weighted rainfall aggregation has been executed.
- No local anomaly climatology exists.
- No local-rainfall ablation or spatial holdout has been run.
- District inheritance remains scientifically preferable to unsupported spatial variation.
