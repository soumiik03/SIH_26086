# Step 8 historical demonstration cases

Cases are selected deterministically from the 2025 replay using fixed thresholds and probability/date/district ordering. These are historical statistical replay demonstrations, not crop-loss counterfactuals.

## Case A — unavailable under the predeclared criterion

Criterion: false-onset probability >= 0.40 and actual `target_false_onset_flag == 1`.

No qualifying case exists in the 2025 test rows. The actual false-onset event count is 11, but the highest replay probability among those events is below the fixed high-risk threshold. This limitation is intentionally exposed.

## Case B — low false-onset probability and no event

- Reference date: 2025-01-01
- District/zone: Alipurduar / terai_teesta
- Prediction information: production feature snapshot available on the date; target and future rows excluded
- Predicted probabilities: onset 0.0003; false onset 0.0011; 5-day dry spell 0.0002; 7-day severe break 0.0003; heavy rain 0.0099; revival 0.0039
- Advisory: `WAIT`
- Rule: `AGRI-WAIT-WINDOW-001`
- Outcome: false onset false; dry spell false; onset false
- Subsequent observed rainfall T+1..T+21 (mm): all 0.0
- Interpretation: low false-onset probability was followed by no false-onset target event. The advisory waited because January is outside the sourced Aman rice window.

## Case C — high onset probability and actual onset

- Reference date: 2025-05-19
- District/zone: Siliguri_Foothill / terai_teesta
- Predicted onset probability: 0.9655
- False-onset probability: 0.0011
- Advisory: `WAIT`
- Rule: `AGRI-WAIT-WINDOW-001`
- Outcome: onset true; false onset false
- Subsequent observed rainfall T+1..T+21 (mm): 0.0, 41.05, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 7.79, 96.27, 0.0, 0.0, 23.32, 0.0, 35.64, 0.0, 18.71, 0.0
- Interpretation: the onset target occurred, while the crop-specific advisory still waited because the reference date preceded the sourced Aman rice window. This demonstrates separation between model event probability and crop decision validity.

## Case D — high dry-spell probability and actual dry spell

- Reference date: 2025-10-05
- District/zone: Bankura / red_laterite
- Predicted 5-day dry-spell probability: 0.9996
- Predicted 7-day severe-break probability: 0.9991
- Advisory: `WAIT`
- Rule: `AGRI-WAIT-WINDOW-001`
- Outcome: 5-day dry spell true; severe break true
- Subsequent observed rainfall T+1..T+21 (mm): all 0.0
- Interpretation: the dry-spell and severe-break targets followed the high forecast probabilities. The advisory remained conservative because October is outside the sourced Aman rice window.

Each returned API case also includes the reproducible T0-to-T+21 timeline with observed future rainfall, clearly separated from the prediction fields.
