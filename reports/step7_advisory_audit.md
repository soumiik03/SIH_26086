# Step 7 advisory audit

## Existing implementation before Step 7

The pre-existing advisory was `src/spatial_forecast.py:get_agricultural_advisory`. It accepted only forecast probabilities and returned one generic headline/action pair. It had no crop identity, crop stage, sowing date, agronomic window, applicability state, rule identifier, or source reference. Its output is still preserved for the existing spatial-artifact tests and compatibility.

The pre-existing `GET /api/forecast/{panchayat_id}` response exposed the artifact's generic `advisory_headline` and `recommended_action`. It now retains the existing forecast contract and adds a structured, conservative expert advisory with `WAIT` and `AGRI-WAIT-CROP-CONTEXT-001` when no crop context is supplied. This prevents a crop-specific recommendation from being inferred from an unspecified crop.

The frontend's existing `FarmerView` parses advisory text to choose a presentation action. That is a frontend heuristic and is not used by the new backend expert system. The new crop-specific contract is `GET /api/advisory/{panchayat_id}?crop=aman_rice`; future UI work should consume its structured `action`, `rule_id`, `reason_keys`, and `risk_factors` fields directly.

## Crop metadata and model leakage audit

`Target_Crops` and `Active_Crop_Cycle` exist in source/raw weather metadata, but the training scripts explicitly exclude them from model features. Step 7 does not add either field to a model feature set, target, calibration process, or spatial forecast artifact. The agronomic layer receives crop context only at advisory evaluation time.

## Scope decision

Only `aman_rice` is enabled. Maize, pulses, and other crops remain documented candidates rather than unsupported UI options: the repository did not contain a reviewed, geography-specific, deterministic rule set and sowing calendar for them. No crop-specific probability or dummy crop data was created.

## Remaining integration note

The expert layer is backend-ready and source-backed. The existing frontend was intentionally not redesigned in Step 7; it does not yet call the new crop-specific endpoint or expose a crop/stage input. Until that is added, the generic forecast endpoint correctly returns a context-required `WAIT` advisory rather than pretending to make a crop decision.
