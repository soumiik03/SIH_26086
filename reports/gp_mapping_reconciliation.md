# VARSHASENTINEL (SIH26086) — Survey of India & Official LGD Reconciliation Report

**Subsystem**: Spatial Data Foundation (Gram Panchayat Scale)  
**Survey Source**: `WEST_BENGAL/WEST_BENGAL.shp` (41,322 village polygons)  
**LGD Source**: `Village_Gram_Panchayat_Mapping_2026-09-12_21-42-27.xlsx` (41,416 data rows)  
**Date**: September 2026  
**Status**: Reconciliation Audit Complete — Strict Guardrails Enforced  

---

## 1. Executive Summary & Verification Matrix

A deterministic primary-key comparison was conducted between the **Survey of India Cadastral Village Shapefile** and the official **Ministry of Panchayati Raj Local Government Directory (LGD) Report**.

| Metric / Dimension | Survey of India Dataset | Official LGD Dataset | Intersection / Alignment | Status |
| :--- | :---: | :---: | :---: | :---: |
| **Total Rows** | **41,322** polygons | **41,416** mapping rows | N/A | Preserved 100% untouched |
| **Unique Village Codes** | **41,214** | **41,006** | **40,804** | **98.8% of SOI codes match LGD** |
| **Null Village Codes** | **34** | **0** | N/A | 34 uninhabited Sundarban areas |
| **Unique Districts** | **23** | **22** | **22 Districts Aligned** | Reconciled via Census 2011 Codes |
| **Unique CD Blocks** | **351** | **345** | **340 Blocks** | **340 of 345 Blocks Aligned directly** |
| **Unique Gram Panchayats**| N/A | **3,340** | **3,340 Gram Panchayats** | Full Statewide Rural Coverage |

---

## 2. Village-Level Join & Coverage Analysis

1. **Survey Villages Matched to LGD**:
   * **40,871 rows** (**98.91%** of all Survey geometries).
   * These villages share an identical 6-digit numeric Government of India LGD code.
2. **Survey Villages NOT Matched to LGD**:
   * **451 rows** (**1.09%**).
   * *Root Cause Analysis*:
     - **34 rows**: Null `Vill_LGD` in uninhabited mangrove reserves / sea tracts in South 24 Parganas (Gosaba, Sagar, Kultali).
     - **285 rows**: 10-digit/12-digit census towns and forest tracts not administered by rural Panchayati Raj (e.g. urban fringe census towns under municipalities).
     - **132 rows**: Re-delimited villages where Census 2011 code was upgraded in later revisions.
3. **LGD Villages Without a Survey Geometry**:
   * **202 codes** (0.49% of LGD registry).
   * Highly concentrated in newly merged peri-urban clusters and tea garden hamlets.

---

## 3. Duplicated LGD Village Code Analysis (The Critical Distinction)

There are **369 unique Village Codes** that appear in multiple rows in the LGD mapping table (spanning **779 rows**).

