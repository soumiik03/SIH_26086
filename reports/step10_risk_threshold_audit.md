# Step 10 Risk Threshold Audit

## Production thresholds

For heavy rain, dry spell, and severe break:

- LOW: `< 0.25`
- MODERATE: `0.25 ≤ p < 0.50`
- HIGH: `0.50 ≤ p < 0.75`
- VERY_HIGH: `p ≥ 0.75`

For false onset:

- LOW: `< 0.20`
- MODERATE: `0.20 ≤ p < 0.40`
- HIGH: `0.40 ≤ p < 0.65`
- VERY_HIGH: `p ≥ 0.65`

Missing or non-finite probabilities classify as `UNAVAILABLE`. Overall risk takes the maximum of available head ranks and is `UNAVAILABLE` only when no risk head is available.

## Bandapani trace

| Event | Probability | Applicability | Category |
| --- | ---: | --- | --- |
| Onset | unavailable | OUT_OF_SEASON | UNAVAILABLE |
| False onset | unavailable | OUT_OF_SEASON | UNAVAILABLE |
| 5-day dry spell | 0.9773 | APPLICABLE | VERY_HIGH |
| 7-day severe break | 0.9971 | APPLICABLE | VERY_HIGH |
| Heavy rain | unavailable | UNAVAILABLE | UNAVAILABLE |
| Revival | unavailable | UNAVAILABLE | UNAVAILABLE |
| Overall | available heads only | mixed | VERY_HIGH |

The map is red because two valid applicable probabilities exceed 0.75. It is not red because null values became high risk. Null handling was corrected so affected individual heads are gray/unavailable.
