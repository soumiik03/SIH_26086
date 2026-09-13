# Step 6 Feature Importance

## Scope

No local rainfall or rainfall-anomaly feature was available, so no local-rainfall-enhanced model was trained. This report records the existing production model's rainfall-related feature importance and avoids attributing it to Panchayat-scale rainfall.

## Existing rainfall-related features

The current models use district/regional rainfall-proxy features. Representative XGBoost importances from the existing artifacts include:

| Head | Highest rainfall/hydrology-related features |
|---|---|
| Onset | `Drought_Stress_Index` 0.0453; `Rolling_Rainfall_7d_mm` 0.0275; `rolling_rain_15d_mm` 0.0254; `Rainfall_Observed_mm` 0.0083 |
| False onset | `Rolling_Rainfall_30d_mm` 0.0684; `Rainfall_Observed_mm` 0.0360; `Dry_Spell_Days_Streak` 0.0243 |
| Heavy rain | `Waterlogging_Risk_Index` 0.3723; `Rolling_Rainfall_30d_mm` 0.0363; `rolling_rain_3d_mm` 0.0297; `Rainfall_Observed_mm` 0.0104 |
| Revival | `rolling_rain_3d_mm` 0.1741; `Dry_Spell_Days_Streak` 0.1184; `Rainfall_Observed_mm` 0.0239 |
| 5-day dry spell | `Waterlogging_Risk_Index` 0.0226; `Rolling_Rainfall_30d_mm` 0.0138; `Dry_Spell_Days_Streak` 0.0043 |
| Severe break | `Rolling_Rainfall_30d_mm` 0.0139; `Waterlogging_Risk_Index` 0.0087; `Dry_Spell_Days_Streak` 0.0046 |

## Interpretation

These importances show that rainfall memory and hydrological state contribute to the existing regional models. They do not demonstrate local spatial skill because the source rainfall varies by district representative series and is inherited across the district's spatial units.

ENSO, IOD, MJO, atmospheric circulation, and rainfall-memory features remain distinct feature families. No local rainfall feature importance is reported because adding a feature without a real source would violate the Step 6 data-integrity rules.
