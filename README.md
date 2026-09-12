# VARSHASENTINEL (SIH 26086)
### AI-Powered Sub-District Agrometeorological Intelligence & Calibrated Monsoon Risk Engine

<img width="1426" height="808" alt="VARSHASENTINEL Architecture" src="https://github.com/user-attachments/assets/9ed9efac-4f81-4c4a-8551-c652dd03ab90" />

---

## Executive Summary
**VARSHASENTINEL** is a physics-informed, machine learning and spatial intelligence platform engineered for sub-district and Gram Panchayat level agrometeorological forecasting across West Bengal, India.

The platform addresses critical agricultural risk management challenges by integrating:
1. **Calibrated Multi-Head Machine Learning**: Six distinct operational forecast heads calibrated for out-of-sample reliability (Brier Score, PR-AUC).
2. **Teleconnection Feature Store**: Real-time integration of macro-climatic drivers including the Indian Ocean Dipole (BoM weekly & NOAA HadISST DMI), Madden-Julian Oscillation (MJO), and Nino3.4 anomalies.
3. **Geospatial Administrative Hierarchy**: Boundary reconciliation bridging Survey of India (SOI) 41,322 village geometries with official Local Government Directory (LGD) codes, producing 100% complete coverage for all **353 CD Blocks** and safe boundary representations for **3,243 Gram Panchayats**.
4. **Physically Downscaled Advisory Layer**: Topographic lapse-rate adjustment, elevation-dependent precipitation downscaling, and rule-based Agronomic Advisory Service (AAS) guidance for field-level decision support.

---

## Directory Architecture

```
SIH_26086/
├── .gitignore                   # Enterprise-grade git exclusion rules
├── README.md                    # System documentation and architecture guide
│
├── data/
│   ├── raw/
│   │   ├── weather/             # Historical meteorological datasets (2020–2025)
│   │   │   ├── gangetic_alluvial_zone_2020_2025.csv
│   │   │   ├── red_laterite_zone_2020_2025.csv
│   │   │   └── terai_teesta_zone_2020_2025.csv
│   │   ├── boundaries/          # Primary administrative boundary sources
│   │   │   ├── Village_Gram_Panchayat_Mapping_2026-09-12_21-42-27.xlsx
│   │   │   └── WEST_BENGAL/     # Survey of India village shapefile
│   │   └── climate_indices/     # Macro-climatic teleconnections
│   │       ├── bom_iod_weekly_raw.txt
│   │       ├── noaa_dmi_hadisst_monthly_raw.csv
│   │       └── noaa_dmi_hadisst_monthly_raw.data
│   │
│   ├── processed/               # Machine learning feature stores
│   │   ├── varshasentinel_master_dataset.csv
│   │   ├── varshasentinel_master_dataset.parquet
│   │   ├── varshasentinel_master_with_iod.csv
│   │   ├── varshasentinel_master_with_iod.parquet
│   │   └── spatial_forecasts/   # Published spatial forecasts & GeoJSON layers
│   │       ├── forecast_run_metadata.json
│   │       ├── latest_block_forecast.geojson
│   │       ├── latest_panchayat_forecast.geojson
│   │       └── latest_risk_map.geojson
│   │
│   └── spatial/
│       └── derived/             # Reconciled geospatial administrative boundaries
│           ├── west_bengal_blocks.geojson
│           ├── west_bengal_blocks.gpkg
│           ├── west_bengal_panchayats_safe.geojson
│           └── west_bengal_panchayats_safe.gpkg
│
├── models/                      # Calibrated machine learning artifacts
│   ├── evaluation_metrics.json  # Baseline benchmark metrics
│   ├── feature_metadata.json    # Baseline feature specifications
│   ├── target_*_xgb.joblib      # Baseline calibrated models (Dry spell heads)
│   └── iod_enhanced/            # IOD-augmented models & performance metrics
│       ├── evaluation_metrics.json
│       ├── feature_metadata.json
│       └── target_*_xgb.joblib  # Calibrated models (Onset, False Onset, Revival, Rain)
│
├── notebooks/                   # Exploratory analysis notebooks
│   ├── gangetic_alluvial_zone.ipynb
│   ├── red_laterite_zone.ipynb
│   └── terai_teesta_zone.ipynb
│
├── reports/                     # Audit logs, reconciliation tables & technical memos
│   ├── data_inventory.md
│   ├── data_quality_report.md
│   ├── missing_data_report.md
│   ├── unified_ml_schema.md
│   ├── iod_data_audit.md
│   ├── iod_feature_integration.md
│   ├── model_audit.md
│   ├── monsoon_model_results.md
│   ├── gp_mapping_reconciliation.md
│   ├── panchayat_boundary_validation.md
│   ├── spatial_data_audit.md
│   └── temperature_corrections.csv
│
├── src/                         # Production application code
│   ├── forecast_engine.py       # Inference pipeline & multi-model orchestrator
│   ├── generate_monsoon_targets.py  # Data cleaning & target definition generator
│   ├── predict.py               # Standalone prediction script
│   ├── spatial_forecast.py      # Downscaling engine & GeoJSON exporter
│   ├── train_monsoon_models.py  # Baseline model training routine
│   ├── train_iod_models.py      # IOD-enhanced model training routine
│   ├── features/
│   │   └── integrate_iod.py     # Teleconnection feature engineering
│   └── spatial/
│       ├── audit_missing_gps.py # LGD-SOI alignment auditor
│       ├── build_block_boundaries.py      # Dissolve to 353 CD Blocks
│       ├── build_panchayat_boundaries.py  # Dissolve to Gram Panchayats
│       ├── reconcile_lgd_soi.py # Reconcile LGD and SOI keys
│       ├── spatial_loader.py    # Spatial boundary & centroid loader
│       └── spatial_validation.py# Geometric validity & coordinate sanity checks
│
└── tests/                       # Automated regression test suite
    ├── test_forecast_engine.py
    ├── test_iod_integration.py
    ├── test_spatial.py
    └── test_spatial_forecast.py
```

