# Step 6 Rainfall Source Selection

## Candidate comparison

| Candidate | Spatial resolution | Temporal resolution | Coverage | Availability | Strength | Limitation |
|---|---:|---|---|---|---|---|
| IMD daily gridded rainfall | 0.25° × 0.25° | Daily | 1901–2024 documented archive | Historical archive | Gauge-derived Indian rainfall analysis and long climatology | Coarse relative to many Panchayats; 2025 test coverage is not in the documented archive |
| NASA GPM IMERG V07B Final | 0.1° × 0.1° | Half-hourly and daily products | 1998–present | Approximately 3.5-month Final latency | Best candidate for 2020–2025 spatial coverage and area-weighted rainfall features | Satellite/multi-sensor estimate, not Panchayat gauge truth; requires regional validation |
| NASA GPM IMERG Early/Late | 0.1° × 0.1° | Half-hourly and daily products | 1998–present | Approximately 4 hours / 14 hours | Operationally timely | Lower-latency estimates are revised and less suitable as final historical labels |
| ERA5 precipitation | 0.25° reanalysis grid | Hourly | 1940–present | Reanalysis latency | Consistent long record and easy temporal aggregation | Model/reanalysis-derived, not direct observation; coarse and not a local gauge substitute |

## Selected evaluation source

The selected candidate for a future local-rainfall evaluation is **NASA GPM IMERG V07B Final daily precipitation**, with IMD 0.25° gridded rainfall as an independent historical comparison where dates overlap.

Selection rationale:

1. It covers the complete 2020–2025 model period.
2. It provides finer spatial support than IMD 0.25° and ERA5 0.25°.
3. Daily accumulation is compatible with the existing event targets.
4. Final Run latency can be represented explicitly in historical replay.
5. It can be aggregated by polygon intersection instead of assigning one value to every Panchayat.

This is a selected candidate, not a production integration. No IMERG files are present in the repository, so no local rainfall-enhanced model was trained and no spatial routing was promoted.

Authoritative references:

- [NASA IMERG V07 technical documentation](https://gpm.nasa.gov/resources/documents/imerg-v07-technical-documentation)
- [NASA IMERG product information](https://gpm.nasa.gov/data/imerg)
- [NASA precipitation data directory](https://gpm.nasa.gov/node/3037)
- [IMD daily 0.25° gridded rainfall archive](https://www.imdpune.gov.in/cmpg/Griddata/Rainfall_25_NetCDF.html)
- [Copernicus ERA5 single-level data](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels)

## Required validation before integration

- Compare IMERG daily accumulations with available district rainfall series.
- Quantify bias, correlation, wet-day detection, and heavy-rain detection by district and season.
- Verify the product's effective support over West Bengal and small polygons.
- Use area-weighted polygon aggregation, not centroid extraction.
- Preserve `NONE_DISTRICT_INHERITED` until temporal and spatial holdout results support promotion.
