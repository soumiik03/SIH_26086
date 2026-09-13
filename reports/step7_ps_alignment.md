# Step 7 PS alignment

| SIH26086 Requirement | Status | Evidence |
| --- | --- | --- |
| Expert system | COMPLETE | `src/agronomy/expert_system.py` is a deterministic downstream rule layer. |
| Crop-specific advisory | PARTIAL | Aman rice is enabled; additional crops are intentionally not enabled without reviewed profiles. |
| Localized advisory | PARTIAL | Panchayat location is returned and existing spatial probabilities are consumed; no new spatial downscaling is claimed. |
| Onset probability integration | COMPLETE | `AGRI-WAIT-ONSET-001` and `AGRI-SOW-001`. |
| False-onset integration | COMPLETE | `AGRI-WAIT-FALSE-ONSET-001`. |
| Dry-spell response | COMPLETE | `AGRI-IRRIGATION-001` uses current and 7–14 day API probabilities. |
| Heavy-rain integration | COMPLETE | `AGRI-DRAINAGE-001` prioritizes water-excess safety. |
| 7–30 day context | COMPLETE | Consumes existing statistical outlook and honors applicability/null values. |
| Delay sowing | COMPLETE | Explicit `WAIT` rules and sourced crop window. |
| Prepare irrigation | COMPLETE | Explicit `PREPARE_IRRIGATION` rule. |
| Alter crop decision support | NOT IMPLEMENTED | No unsupported crop switching recommendation is generated. |
| Deterministic/explainable | COMPLETE | Stable rule IDs, reasons, source-backed profile, disclosed thresholds. |
| No synthetic forecast data | COMPLETE | Existing forecast probabilities are passed through unchanged. |
| No ML leakage | COMPLETE | No model features, targets, training, or calibration changed. |
| Regional-language readiness | COMPLETE | Stable message keys are emitted; translation is not fabricated. |
| Spatial honesty | COMPLETE | Advisory consumes existing API artifact values; it does not downscale or invent local rainfall. |
