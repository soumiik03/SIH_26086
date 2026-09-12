# VARSHASENTINEL (SIH26086) — Gram Panchayat Boundary Validation Report (Safe Layer)

**Dataset**: Official Gram Panchayat Safe Boundary Layer (`west_bengal_panchayats_safe`)  
**Survey Source**: `WEST_BENGAL/WEST_BENGAL.shp` (41,322 village polygons)  
**LGD Source**: `Village_Gram_Panchayat_Mapping_2026-09-12_21-42-27.xlsx` (41,416 rows, 3,339 rural Gram Panchayats)  
**Output GeoJSON**: `data/spatial/derived\west_bengal_panchayats_safe.geojson`  
**Output GeoPackage**: `data/spatial/derived\west_bengal_panchayats_safe.gpkg`  
**Date**: September 2026  
**Status**: Successfully Derived & Validated (Strict SAFE_TO_DISSOLVE Protocol)  

---

> [!IMPORTANT]
> **Scope & Coverage Declaration**:
> This dataset represents the **SAFE/verified Gram Panchayat layer** (97.45% statewide GP coverage).
> - It includes **ONLY** villages with unambiguous 1-to-1 mappings between Survey of India cadastral polygons and MoPR Local Government Directory records.
> - Exactly **371 multi-GP village polygons** (`REQUIRES_SPLIT_GEOMETRY`) were **EXCLUDED** to prevent geographic corruption, artificial polygon assignment, or boundary duplication.
> - **DO NOT claim this is 100% boundary coverage.** The remaining 85 Gram Panchayats in West Bengal require cadastral sub-parceling or multi-GP association tags before boundary synthesis.

---

## 1. Boundary Derivation & Validation Metrics

| Metric / Dimension | Value | Target / Baseline | Audit Finding & Explanation |
| :--- | :---: | :---: | :--- |
| **Total Features Derived** | **3,321** | N/A | 3,267 genuine GP components + 54 non-panchayat tracts |
| **Unique Genuine Gram Panchayats** | **3,254** | 3,339 total in LGD | **97.45% Verified Statewide Coverage** |
| **Source Villages Used** | **40,235** | 41,322 total in SoI | **97.37% of All Cadastral Villages** |
| **Excluded Multi-GP Villages** | **371** | 370 in Audit | **100% Excluded (`REQUIRES_SPLIT_GEOMETRY`)** |
| **District Coverage** | **22 Districts** | 22 Rural Districts | **100.0% Coverage** |
| **CD Block Coverage** | **340 Blocks** | 340 Common Blocks | **100.0% Coverage** |
| **Coordinate Reference System** | **EPSG:4326 (WGS 84)** | EPSG:4326 | **100% Standardized** |
| **Invalid Geometries (OGC)** | **0** | 0 | **100% OGC Valid (Zero Self-Intersections)** |
| **Empty Geometries** | **0** | 0 | **Zero Empty Geometries** |
| **Duplicate GP LGD IDs** | **66** | 0 | Explained below: 53 from non-GP code `0` + 13 from 11 cross-block GPs |
| **Missing GP IDs / Names** | **0 / 54** | 0 | **Zero missing in genuine GPs**; 54 blanks are non-panchayat tracts (code `0`) |

---

## 2. Duplicate GP IDs & Missing Names Audit

The audit identified two distinct causes for duplicate IDs and missing names:

### 2.1 Unadministered Non-Panchayat Tracts (`Local Body Code == 0`)
- In the official MoPR LGD register, reserved forest ranges, Sundarban mangrove estuaries (e.g. Kultali, Basanti, Gosaba, Sagar), and cantonment enclaves (Barrackpur Cantt) do not have a Gram Panchayat.
- LGD assigns `Local Body Code = 0` and `Local Body Name = NaN` for these mouzas.
- Because the dissolve was grouped by `(District, Subdistrict, Local Body Code)`, code `0` produces **54 distinct block-level features**, accounting for **54 missing names** and **53 duplicate code instances**.

