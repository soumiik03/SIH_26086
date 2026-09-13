# Step 5 — Spatial Downscaling Audit & Scientific Assessment

## Objective

Investigate whether the current `NONE_DISTRICT_INHERITED` downscaling method
can be replaced with genuine spatial downscaling using real physical/spatial
predictors (elevation, latitude, longitude, rainfall climatology).

## Step 5A: Current Spatial Pipeline Audit

### Data Architecture
- **12 meteorological districts** across West Bengal
- **187 CD Blocks** with official SOI boundaries (EPSG:4326)
- **1,710 unique Gram Panchayats** with SAFE_VERIFIED geometries
- **1 weather observation point per district** (district centroid)
- **0 sub-district weather stations** in the dataset

### Current Downscaling
All blocks and panchayats currently inherit their parent district's
calibrated probability without adjustment:
```
downscaling_method = "NONE_DISTRICT_INHERITED"
```

An unused `SpatialDataLoader.downscale_district_forecast()` method exists in
`src/spatial/spatial_loader.py` with hardcoded logit-space coefficients, but
it is **never called** and has **no empirical validation**.

### Available Spatial Covariates

| Covariate | Block | Panchayat | Source |
|-----------|-------|-----------|--------|
| Centroid latitude | ✅ | ✅ | Geometry |
| Centroid longitude | ✅ | ✅ | Geometry |
| Area (km²) | ✅ | ✅ | Projected geometry |
| SRTM Elevation (m) | ✅ **NEW** | ✅ **NEW** | Open-Elevation API (SRTM) |
| Slope / Aspect | ❌ | ❌ | Requires DEM raster |
| TWI (Topographic Wetness) | ❌ | ❌ | Requires DEM raster |
| Land Cover / LULC | ❌ | ❌ | Not available |
| Sub-district rainfall | ❌ | ❌ | No sub-district stations |

## Step 5B: SRTM Elevation Acquisition

Successfully fetched real SRTM-derived elevation for:
- **187 blocks** → `data/spatial/derived/block_elevation.csv`
- **1,710 panchayats** → `data/spatial/derived/panchayat_elevation.csv`

### Intra-District Elevation Variation

| District | Blocks | Elev Range (m) | Std (m) | GPs | GP Elev Range (m) |
|----------|--------|-----------------|---------|-----|---------------------|
| Purulia | 20 | 133–309 (176) | 50.1 | 170 | 3–564 (**446**) |
| Alipurduar | 8 | 53–162 (109) | 36.4 | 62 | 220 |
| Jalpaiguri | 9 | 79–151 (72) | 30.0 | 55 | **306** |
| Jhargram | 8 | 43–149 (106) | 33.9 | 79 | 205 |
| Bankura | 22 | 27–205 (178) | 43.3 | 190 | 176 |
| Hooghly | 18 | 4–24 (20) | 5.0 | 206 | 44 |
| Nadia | 18 | 6–21 (15) | 4.5 | 176 | 21 |

Significant elevation variation exists, particularly in Purulia (plateau),
Jalpaiguri/Alipurduar (foothills), and Bankura/Jhargram (laterite hills).

## Step 5C: Scientific Validation Assessment

### Cross-District Correlation Analysis

| Predictor | vs Rainfall | r | p-value |
|-----------|------------|-----|---------|
| **Elevation** | Mean rain | **-0.019** | **0.952** |
| **Latitude** | Mean rain | **0.947** | **<0.001** |
| **Elevation** | Heavy rain % | **0.065** | **0.841** |
| **Latitude** | Heavy rain % | **0.960** | **<0.001** |

> **KEY FINDING**: Elevation has *zero* correlation with monsoon rainfall
> across our 12 districts. **Latitude is the dominant spatial predictor**
> (R²=0.917 with latitude+elevation, but latitude coefficient=3.58 while
> elevation coefficient=-0.015).

### Why Spatial Downscaling Cannot Be Validated

**Fundamental Problem**: All training/observation data exists at a single
point per district. We have NO sub-district ground truth.

1. **No validation target**: Cannot verify "block X at 200m gets 10% more
   rain than block Y at 50m" because we only observe rainfall at the
   district centroid.

2. **Elevation-rainfall relationship is weak**: Cross-district analysis
   shows r=-0.019 (effectively zero). The Terai/Teesta districts (high
   latitude, moderate elevation) get 3-5× more rain than Purulia (highest
   elevation).

3. **Monsoon dynamics are latitude-driven**: In West Bengal, the monsoon
   trough and Bay of Bengal moisture flux determine spatial rainfall patterns
   far more than local orography.

4. **Leave-one-out sanity check**: LOO-CV with 12 points achieves 21.3%
   relative MAE, but this tests *inter*-district variation, not
   *intra*-district downscaling.

### Decision

> **RETAIN `NONE_DISTRICT_INHERITED`**
>
> A scientifically defensible spatial downscaling model CANNOT be built
> with the available data. Any block-level probability adjustment would
> be statistically unvalidatable and violate the SIH26086 scientific
> integrity requirements.

## What We CAN Do (Step 5D Implementation)

While validated downscaling is not possible, we can meaningfully improve
the spatial metadata:

1. **Embed real SRTM elevation** into block and panchayat forecast outputs
2. **Store centroid coordinates** for each sub-district unit
3. **Transparently document** the downscaling status and data gap
4. **Future-proof** the schema for when sub-district AWS data becomes available
5. **Update the spatial output contract** to include elevation metadata

### Files to Modify

1. `src/spatial_forecast.py` — Add elevation enrichment to block and
   panchayat forecast layers
2. `reports/step5_spatial_audit.md` — This report (created)
3. `data/spatial/derived/block_elevation.csv` — Block elevation data (created)
4. `data/spatial/derived/panchayat_elevation.csv` — GP elevation data (created)

### Files NOT Modified
- `src/forecast_engine.py` — No changes (models unchanged)
- `models/` — No model retraining
- `backend/` — No API changes needed
- `frontend/` — No changes needed

## Verification Plan

1. Run existing 62+ pytest tests — all must pass
2. Run spatial forecast pipeline — verify output includes elevation metadata
3. Verify `downscaling_method` remains `NONE_DISTRICT_INHERITED`
4. Frontend build passes
