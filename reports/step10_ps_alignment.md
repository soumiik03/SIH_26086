# Step 10 PS Alignment

| PS Requirement | Status | Evidence |
|---|---|---|
| ENSO | COMPLETE | Niño3.4 source and feature in `AsOfFeatureBuilder` and model schemas |
| IOD | COMPLETE | BoM IOD as-of join, lag features, IOD model schema |
| MJO | COMPLETE | BoM RMM source, phase/amplitude and cyclic features |
| Regional atmospheric data | PARTIAL | Historical training features and atmospheric artifacts exist; current 2026 source lacks atmospheric fields |
| Local rainfall behavior | PARTIAL | Current district rainfall and rolling/streak features exist; spatial method is district-inherited |
| Onset prediction | COMPLETE | Production artifact and seasonal applicability logic present |
| False onset prediction | COMPLETE | Atmospheric artifact and seasonal applicability logic present |
| Dry spell prediction | COMPLETE | Baseline production artifact and current applicable output present |
| Break prediction | COMPLETE | Baseline severe-break artifact and current applicable output present |
| Revival prediction | COMPLETE | Atmospheric artifact present; current output unavailable without atmospheric inputs |
| Heavy rainfall prediction | COMPLETE | Atmospheric artifact present; current output unavailable without atmospheric inputs |
| 7–30 day outlook | PARTIAL | Twelve calibrated artifacts and API contract exist; current atmospheric input is unavailable |
| Block-level output | COMPLETE | 187 official Block polygons with district inheritance |
| Panchayat-level output | COMPLETE | 1,719 safe-layer polygons / 1,710 unique LGD identifiers |
| Dynamic risk map | COMPLETE | `/api/risk-map` serves generated GeoJSON and MapLibre renders API risk levels |
| Crop-specific advisory | COMPLETE | Deterministic backend expert system with crop context and sourced rules |
| SOW / WAIT / irrigation decision | COMPLETE | Backend action field and explicit missing/context states |
| Historical validation | COMPLETE | 2025 replay/backtest and temporal test reports |
| Current-period forecasting | PARTIAL | Current 2026 surface/climate data are used; atmospheric-dependent heads remain unavailable |

The spatial output is not claimed as complete local rainfall downscaling because production remains `NONE_DISTRICT_INHERITED`.
