# Step 10 Advisory Forensics

## Bandapani / gp_109796

The forecast endpoint calls `backend.services.forecast_service._expert_advisory()` without crop context. The expert system therefore returns:

- action: `WAIT`
- rule: `AGRI-WAIT-CROP-CONTEXT-001`
- validity: `CROP_CONTEXT_REQUIRED`
- explanation: select a supported crop before requesting a crop-specific sowing decision

This explains why the farmer UI shows `WAIT` while the headline may say `Crop context required`: the action is the backend's conservative action and the headline describes the missing crop context. The frontend reads `advisory.action` and does not infer thresholds.

The crop-specific advisory route requires a crop. For `aman_rice`, the current September reference date is outside the sourced sowing window, and missing current/horizon probabilities are also handled by explicit backend WAIT rules. It does not fall through to SOW.

## Rule inputs

- Dry spell: 0.9773
- Severe break: 0.9971
- Onset, false onset, heavy rain, revival: unavailable or out of season
- 7–14 day outlook: unavailable
- Crop-neutral endpoint: no crop supplied

The advisory layer does not change the model probabilities or risk thresholds. The spatial artifact advisory is `Agronomic Advisory Unavailable` after regeneration because required probabilities are incomplete.
