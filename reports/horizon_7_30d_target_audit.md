# 7–30 Day Target Audit

Generated after the horizon target repair and rebuild.

## Applicability

- Dry spell: June–October, matching the existing monsoon dry-spell definition.
- Severe break: June–October, matching the existing severe-break definition.
- Revival: June–October because it represents recovery from a monsoon dry/break state; the existing conditional dry-streak requirement is retained.
- Heavy rain: all months, preserving the existing all-year extreme-rain definition.

Out-of-season targets are `NaN` with `target_applicable_* = False`. Future-window tail rows are also `NaN`, with `label_available_* = False`. Neither category enters model training.

## Class Balance

Counts are `positive / negative / out-of-season / unavailable`.

| Target | Train 2020–23 | Validation 2024 | Test 2025 |
|---|---:|---:|---:|
| Dry 7–14d | 4653 / 2691 / 10188 / 0 | 1273 / 563 / 2556 / 0 | 1212 / 624 / 2292 / 252 |
| Dry 15–21d | 4641 / 2703 / 10188 / 0 | 1263 / 573 / 2556 / 0 | 1205 / 631 / 2208 / 336 |
| Dry 22–30d | 5166 / 2178 / 10188 / 0 | 1385 / 451 / 2556 / 0 | 1343 / 493 / 2100 / 444 |
| Severe 7–14d | 3507 / 3837 / 10188 / 0 | 942 / 894 / 2556 / 0 | 887 / 949 / 2292 / 252 |
| Severe 15–21d | 3530 / 3814 / 10188 / 0 | 943 / 893 / 2556 / 0 | 898 / 938 / 2208 / 336 |
| Severe 22–30d | 4160 / 3184 / 10188 / 0 | 1093 / 743 / 2556 / 0 | 1070 / 766 / 2100 / 444 |
| Heavy 7–14d | 1301 / 16231 / 0 / 0 | 292 / 4100 / 0 / 0 | 303 / 3825 / 0 / 252 |
| Heavy 15–21d | 1175 / 16357 / 0 / 0 | 268 / 4124 / 0 / 0 | 270 / 3774 / 0 / 336 |
| Heavy 22–30d | 1421 / 16111 / 0 / 0 | 329 / 4063 / 0 / 0 | 321 / 3615 / 0 / 444 |
| Revival 7–14d | 632 / 6712 / 10188 / 0 | 114 / 1722 / 2556 / 0 | 156 / 1680 / 2292 / 252 |
| Revival 15–21d | 545 / 6799 / 10188 / 0 | 125 / 1711 / 2556 / 0 | 98 / 1738 / 2208 / 336 |
| Revival 22–30d | 555 / 6789 / 10188 / 0 | 134 / 1702 / 2556 / 0 | 128 / 1708 / 2100 / 444 |

## Tail Verification

The repaired implementation was tested against final reference rows and confirms that 2025-12-29, 2025-12-30, and 2025-12-31 cannot receive complete future labels. Required target values remain unavailable rather than being converted to zero.

## Leakage Checks

- Target windows use future observations relative to each reference row.
- IOD as-of validation remains enabled with the three-day publication lag.
- Training remains 2020–2023, calibration remains 2024, and test remains 2025.
