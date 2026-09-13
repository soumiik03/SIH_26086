# Step 10 Spatial Risk Diagnostic

The corresponding machine-readable table is `step10_spatial_risk_diagnostic.csv`.

| District | Blocks | Supported Panchayants | Dry spell | Severe break | Heavy rain | Risk |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| Alipurduar | 8 | 62 | 0.9773 | 0.9971 | unavailable | VERY_HIGH |
| Bankura | 22 | 190 | 0.9871 | 0.9979 | unavailable | VERY_HIGH |
| Birbhum (Suri) | 19 | 167 | 0.9907 | 0.9985 | unavailable | VERY_HIGH |
| Cooch Behar | 12 | 129 | 0.9788 | 0.9826 | unavailable | VERY_HIGH |
| Hooghly | 18 | 206 | 0.9831 | 0.9963 | unavailable | VERY_HIGH |
| Jalpaiguri | 9 | 55 | 0.9738 | 0.9946 | unavailable | VERY_HIGH |
| Jhargram | 8 | 79 | 0.9935 | 0.9972 | unavailable | VERY_HIGH |
| Murshidabad | 26 | 242 | 0.9900 | 0.9971 | unavailable | VERY_HIGH |
| Nadia | 18 | 176 | 0.9809 | 0.9839 | unavailable | VERY_HIGH |
| Purba Bardhaman | 23 | 215 | 0.9877 | 0.9946 | unavailable | VERY_HIGH |
| Purulia | 20 | 170 | 0.9915 | 0.9947 | unavailable | VERY_HIGH |
| Darjeeling (Siliguri Foothills) | 4 | 28 | 0.9885 | 0.9944 | unavailable | VERY_HIGH |

## Interpretation

All 12 supported meteorological districts have distinct dry/severe values, so one global forecast was not applied. Each district's Blocks and Panchayats inherit its own district state under `NONE_DISTRICT_INHERITED`. The map is uniformly red because every district's two applicable baseline heads are above the `VERY_HIGH` threshold.

The heavy-rain column is unavailable for every district because the current 2026 atmospheric feature vector is absent. It is not a zero and it is not used to create the red overall state.

The generated artifact contains 187 Block polygons, 1,719 Panchayat polygons, 1,710 unique safe Panchayat LGD identifiers, and 85 intentionally excluded official GPs. Unsupported blocks are not assigned forecast states.
