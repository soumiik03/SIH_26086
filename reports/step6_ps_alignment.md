# Step 6 PS Alignment

| SIH26086 Requirement | Status | Evidence |
|---|---|---|
| Hyperlocal precipitation behavior | PARTIAL | Official Block/Panchayat geometry exists, but no local rainfall observations are available |
| Local rainfall information | PARTIAL | Twelve district-representative rainfall series exist; no local product is present |
| Local rainfall anomaly | NOT IMPLEMENTED | No defensible local baseline or local rainfall field is available |
| Monsoon onset localization | PARTIAL | Existing onset model remains district-inherited |
| Break localization | PARTIAL | Existing dry/severe models remain district-inherited |
| Heavy-rain localization | PARTIAL | Existing heavy-rain model remains district-inherited |
| ENSO integration | COMPLETE | Existing model feature schemas and enriched datasets |
| IOD integration | COMPLETE | As-of IOD integration and lag features |
| MJO integration | COMPLETE | Existing MJO phase/amplitude features |
| Regional atmospheric signals | COMPLETE | NOAA NCEP regional circulation features remain available |
| Spatial prediction | PARTIAL | Spatial artifacts exist, but predictions are district-inherited |
| Block scale | PARTIAL | Block polygons and inherited forecasts exist; local rainfall skill is unvalidated |
| Panchayat/Village-cluster scale | PARTIAL | Panchayat geometry/output exists; no Panchayat rainfall ground truth |
| 7–30 day outlook | COMPLETE | Three horizons and nullable applicability state are preserved |
| Probability calibration | COMPLETE | Validation-only calibration remains in production horizon models |
| Temporal validation | COMPLETE | 2020–2023 train, 2024 calibration, 2025 test |
| Spatial validation | NOT IMPLEMENTED | No local rainfall field exists to support a valid spatial holdout |
| No future leakage | COMPLETE | Existing IOD controls and new rainfall availability utility/tests |
| Real data only | COMPLETE | No synthetic rainfall or arbitrary spatial variation added |
| No synthetic spatial probabilities | COMPLETE | Routing remains `NONE_DISTRICT_INHERITED` |
