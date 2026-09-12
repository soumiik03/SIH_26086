# VARSHASENTINEL (SIH26086) — Spatial Data Gap Report

**Project**: VARSHASENTINEL — Hyperlocal Monsoon Intelligence System for West Bengal  
**Subsystem**: Chapter 5 — Spatial Data Foundation for Block & Panchayat Downscaling  
**Lead Engineer**: Lead ML & Climate-Data Engineer  
**Date**: September 2026  
**Status**: Real Spatial Asset Audit Completed — Data Gap Identified  

---

## 1. Executive Summary

The Smart India Hackathon Problem Statement (SIH26086) mandates:
> *"7-to-30-day probabilistic outlook of monsoon behavior at the Block and Panchayat (Village cluster) scale."*

A comprehensive forensic inspection of the codebase confirms that:
1. **Existing Spatial Assets**: The project currently contains only tabular district-level records with 12 single-point centroid coordinates (one latitude/longitude pair per district).
2. **Missing Spatial Assets**: **No vector boundary datasets (Shapefiles, GeoJSON, GeoPackage, KML, TopoJSON) exist** in the repository for:
   * District administrative boundaries
   * Community Development (CD) Block boundaries
   * Gram Panchayat (Village Cluster / GP) boundaries
3. **Strict Compliance Policy**: In adherence to engineering integrity rules:
   * **No synthetic polygons or dummy coordinates have been fabricated**.
   * Downscaled Panchayat probabilities must not be simulated or claimed as real without authentic administrative boundary polygons.

This document identifies the exact datasets required, authoritative government and scientific sources, required attributes, and the spatial schema required to ingest real boundary vectors.

---

## 2. Inventory of Required Spatial Datasets

To establish real spatial downscaling across West Bengal, the following 4 official datasets must be acquired:

| Level / Layer | Entity Count (WB Statewide) | Entity Count (12 Project Districts) | Required Geometry | Authoritative Custodian |
| :--- | :---: | :---: | :---: | :--- |
| **1. District Boundaries** | 23 Districts | 12 Districts | MultiPolygon (`EPSG:4326`) | Survey of India (SoI) / BharatMaps (NIC) |
| **2. CD Block Boundaries** | 345 Blocks | ~170 Blocks | MultiPolygon (`EPSG:4326`) | Panchayats & Rural Development (P&RD), WB / Census of India |
| **3. Gram Panchayat Boundaries** | 3,342 GPs | ~1,650 GPs | MultiPolygon (`EPSG:4326`) | GIS Cell, P&RD Dept, Govt of West Bengal |
| **4. Digital Elevation Model (DEM)** | Full State Raster | Full 12 Districts | GeoTIFF (30m Resolution) | ISRO Bhuvan (CartoDEM) / Copernicus DEM GLO-30 |

---

## 3. Authoritative Sources & Acquisition Procedures

### 3.1 Survey of India (SoI) & BharatMaps (NIC)
* **Custodian**: National Mapping Agency of India (DST) and National Informatics Centre (MeitY).
* **Portal**: [BharatMaps Multi-Layer GIS](https://bharatmaps.gov.in/) & [Survey of India Nakshe](https://onlinemaps.surveyofindia.gov.in/)
* **Asset**: National Administrative Boundaries (State, District, Sub-District/Tehsil).
* **Standard**: Conforms to the National Geospatial Policy (NGP 2022).

### 3.2 Panchayats & Rural Development (P&RD) Department, Govt of West Bengal
* **Custodian**: GIS Cell, Department of Panchayats & Rural Development, Joint Administrative Building, Salt Lake, Kolkata.
* **Portal**: [wbprd.gov.in](https://wbprd.gov.in/) & WB State Spatial Data Infrastructure (WBSDI).
* **Asset**: The definitive official cadastral and Gram Panchayat boundary shapefiles for all 3,342 Gram Panchayats across the 3-tier Panchayati Raj system (Zilla Parishad → Panchayat Samiti/Block → Gram Panchayat).

### 3.3 Local Government Directory (LGD) — Ministry of Panchayati Raj (MoPR)
* **Custodian**: Ministry of Panchayati Raj, Government of India.
* **Portal**: [lgd.gov.in](https://lgd.gov.in/)
* **Asset**: Standardized national spatial census identifiers (`LGD Code`) mapping every Gram Panchayat to its parent Block, District, and State.

### 3.4 Open Government Data & Open Spatial Initiatives
* **DataMeet Spatial Repository**: Community-validated, open-source Indian administrative boundaries curated from Census of India 2011 and Election Commission shapefiles (`github.com/datameet/maps`).
* **Bhuvan (ISRO / NRSC)**: Satellite-derived 30m CartoDEM elevation rasters and 1:50,000 Land Use / Land Cover (LULC) vector shapefiles for West Bengal.

---

## 4. Standardized Administrative Downscaling Schema

Once authentic boundaries are acquired, they must be formatted into the following unified schema:

```
spatial_schema/
├── district_id         : VARCHAR(32)   -- Standard LGD or Snake_Case (e.g. 'wb_purba_bardhaman')
├── district_name       : VARCHAR(64)   -- Official district name (e.g. 'Purba Bardhaman')
├── block_id            : VARCHAR(32)   -- Unique Block LGD code (e.g. 'wb_blk_bhatar')
├── block_name          : VARCHAR(64)   -- Community Development Block name (e.g. 'Bhatar')
├── panchayat_id        : VARCHAR(32)   -- Unique Gram Panchayat LGD code (e.g. 'wb_gp_barabelun1')
├── panchayat_name      : VARCHAR(64)   -- Gram Panchayat name (e.g. 'Barabelun I')
├── centroid_lat        : FLOAT32       -- Geometric interior centroid latitude (°N, EPSG:4326)
├── centroid_lon        : FLOAT32       -- Geometric interior centroid longitude (°E, EPSG:4326)
├── elevation_mean_m    : FLOAT32       -- Zonal mean elevation above sea level (meters)
├── agro_climatic_zone  : VARCHAR(32)   -- 'gangetic_alluvial' | 'red_laterite' | 'terai_teesta'
├── geometry            : GEOMETRY      -- Validated OGC Polygon or MultiPolygon in WGS84
└── parent_hierarchy    : JSON          -- Nested structural lineage {state, district, block}
```

---

## 5. Technical Requirements for Ingested Vectors

To ensure seamless integration with the Python downscaling engine and future WebGL/MapLibre frontend:
1. **Coordinate Reference System (CRS)**: Must be strictly **WGS 84 (EPSG:4326)** (Latitude/Longitude in decimal degrees). Projections such as UTM 45N (EPSG:32645) must be reprojected.
2. **Topological Cleanliness**:
   * Zero self-intersecting rings (`is_valid == True`).
   * No sliver polygons or unclosed linear rings.
   * Planar enforcement: Adjacent panchayats must share identical vertices without micro-overlaps or void gaps.
3. **Data Volume & Web Optimization**:
   * Full-state GP boundaries in raw cadastral resolution typically exceed 150 MB.
   * Vector simplification using the Douglas-Peucker algorithm with topological preservation (Visvalingam-Whyatt) must target an optimized MapLibre-ready GeoJSON of $< 12\text{ MB}$.
