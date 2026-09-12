from typing import Dict, Literal

from pydantic import BaseModel, Field


RiskLevel = Literal["LOW", "MODERATE", "HIGH", "VERY_HIGH"]
ForecastStatus = Literal["EXPERIMENTAL_OBSERVATION_STATE"]


class RiskLevels(BaseModel):
    overall: RiskLevel
    heavy_rain: RiskLevel
    severe_break: RiskLevel
    dry_spell: RiskLevel
    false_onset: RiskLevel


class AgronomicAdvisory(BaseModel):
    headline: str
    recommended_action: str


class ForecastResponse(BaseModel):
    panchayat_id: str
    panchayat_name: str
    block_id: str
    block_name: str
    district_id: str
    district_name: str
    onset_probability: float = Field(ge=0, le=1)
    false_onset_probability: float = Field(ge=0, le=1)
    dry_spell_5d_probability: float = Field(ge=0, le=1)
    severe_break_7d_probability: float = Field(ge=0, le=1)
    heavy_rain_probability: float = Field(ge=0, le=1)
    revival_probability: float = Field(ge=0, le=1)
    risk_levels: RiskLevels
    advisory: AgronomicAdvisory
    model_versions: Dict[str, str]
    forecast_status: ForecastStatus
    timestamp: str
    disclaimer: str


class HealthResponse(BaseModel):
    service_status: Literal["ok"]
    engine_version: str
    forecast_status: ForecastStatus
    model_availability: Dict[str, bool]