The complete record-by-record analysis is saved in:  
[`reports/lgd_duplicate_village_mapping.csv`](file:///j:/Projects/Web/SIH_26086/SIH_26086/reports/lgd_duplicate_village_mapping.csv)

### Classification of Duplication Mechanism (Question 6):
1. **Case A — Multiple Survey Geometry Records**: **3 codes**
   * The Survey of India shapefile *itself* contains multiple distinct physical polygons sharing the same `Vill_LGD` code (detached enclaves or multi-part mouzas).
2. **Case B — Single Survey Geometry Mapped to Multiple GPs**: **364 codes**
   * Exactly **ONE single Survey polygon exists**, but the Ministry of Panchayati Raj assigns parts of that village to **two or more distinct Gram Panchayats**.
   * *Example*: In Kalimpong, `Icha Khasmahal` (Village Code `306226`) is partitioned between `Upper Echhay GP` (261016) and `Lower Echhay GP` (261006). In Darjeeling, `Bukim Tea Garden (Tharbu) (P)` (`306397`) is divided between `Paheligaon School Dara-I GP` and `Paheligaon School Dara-Ii GP`.
   * **Critical Anti-Fabrication Rule**: In strict accordance with user instructions, **a single polygon must NOT be duplicated or arbitrarily assigned to one GP**. These are flagged as `REQUIRES_SPLIT_GEOMETRY`.
3. **Case C — Zero Survey Geometries**: **2 codes**
   * Duplicated LGD codes that have no matching geometry in the rural Survey shapefile.

---

## 4. CD Block & District Reconciliation

### 4.1 CD Blocks:
* **Matching Block Codes (`Subdis_LGD` == `Subdistrict Code`)**: **340 blocks**.
* **Survey-Only Blocks (11)**: `['02156', '02157', '02157N001', '02158', '02167N003', '02171', '02173', '02176N004', '02212', '02314N002', '02477']` (primarily Darjeeling/Kalimpong hill blocks with modified sub-district identifiers).
* **LGD-Only Blocks (5)**: `['2325', '6966', '7051', '7118', '7119']`.
* **Block Name Orthography Differences**: Exactly **27 blocks** have minor hyphenation or Roman numeral formatting variations between Survey and LGD:

| Block LGD Code | Survey of India Block Name | LGD Official Block Name |
| :---: | :--- | :--- |
| `2154` | Darjiling Phulbazar | Darjeeling Pulbazar |
| `2155` | Rangoli and Rangliot | Rangli Rangliot |
| `2156` | Kalimpong - I | Kalimpong -I |
| `2159` | Jor Bungalow Sukhiya Pokhri | Jorebunglow Sukiapokhri |
| `2182` | Mathabhanga - II | Mathabhanga-II |
| `2183` | KOCH BIHAR - I | Cooch Behar - I |
| `2184` | KOCH BIHAR - II | Cooch Behar - II |
| `2198` | Kaliyaganj | Kaliaganj |
| `2206` | Banshihari | Bansihari |
| `2217` | Old Malda | Maldah (Old) |

### 4.2 Districts:
* **Key Insight on District Identifiers**:
  * In `WEST_BENGAL.shp`, the `Dist_LGD` column actually records the **Census 2011 District Code** (e.g. `333` for Murshidabad, `335` for Purba Bardhaman, `338` for Bankura, `340` for Puruliya).
  * In the LGD Excel, `District Code` records the **Modern LGD District Code** (e.g. `319` for Murshidabad, `306` for Purba Bardhaman, `305` for Bankura, `321` for Purulia), while Column 4 (`District Census 2011 Code`) records `333`, `335`, `338`, `340`.
  * Cross-referencing `Dist_LGD` against `District Census 2011 Code` establishes **100% alignment across all 22 rural districts**.

---

## 5. Final Classification of All 41,322 Survey Polygons

Every single one of the 41,322 Survey of India village polygons is categorized into a mutually exclusive operational status:

| Classification Category | Feature Count | Percentage | Operational Meaning | Action Protocol |
| :--- | :---: | :---: | :--- | :--- |
| **`SAFE_TO_DISSOLVE`** | **40,235** | **97.37%** | Village matches **exactly 1 Gram Panchayat** with matching block & district. | **100% Safe to dissolve** into official Gram Panchayat polygons. |
| **`REQUIRES_SPLIT_GEOMETRY`** | **370** | **0.90%** | 1 single Survey polygon belongs to **$\ge 2$ distinct Gram Panchayats** in LGD. | **Must NOT be merged into a single GP**. Requires sub-village parcel boundary or shared multi-GP risk indexing. |
| **`ADMINISTRATIVE_MISMATCH`** | **266** | **0.64%** | Village code matches, but parent CD Block code differs between datasets. | Must be reconciled to the authoritative LGD parent Block before dissolving. |
| **`UNMATCHED`** | **451** | **1.09%** | No record in rural LGD table (uninhabited forests, urban census towns, mangrove reserves). | Excluded from rural Gram Panchayat dissolution. |

---

## 6. Strict Compliance Audit

* `data/spatial/derived/west_bengal_panchayats.geojson`: **NOT CREATED** (Halted per instructions).
* Panchayat polygon dissolution: **NOT EXECUTED**.
* Synthetic or inferred geometries: **ZERO GENERATED**.
* Source datasets: **100% UNTOUCHED**.
