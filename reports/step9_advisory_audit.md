# Step 9 Advisory Audit

## Representative current case

- Panchayat: Bandapani (`gp_109796`)
- Block: Madarihat
- District: Alipurduar
- Reference/data date: `2026-09-08`
- Applicable current probabilities: dry spell `0.9773`; severe break `0.9971`
- Unavailable/out-of-season current probabilities: onset, false onset, heavy rain, revival

## Rule trace

| Stage | Result |
| --- | --- |
| Input probabilities | Missing values remain null; no missing value is converted to zero |
| Seasonal applicability | Onset and false onset out of season; revival and heavy rain unavailable in the artifact; dry/severe applicable |
| Applicable rule | The API expert system requires complete current inputs and applicable 7–14 day inputs |
| Selected rule | `AGRI-WAIT-APPLICABILITY-002` when required current inputs are missing |
| Final action | `WAIT` from the backend expert system, not a frontend-generated action |
| Explanation | Do not infer a sowing decision from missing probabilities; reassess when the forecast is complete |

The old spatial helper had a separate defect: `probabilities.get(...) or 0.0` allowed missing inputs to fall through to a normal or risk-derived advisory. It now returns `Agronomic Advisory Unavailable` and does not invent an action. The frontend also no longer falls back to `SOW` when advisory data are missing or malformed.

## Rule priority verified

The source-backed expert-system order is: crop context and date validity, forecast applicability, current forecast completeness, heavy-rain wait, false-onset wait, onset threshold, severe dry/break wait, irrigation preparation, then sowing. Existing thresholds were not changed.
