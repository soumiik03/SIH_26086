# VARSHASENTINEL (SIH26086) — Spatial Data & Downscaling Architecture Audit

**Project**: VARSHASENTINEL — Hyperlocal Monsoon Intelligence System for West Bengal  
**Subsystem**: Chapter 5 — Spatial Data Foundation for Block & Panchayat Downscaling  
**Lead Engineer**: Lead ML & Climate-Data Engineer  
**Date**: September 2026  
**Document**: `reports/spatial_data_audit.md`  
**Status**: Formal Audit Completed  

---

## 1. Spatial Audit of Existing Assets

An exhaustive recursive search across all directories in the repository was conducted for spatial vector formats (`.geojson`, `.shp`, `.gpkg`, `.kml`, `.topojson`) and raster grids (`.tif`, `.nc`, `.hdf`).

```
╔══════════════════════════════════════════════════════════════════════════════════════╗
║ REAL BOUNDARY ASSET INVENTORY                                                       ║
║ District Polygon Boundaries : 0 files found (Missing)                               ║
║ CD Block Polygon Boundaries  : 0 files found (Missing)                               ║
║ Gram Panchayat Boundaries    : 0 files found (Missing)                               ║
║ Digital Elevation Rasters    : 0 files found (Missing)                               ║
║ Tabular District Centroids   : 12 Points Available (WGS 84, Lat/Lon)                 ║
║ Geometry Validation Status   : NO DUMMY OR SYNTHETIC GEOMETRIES FABRICATED          ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
```

### Existing Tabular Spatial Assets (12 District Centroids)
The project currently possesses 12 authentic centroid coordinate pairs embedded in the primary daily datasets:
1. **Gangetic New Alluvial Zone (4 Centroids)**:
   * `Purba_Bardhaman`: 23.25°N, 87.85°E
   * `Hooghly`: 22.88°N, 87.78°E
   * `Nadia`: 23.40°N, 88.50°E
   * `Murshidabad`: 24.10°N, 88.25°E
2. **Red & Laterite Zone (4 Centroids)**:
   * `Purulia`: 23.33°N, 86.36°E
   * `Bankura`: 23.23°N, 87.07°E
   * `Jhargram`: 22.45°N, 86.98°E
   * `Birbhum_Suri`: 23.91°N, 87.53°E
3. **Terai-Teesta Zone (4 Centroids)**:
   * `Jalpaiguri`: 26.54°N, 88.72°E
   * `Alipurduar`: 26.49°N, 89.53°E
   * `Cooch_Behar`: 26.32°N, 89.45°E
   * `Siliguri_Foothill`: 26.71°N, 88.43°E

*Coordinate Reference System (CRS)*: **WGS 84 (EPSG:4326)** decimal degrees.

---

## 2. Downscaling Architecture: From District Forecasts to Panchayat Risk

Because numerical weather models, global reanalysis, and IMD synoptic stations operate at district or gridded resolutions ($0.25^\circ \times 0.25^\circ \approx 27\text{ km} \times 27\text{ km}$), predicting at the **Block** ($\approx 10\text{ km}$) and **Panchayat** ($\approx 2\text{ km} - 5\text{ km}$) scale requires a **physically constrained downscaling engine**:

```
┌────────────────────────────────────────────────────────┐
│               DISTRICT ML FORECAST                     │
│  Calibrated Probabilities P(E_district) for 6 Events    │
│  (Onset, False Onset, Dry Breaks, Heavy Rain, Revival) │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│             LOCAL SPATIAL COVARIATES                   │
│  ├── High-Resolution Elevation & Slope (DEM 30m)       │
│  ├── Distance to Waterbodies / River Basins            │
│  ├── Land Use / Land Cover (LULC & Vegetation Index)   │
│  ├── Topographic Wetness Index (TWI)                   │
│  └── Microclimatic Agro-Ecological Sub-Zone            │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│             BLOCK-LEVEL CONDITIONING                   │
│  Spatial covariate anomaly Δ_block relative to         │
│  district mean:                                        │
│  P(E_block) = σ(logit(P_district) + β^T · Δ_block)     │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│           PANCHAYAT-LEVEL DOWNSCALING                  │
│  Hyperlocal topographic and soil moisture adjustment:  │
│  - Waterlogging risk amplified in low-lying alluvial   │
│    and foothill floodplains (high TWI)                 │
│  - Drought stress amplified on elevated, rocky laterite│
│    uplands (low TWI, low moisture retention)           │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│           PROBABILISTIC RISK SURFACE                   │
│  Continuous vector surface ready for GeoJSON tile-     │
│  serving to MapLibre / WebGL interactive frontend      │
└────────────────────────────────────────────────────────┘
```

---

## 3. Critical Scientific Distinction: Observational vs Downscaled Resolution

> [!IMPORTANT]
> **A downscaled Panchayat probability is NOT an in-situ Panchayat observation.**
> The system strictly enforces the following scientific taxonomy:

1. **Observational & Model Validation Resolution (District Scale)**:
   * Where ground truth is measured by automatic weather stations (AWS), rain gauges, and satellite calibration.
   * **Brier score, ROC-AUC, PR-AUC, and F1 metrics** are verified at this level against actual historical rainfall and temperature.
   * Models can only be validated where ground truth exists.
2. **Operational Downscaled Resolution (Block & Panchayat Scale)**:
   * Represents a **spatial risk surface** conditioned on local physiographic features (orographic lift, valley pooling, soil drainage).
   * It provides farmers and panchayat pradhans with differential hazard vulnerability within the same district (e.g. an upland block in Purulia has higher dry break vulnerability than an adjacent riverine block).
   * It must be presented to users as an *operational hazard estimation*, not a direct local station recording.

---

## 4. Operational Readiness Status

| Milestone | Status | Description |
| :--- | :---: | :--- |
| **District Centroid Geometries** | ✅ Ready | 12 districts verified with valid coordinates in WGS 84. |
| **Downscaling Architecture** | ✅ Ready | Mathematical formulation and covariate integration pipeline mapped. |
| **Spatial Ingestion & Validation Code** | ✅ Ready | `src/spatial/spatial_loader.py` and `src/spatial/spatial_validation.py` implemented. |
| **Real Polygon Boundary Files** | ❌ Missing | No official SoI/Census shapefiles currently in repository. |
| **MapLibre Validated GeoJSON** | ⏸️ Paused | Strictly deferred until authentic government shapefiles are provided (preventing fake geometry generation). |
