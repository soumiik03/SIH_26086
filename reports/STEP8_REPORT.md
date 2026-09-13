# STEP 8 REPORT — Historical False-Onset Replay + Backtest

## 1. Backtest audit

The previous endpoint was an honest HTTP 501 with no callable replay implementation. Real feature data, target definitions, and production model artifacts were available.

## 2–4. Replay methodology, period, and leakage controls

The implementation performs a walk-forward historical statistical replay over the untouched 2025 test period. The prediction frame is built from the production feature schemas after removing targets, label-availability fields, crop metadata, and future outcome information. Forecast probabilities and the Step 7 advisory are generated first; existing target labels and future rainfall are joined afterward.

Training remains 2020–2023. Calibration remains 2024. Replay/test remains 2025. Existing operational metadata records a 3-day IOD lag and 1-day atmospheric lag. The replay does not retrain or recalibrate models.

## 5–7. Model versions, inputs, and advisory integration

The API records `VARSHASENTINEL_FORECAST_ENGINE_v1.2`, the production head artifact paths, feature schemas, and `step7-deterministic-v1`. It evaluates all six existing event heads and the statistical 7–30 day outlook. The Aman rice expert system receives forecast probabilities, reference date, location context, observations available at T, and the existing outlook; it never receives the outcome.

## 8. Outcome definitions

Outcomes use the existing target columns from `src/generate_monsoon_targets.py`: `target_onset_window_14d`, `target_false_onset_flag`, `target_dry_spell_5d_14d`, `target_dry_spell_7d_21d`, `target_heavy_rain_7d`, and `target_revival_7d`. No alternate event definition was added.

## 9. False-onset cases

There were 11 actual false-onset events in 2025. No event met the fixed high-probability criterion of false-onset probability >= 0.40, so Case A is unavailable. Cases B–D are included in `reports/step8_false_onset_cases.md`; they are selected algorithmically and not manually cherry-picked.

## 10. Model-level metrics

Metrics below are full 2025 replay evaluation, not demonstration-case performance:

| Head | Events | Brier | Precision | Recall | F1 | ROC-AUC | PR-AUC |
|---|---:|---:|---:|---:|---:|---:|---:|
| Onset | 180 | 0.04368 | 0.33875 | 0.69444 | 0.45537 | 0.95567 | 0.41621 |
| False onset | 11 | 0.00250 | 0.00000 | 0.00000 | 0.00000 | 0.77194 | 0.04493 |
| 5-day dry spell | 1,415 | 0.06406 | 0.79919 | 0.97880 | 0.87992 | 0.97778 | 0.95160 |
| 7-day severe break | 1,218 | 0.06930 | 0.76569 | 0.94171 | 0.84462 | 0.97534 | 0.93935 |
| Heavy rain | 253 | 0.03899 | 0.28571 | 0.01581 | 0.02996 | 0.92140 | 0.36429 |
| Revival | 170 | 0.02733 | 0.00000 | 0.00000 | 0.00000 | 0.93189 | 0.44646 |

The false-onset precision/recall at the fixed 0.5 classification threshold are zero despite non-trivial ranking metrics; this is reported transparently and is not relabeled as a successful demonstration.

## 11. Decision-level metrics

No 2025 replay record triggered `AGRI-WAIT-FALSE-ONSET-001` because no false-onset probability reached the fixed 0.40 rule boundary. Therefore false-onset-specific warning-follow-up rates are unavailable. This must not be interpreted as crop losses prevented or as a counterfactual benefit.

## 12. Limitations

The historical feature data are district-level, not historical Panchayat-level observations. Only 11 false-onset events exist in the single 2025 test year. One test year is insufficient for broad climatological claims. The replay is a statistical model backtest, not an NWP/S2S hindcast.

## 13. API

`GET /api/backtest` now returns `AVAILABLE` with cases, full-period metrics, methodology, model artifact paths, target definitions, lag metadata, and reproducibility information. If the real dataset/artifacts are unavailable, it returns a structured `UNAVAILABLE` response rather than fake results.

## 14–15. Tests and frontend build

- `pytest -q`: required after implementation.
- `python -m unittest discover -s tests -q`: required after implementation.
- `npm run build`: frontend compatibility check; no historical replay UI was added.

## 16. PS alignment

See `reports/step8_ps_alignment.md`. Core replay, temporal, leakage, real-data, probabilistic, advisory, and reproducibility requirements are complete. The high-confidence false-onset demonstration case is unavailable in 2025 and is explicitly reported as a data/model limitation.
