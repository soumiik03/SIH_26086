from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class DistrictResponse(BaseModel):
    district_id: str
    district_name: str
    meteorological_key: str


class BlockResponse(BaseModel):
    block_id: str
    block_name: str
    district_id: str
    district_name: str
    block_lgd_code: Optional[str] = None
    centroid_lat: float
    centroid_lon: float
    risk_level: str


class GeometryMetadata(BaseModel):
    geometry_type: str
    centroid_lat: float
    centroid_lon: float


class PanchayatResponse(BaseModel):
    panchayat_id: str
    panchayat_name: str
    block_id: str
    block_name: str
    district_id: str
    district_name: str
    district_lgd_code: Optional[str] = None
    block_lgd_code: Optional[str] = None
    gp_lgd_code: Optional[str] = None
    geometry: Dict[str, Any]
    geometry_metadata: GeometryMetadata
    support_status: Literal["SUPPORTED_VERIFIED_SAFE_LAYER"]


class GeoJSONFeature(BaseModel):
    type: Literal["Feature"]
    properties: Dict[str, Any]
    geometry: Optional[Dict[str, Any]]


class RiskMapResponse(BaseModel):
    type: Literal["FeatureCollection"]
    features: List[GeoJSONFeature]
    name: Optional[str] = None
    crs: Optional[Dict[str, Any]] = None


class PanchayatListItem(BaseModel):
    panchayat_id: str
    panchayat_name: str
    block_id: str
    block_name: str
    district_name: str
    gp_lgd_code: Optional[str] = None
    centroid_lat: float
    centroid_lon: float
    geometry: Dict[str, Any]

