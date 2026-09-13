# STEP 7 REPORT — Crop-Specific Agronomic Expert System

## Executive result

Implemented a deterministic backend agronomic expert layer downstream of the existing forecast API. It does not train a model, create dummy data, produce synthetic probabilities, alter model features, alter forecast labels, or change the spatial forecast engine.

## Implementation

- `src/agronomy/expert_system.py`: source-backed Aman rice profile and deterministic rules.
- `backend/services/forecast_service.py`: passes existing six probabilities and the existing statistical outlook into the expert system; generic forecast responses safely require crop context; crop-specific advisory service added.
- `backend/routes/forecast.py`: added `GET /api/advisory/{panchayat_id}` with required `crop` and optional stage/date context.
- `backend/schemas/forecast.py`: structured advisory fields and crop-specific advisory response models.
- `tests/test_agronomy.py`: rule priority, missing applicability, missing input, source profile, determinism, and bounds tests.

## Existing advisory audit

The legacy spatial artifact advisory remains intact for compatibility and regression coverage. The API interpretation layer now evaluates the unchanged forecast probabilities through the agronomic expert system. Existing crop metadata is not used as a predictive feature.

## Supported crop and sowing windows

The only enabled crop is Aman rice: May 20-August 7 decision window, with June 10-June 25 preferred transplanting interval, subject to location and stage confirmation. Maize/pulses/oilseeds remain future extensions because evidence was not encoded into reviewed rules.

## Farmer and officer behavior

The structured backend result prioritizes `SOW`, `WAIT`, or `PREPARE_IRRIGATION`, followed by `headline`, `reasons`, `risk_factors`, `validity`, and `rule_id`. Officers can use the crop, stage, rule, probability factors, and `supporting_outlook` fields. No LLM or free-form override is used.

## 7-30 day integration and applicability

The advisory receives the existing 7-30 day object, respects `OUT_OF_SEASON` and null values, uses applicable 7-14 day dry/break evidence as supporting context, and returns the complete outlook separately. It does not collapse 30 days into an average or treat out-of-season null as zero.

## Explanation, API, tests, and limitations

Stable reason keys and rule IDs enable later translation. `GET /api/forecast/{panchayat_id}` remains available with unchanged six probabilities; `GET /api/advisory/{panchayat_id}?crop=aman_rice` supplies the crop-specific interpretation. `pytest -q` and unittest discovery are required validation commands. The current frontend has not been redesigned and does not yet collect crop context, so the generic forecast path conservatively returns context-required `WAIT`.

## Future extension points

Add another crop only after recording authoritative geography-specific timing, water-risk, stage, and source evidence plus tests. Add a frontend consumer for the structured advisory endpoint only as a later scoped UI task. Do not feed advisory outputs back into model training.

## Data integrity

The only enabled crop profile is Aman rice because its timing and contingency actions are documented for West Bengal/North 24 Parganas. The layer reads forecast probabilities from existing artifacts and returns a conservative `WAIT` state for missing context or unavailable applicability. No false data model or fabricated crop data is present.

## Validation

Run `pytest -q` and `python -m unittest discover -s tests -q` after implementation. Existing spatial advisory compatibility remains covered by the original tests. Frontend files and model/data pipelines were not changed.

See `step7_advisory_audit.md`, `step7_agronomic_sources.md`, `step7_advisory_rules.md`, and `step7_ps_alignment.md` for audit, sources, rule definitions, and requirement mapping.