### 2.2 Genuine Cross-Block Gram Panchayats (11 GPs)
- In West Bengal, exactly **11 Gram Panchayats** legitimately contain revenue mouzas located in two adjacent CD Blocks:
  - `Kirnahar-I` (Birbhum: Nanoor & Labpur)
  - `Sahapur` (Birbhum: Suri-I & Suri-II)
  - `Falmari` (Cooch Behar: Dinhata-I & Sitai)
  - `Chhotosalbari` (Cooch Behar: Sitalkuchi & Mathabhanga-I)
  - `Buraganj` (Darjeeling: Phansidewa & Kharibari)
  - `Lower Bagdogra` (Darjeeling: Naxalbari & Phansidewa)
  - `Balichak` (Howrah: Shyampur-I & Shyampur-II)
  - `Changmari` (Jalpaiguri: Mal & Jalpaiguri)
  - `Beernagar-I` & `Beernagar-Ii` (Malda: Kaliachak-I & Kaliachak-III)
  - `Atpukur` (North 24 Parganas: Haroa & Minakhan)
  - `Marishda` (Purba Medinipur: Contai-III & Deshapran)
- Under the required dissolve grouping `['district_lgd_code', 'block_lgd_code', 'gp_lgd_code']`, these 11 GPs are preserved with their respective block-level components (total 13 duplicate occurrences).

---

## 3. Methodology & Guardrail Enforcement

1. **Deterministic Primary Key Join**:
   - Joined Survey of India `Vill_LGD` directly to MoPR LGD `Village Code`.
   - String normalization applied strictly to whitespace and float-formatting; zero alteration of official identifiers or names.
2. **Strict Multi-GP Exclusion**:
   - In accordance with user instructions, multi-GP villages (370 polygons representing Case A and Case B duplicates) were completely withheld from dissolution.
   - No single polygon was duplicated across multiple Panchayats.
   - No heuristic, Voronoi, or synthetic boundaries were fabricated.
3. **Hierarchical Grouping & Dissolve**:
   - Geometries dissolved strictly by `['district_lgd_code', 'district_name', 'block_lgd_code', 'block_name', 'gp_lgd_code', 'gp_name']`.
   - Geometry boundaries were inspected and auto-repaired using `shapely.validation.make_valid()`.
4. **Attribute Preservation**:
   - Primary ID: `gp_lgd_code` (MoPR `Local Body Code`).
   - Primary Name: `gp_name` (MoPR `Local Body Name (In English)`).
   - Parent Block: `block_lgd_code` (`Subdistrict Code`) and `block_name`.
   - Parent District: `district_lgd_code` (`District Code`), `district_name`, and `district_census_code`.
   - Derived metric: `village_count` recording number of constituent villages per Gram Panchayat.

---

## 4. District-Level Gram Panchayat Coverage Breakdown

| District Name | District LGD Code | Census 2011 Code | CD Blocks Covered | Safe GPs Created |
| :--- | :---: | :---: | :---: | :---: |
| Alipurduar | `664` | `0` | 6 | 62 |
| Bankura | `305` | `339` | 22 | 190 |
| Birbhum | `307` | `334` | 19 | 166 |
| Cooch Behar | `308` | `329` | 12 | 127 |
| Dakshin Dinajpur | `310` | `331` | 8 | 64 |
| Darjeeling | `309` | `327` | 9 | 91 |
| Hooghly | `312` | `338` | 18 | 206 |
| Howrah | `313` | `341` | 14 | 146 |
| Jalpaiguri | `314` | `328` | 7 | 55 |
| Jhargram | `703` | `0` | 8 | 79 |
| Kalimpong | `702` | `0` | 3 | 34 |
| Malda | `316` | `332` | 15 | 143 |
| Murshidabad | `319` | `333` | 26 | 242 |
| Nadia | `320` | `336` | 17 | 176 |
| North 24 Parganas | `303` | `337` | 21 | 190 |
| Paschim Bardhaman | `704` | `0` | 8 | 60 |
| Paschim Medinipur | `318` | `344` | 21 | 211 |
| Purba Bardhaman | `306` | `335` | 23 | 215 |
| Purba Medinipur | `317` | `345` | 25 | 223 |
| Purulia | `321` | `340` | 20 | 170 |
| South 24 Parganas | `304` | `343` | 29 | 306 |
| Uttar Dinajpur | `311` | `330` | 9 | 98 |

---

## 5. Downstream VARSHASENTINEL Integration

This dataset is stored at:
- `data/spatial/derived/west_bengal_panchayats_safe.geojson`
- `data/spatial/derived/west_bengal_panchayats_safe.gpkg`

It serves as the authentic spatial base for:
- Hyperlocal meteorological risk mapping (P(onset), P(dry spell), P(heavy rain)) downscaled from District to Block and Panchayat scales.
- Interactive visualization in the upcoming frontend dashboard.
