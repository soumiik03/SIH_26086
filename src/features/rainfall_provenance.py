"""Provenance and point-in-time controls for rainfall products.

This module deliberately does not synthesize local rainfall or perform spatial
downscaling.  It records the source contract needed before a real gridded
rainfall product can be integrated and provides the common availability rule
for leakage-safe historical replay.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict


RAINFALL_SOURCE_CATALOG: Dict[str, Dict[str, Any]] = {
    "project_zone_centered_weather": {
        "provider": "Not documented in repository",
        "product": "VARSHASENTINEL zone weather CSVs",
        "observation_type": "district-representative proxy; source measurement type unverified",
        "spatial_resolution": "one representative coordinate per district; no grid resolution",
        "temporal_resolution": "daily",
        "coverage": "2020-01-01 through 2025-12-31",
        "units": "millimetres per daily accumulation, per column name",
        "local_panchayat_suitability": False,
    },
    "imd_daily_gridded_025": {
        "provider": "India Meteorological Department",
        "product": "Daily gridded rainfall over India",
        "observation_type": "gauge-derived gridded analysis",
        "spatial_resolution": "0.25 degree x 0.25 degree",
        "temporal_resolution": "daily",
        "coverage": "1901-01-01 through 2024-12-31 in the documented archive",
        "units": "millimetres",
        "local_panchayat_suitability": "candidate; requires validation and area-weighted aggregation",
    },
    "nasa_imerg_v07b_final": {
        "provider": "NASA Global Precipitation Measurement mission",
        "product": "IMERG V07B Final",
        "observation_type": "satellite multi-sensor precipitation estimate with gauge adjustment",
        "spatial_resolution": "0.1 degree x 0.1 degree",
        "temporal_resolution": "half-hourly, with daily accumulations available",
        "coverage": "1998-01-01 to present",
        "units": "millimetres for daily accumulation products",
        "nominal_availability_latency": "approximately 3.5 months for Final Run",
        "local_panchayat_suitability": "candidate signal, not Panchayat ground truth",
    },
}


def usable_data_timestamp(observation_timestamp: datetime, availability_latency: timedelta) -> datetime:
    """Return the earliest timestamp at which an observation may be used."""
    return observation_timestamp + availability_latency


def is_available_as_of(
    observation_timestamp: datetime,
    availability_timestamp: datetime,
    forecast_reference_timestamp: datetime,
) -> bool:
    """Return whether data publication occurred by forecast issue time."""
    if availability_timestamp < observation_timestamp:
        raise ValueError("Availability timestamp cannot precede observation timestamp")
    return availability_timestamp <= forecast_reference_timestamp

