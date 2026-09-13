# Step 7 advisory rules

The expert system is deterministic and downstream of existing forecast probabilities. It never generates or modifies probabilities.

| Priority | Rule ID | Condition | Action |
| --- | --- | --- | --- |
| 1 | `AGRI-WAIT-CROP-CONTEXT-001` | No crop supplied | `WAIT`; request supported crop context |
| 2 | `AGRI-WAIT-WINDOW-001` | Reference date outside Aman rice sourced window | `WAIT`; confirm local calendar |
| 3 | `AGRI-WAIT-APPLICABILITY-001` | Required 7–14 day dry/break state is null or out of season | `WAIT`; do not infer |
| 4 | `AGRI-WAIT-APPLICABILITY-002` | Required current probability is unavailable | `WAIT`; do not infer |
| 5 | `AGRI-DRAINAGE-001` | Heavy-rain probability >= 0.50 | `WAIT`; prepare drainage/protect nursery |
| 6 | `AGRI-WAIT-FALSE-ONSET-001` | False-onset probability >= 0.40 | `WAIT`; reassess onset reliability |
| 7 | `AGRI-WAIT-ONSET-001` | Onset probability < 0.60 | `WAIT`; reassess |
| 8 | `AGRI-WAIT-DRY-SPELL-001` | Current dry or 7–14 severe-break risk >= 0.70 | `WAIT`; defer until dependable water is confirmed |
| 9 | `AGRI-IRRIGATION-001` | Current dry >= 0.50, 7–14 dry >= 0.50, or 7–14 severe break >= 0.50 | `PREPARE_IRRIGATION` |
| 10 | `AGRI-SOW-001` | In window, applicable, onset favorable, false-onset low, and dry/break risk acceptable | `SOW` |

Thresholds reuse the existing production advisory/risk boundaries. They are disclosed in every structured result. Rule output includes stable `rule_id`, localization-ready `headline_key` and `reason_keys`, human-readable reasons, validity, and input risk factors.

Crop stage and planned sowing date are accepted as explicit context fields but are not silently used to invent a stage-specific rule. More stage-specific rules require a reviewed source and tests before activation.

Each rule is applicable to the enabled Aman rice profile unless it is a context/applicability guard. Explanation output contains a stable key, human-readable trigger text, actual risk factors, and validity. The dedicated advisory response also returns the unmodified statistical 7–30 day outlook as `supporting_outlook`; the current decision uses only the relevant 7–14 day support fields rather than averaging the horizons.
