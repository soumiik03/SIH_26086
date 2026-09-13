# Step 9 Risk Map, Advisory, and Graph Audit

## Scope and method

This audit traced the current artifact and source path:

`data/processed/...` → `ForecastEngine.predict()` → `src/spatial_forecast.py` → `backend/services/forecast_service.py` → frontend API types/components.

The checked current spatial artifacts contain 187 blocks and 1,710 safe-layer Panchayats. They are dated `2026-09-08` with system date `2026-09-13`.

## Probability distribution

The current block artifact has district-inherited values. Across all 187 blocks:

| Field | Available values | Missing values |
| --- | ---: | ---: |
| Onset | 0 | 187 |
| False onset | 0 | 187 |
| 5-day dry spell | 187 | 0 |
| 7-day severe break | 187 | 0 |
| Heavy rain | 0 | 187 |
| Revival | 0 | 187 |

The applicable dry-spell values range from 0.9738 to 0.9935; severe-break values range from 0.9826 to 0.9985. These are decimal probabilities, not percentages. No second `×100` occurs in the backend path. The frontend multiplies once only for display.

## Risk-category distribution

Before the fix, all 187 blocks were labeled `VERY_HIGH`; affected missing heads were incorrectly categorized as `LOW` and the legacy spatial advisory treated missing values as zero. The valid dry-spell and severe-break values legitimately produce `VERY_HIGH` overall risk under the documented thresholds.

After the fix, missing individual heads are `UNAVAILABLE`; overall risk is derived only from available heads, and becomes `UNAVAILABLE` only when no risk head is available. No risk value is manufactured to improve map appearance.

## Thresholds

- LOW: `< 0.25` for heavy rain, dry spell, severe break; `< 0.20` for false onset.
- MODERATE: `0.25–<0.50`; false onset `0.20–<0.40`.
- HIGH: `0.50–<0.75`; false onset `0.40–<0.65`.
- VERY_HIGH: `>= 0.75`; false onset `>= 0.65`.
- UNAVAILABLE: no finite probability for that head.

The thresholds remain unchanged.

## District and block variation

| District | Blocks | Panchayats | Onset | False Onset | Dry spell | Severe break | Heavy rain | Revival |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Alipurduar | 8 | 91 | unavailable | unavailable | 0.9773 | 0.9971 | unavailable | unavailable |
| Bankura | 22 | 179 | unavailable | unavailable | 0.9871 | 0.9979 | unavailable | unavailable |
| Birbhum (Suri) | 19 | 167 | unavailable | unavailable | 0.9907 | 0.9985 | unavailable | unavailable |
| Cooch Behar | 12 | 128 | unavailable | unavailable | 0.9788 | 0.9826 | unavailable | unavailable |
| Hooghly | 18 | 197 | unavailable | unavailable | 0.9831 | 0.9963 | unavailable | unavailable |
| Jalpaiguri | 9 | 75 | unavailable | unavailable | 0.9738 | 0.9946 | unavailable | unavailable |
| Jhargram | 8 | 79 | unavailable | unavailable | 0.9935 | 0.9972 | unavailable | unavailable |
| Murshidabad | 26 | 237 | unavailable | unavailable | 0.9900 | 0.9971 | unavailable | unavailable |
| Nadia | 18 | 188 | unavailable | unavailable | 0.9809 | 0.9839 | unavailable | unavailable |
| Purba Bardhaman | 23 | 203 | unavailable | unavailable | 0.9877 | 0.9946 | unavailable | unavailable |
| Purulia | 20 | 156 | unavailable | unavailable | 0.9915 | 0.9947 | unavailable | unavailable |
| Darjeeling (Siliguri Foothills) | 4 | 10 | unavailable | unavailable | 0.9885 | 0.9944 | unavailable | unavailable |

Each district's Blocks and Panchayats inherit one district state with `NONE_DISTRICT_INHERITED`; there is no synthetic spatial noise. District states differ, so the map preserves legitimate district variation.

## Block/Panchayat mapping

The spatial generator writes `district_id`, `block_id`, `panchayat_id`, and inherited state together. The API service finds Panchayats by exact `panchayat_id` and Block membership by exact `block_id`. Tests assert the `gp_`/`blk_` mappings and district-inheritance consistency.

## Advisory distribution and defects

The pre-fix artifact contained “Prolonged Dry Spell / Break Warning” because the legacy spatial advisory converted missing onset/heavy/revival probabilities to zero. This was a confirmed missing-data coercion defect. The legacy function now returns `Agronomic Advisory Unavailable` whenever required probabilities are missing. The API expert system separately returns a deterministic `WAIT` with an explicit incomplete-forecast rule, never `SOW`, when required inputs are unavailable.

## Graph values

The current artifact's 7–30 day outlook has `UNAVAILABLE` applicability and null probabilities for all three horizons and all four events because the horizon feature vector was unavailable. The previous frontend converted each null to `0` and rounded before rendering. The chart now preserves nulls, includes all four event series, and labels the state `Data unavailable`; it uses `Low modeled probability` only when real numeric values exist and are below 1%.

## Fixes made

- Added explicit `UNAVAILABLE` risk handling in spatial classification and map colors.
- Removed null-to-LOW classification and null-to-zero advisory coercion.
- Preserved nullable API probabilities.
- Removed chart null-to-zero and pre-render rounding behavior.
- Added frontend unavailable/out-of-season labels and backend advisory action consumption without a frontend SOW fallback.
- Added Step 9 regression tests for missing states, decimal preservation, thresholds, inheritance, IDs, graph values, and no synthetic variation.

The Python runtime is not installed in this execution environment, so the checked GeoJSON artifacts were not regenerated here. The API now recomputes risk levels from the preserved probability fields, and the next normal forecast-generation run will write the corrected `UNAVAILABLE` head states and unavailable advisory metadata into the derived artifacts.

## Remaining scientific limitations

- The current source data do not provide a usable atmospheric feature vector for the horizon models, so the 7–30 day values are unavailable rather than zero.
- Several core event heads are correctly out of season or unavailable on the reference date.
- The spatial method is intentionally district-inherited (`NONE_DISTRICT_INHERITED`); it does not provide validated Panchayat-scale downscaling.
- A full raw-observation/model-feature trace requires the feature-builder output and model runtime to be available in the execution environment; the artifact metadata and model versions remain exposed for that trace.