---

## Machine Learning Forecast Heads

| Target Key | Horizon & Definition | Optimal Model Checkpoint | Verification Metric |
| :--- | :--- | :--- | :--- |
| `target_onset_window_14d` | Monsoon onset within next 14 days | `models/iod_enhanced/` | PR-AUC: 0.8817 (+0.0232) |
| `target_false_onset_flag` | High rain followed by $\ge 7\text{d}$ dry spell | `models/iod_enhanced/` | ROC-AUC: 0.8504 (+0.0116) |
| `target_dry_spell_5d_14d` | $\ge 5$-day dry spell in next 14 days | `models/` (Baseline) | Brier: 0.1420 (Zero Overfit) |
| `target_dry_spell_7d_21d` | $\ge 7$-day severe break in next 21 days | `models/` (Baseline) | Brier: 0.0890 (Sharp Calibration)|
| `target_revival_7d` | Monsoon revival within 7 days | `models/iod_enhanced/` | ROC-AUC: 0.8920 (+0.0046) |
| `target_heavy_rain_7d` | $\ge 64.5\text{ mm}$ daily or $\ge 150\text{ mm}$ 3d | `models/iod_enhanced/` | Precision: 0.8421 (+0.0363) |

---

## Quickstart & Operational Usage

### 1. Environment Activation
Activate the project Python environment:
```powershell
.\.venv\Scripts\activate
```

### 2. Running Automated Tests
Run the comprehensive 29-test validation suite:
```powershell
.\.venv\Scripts\python.exe -m unittest discover tests
```

### 3. Executing the Spatial Forecast Pipeline
Generate downscaled risk maps across all 353 Blocks and Gram Panchayats:
```powershell
.\.venv\Scripts\python.exe src/spatial_forecast.py
```
Output artifacts are saved into `data/processed/spatial_forecasts/`:
- `latest_block_forecast.geojson`
- `latest_panchayat_forecast.geojson`
- `latest_risk_map.geojson`
- `forecast_run_metadata.json`

---

## License & Attribution
Developed for the Smart India Hackathon (SIH 26086).
Geospatial data sourced from Survey of India (SOI) and Ministry of Panchayati Raj Local Government Directory (LGD).
Macro-climatic indices provided by Bureau of Meteorology (BoM) and NOAA PSL.
