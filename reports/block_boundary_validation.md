# VARSHASENTINEL (SIH26086) — CD Block Boundary Validation Report

**Dataset**: Official Survey of India Cadastral Dissolve to CD Blocks  
**Source Path**: `WEST_BENGAL/WEST_BENGAL.shp` (Preserved untouched)  
**Output GeoJSON**: `data/spatial/derived\west_bengal_blocks.geojson`  
**Output GeoPackage**: `data/spatial/derived\west_bengal_blocks.gpkg`  
**Status**: Successfully Derived & Validated  

---

## 1. Summary of Derived Dataset

| Metric | Source Input | Derived Block Output | Status |
| :--- | :---: | :---: | :---: |
| **Total Features** | 41322 Villages | **353 CD Blocks** | ✅ Complete Statewide Coverage |
| **Number of Districts** | 22 Rural Districts | **22 Districts** | ✅ Fully Preserved |
| **Coordinate Reference System** | `LCC_WGS84` (Projected meters) | **`EPSG:4326` (WGS 84)** | ✅ Reprojected for WebGL/MapLibre |
| **Invalid Geometries** | 3 Invalid | **0 Invalid (0%)** | ✅ 100% Valid OGC Geometries |
| **Missing Block IDs (`Subdis_LGD`)** | 0 | **0** | ✅ 100% Non-Null LGD IDs |
| **Missing Block Names (`Sub_dist`)** | 0 | **0** | ✅ 100% Non-Null Names |
| **Missing / Empty Geometries** | 0 | **0** | ✅ Every block has valid polygon |
| **Compound Key Duplicates** | N/A | **0 duplicates on `(Dist_LGD, Subdis_LGD)`** | ✅ Unique Administrative Identity |

---

## 2. Schema of Derived CD Block Layer

| Field Name | Type | Description | Sample Value |
| :--- | :--- | :--- | :--- |
| `State_LGD` | Integer | West Bengal State LGD Code | `19` |
| `STATE_UT` | String | State Name | `WEST BENGAL` |
| `Dist_LGD` | String/Integer | District LGD Code | `333` |
| `District` | String | District Name | `Murshidabad` |
| `Subdis_LGD` | String/Integer | Community Development Block LGD Code | `2248` |
| `Sub_dist` | String | Community Development Block Name | `Burwan` |
| `Subdis_Typ` | String | Administrative Classification | `CD_Block` |
| `village_count`| Integer | Number of source villages dissolved into this block | `148` |
| `geometry` | MultiPolygon | OGC Boundary in WGS 84 decimal degrees | `MULTIPOLYGON (((88.01 23.95...)))` |

---

## 3. Handling of Source Anomalies

1. **`Subdis_Typ` Case Normalization**:
   * The source shapefile contained 37,009 entries labeled `CD_Block` and 4,311 entries labeled `CD_BLOCK` (in Bankura and Jalpaiguri districts).
   * Both were preserved and normalized to standard `"CD_Block"`.
   * Exactly 2 non-CD Block entries were excluded:
     - Row 37315: `Kolkata (M Corp)` (`Subdis_Typ == 'Sub_Division'`, urban municipal corporation without rural CD blocks).
     - Row 40064: `Darjeeling Hilldoars Tea Garden` in Kalimpong (`Subdis_Typ == 'RD_Block'`).
2. **Spelling Typo Harmonization**:
   * `Kalna - l` (lowercase l) normalized to `Kalna - I` (Purba Bardhaman, LGD 2293).
   * `Nax<lbari` (stray character typo) normalized to `Naxalbari` (Darjiling, LGD 2163).
3. **Compound Primary Key Requirement**:
   * Two `Subdis_LGD` codes (2393 and 2394) are shared across distinct districts:
     - 2393 represents *Balarampur* in Puruliya (340) and *Balarampur* in South 24 Parganas (343).
     - 2394 represents *Barabazar* in Puruliya (340) and *Barasat - I* in North 24 Parganas (337).
   * Enforcing the compound key `(Dist_LGD, Subdis_LGD)` eliminates ambiguity and ensures 353 distinct, authentic administrative CD Blocks.
