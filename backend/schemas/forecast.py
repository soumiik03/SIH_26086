from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field

RiskLevel = Literal["LOW", "MODERATE", "HIGH", "VERY_HIGH"]
ForecastStatus = Literal["EXPERIMENTAL_OBSERVATION_STATE"]
HorizonForecastStatus = Literal["STATISTICAL_7_30_DAY_OUTLOOK"]
HorizonApplicability = Literal["APPLICABLE", "OUT_OF_SEASON", "UNAVAILABLE"]
DataFreshnessStatus = Literal["CURRENT", "STALE", "UNAVAILABLE"]


class RiskLevels(BaseModel):
    overall: RiskLevel
    heavy_rain: RiskLevel
    severe_break: RiskLevel
    dry_spell: RiskLevel
    false_onset: RiskLevel


class AgronomicAdvisory(BaseModel):
    headline: str
    recommended_action: str
    action: Literal["SOW", "WAIT", "PREPARE_IRRIGATION"] = "WAIT"
    rule_id: str = "AGRI-WAIT-CONTEXT-001"
    crop: Optional[str] = None
    crop_name: Optional[str] = None
    headline_key: str = "advisory.wait"
    reason_keys: List[str] = Field(default_factory=list)
    reasons: List[str] = Field(default_factory=list)
    risk_factors: Dict[str, Optional[float]] = Field(default_factory=dict)
    validity: str = "UNKNOWN"
    thresholds: Dict[str, float] = Field(default_factory=dict)


class AgronomicAdvisoryLocation(BaseModel):
    panchayat_id: str
    panchayat_name: str
    block_id: str
    block_name: str
    district_id: str
    district_name: str


class HorizonModelVersion(BaseModel):
    target_col: str
    model_version: str
    artifact_path: str
    calibration_method: str
    features_evaluated: int


class HorizonForecast(BaseModel):
    dry_spell_probability: Optional[float] = Field(default=None, ge=0, le=1)
    severe_break_probability: Optional[float] = Field(default=None, ge=0, le=1)
    heavy_rain_probability: Optional[float] = Field(default=None, ge=0, le=1)
    revival_probability: Optional[float] = Field(default=None, ge=0, le=1)
    dry_spell_applicability: HorizonApplicability
    severe_break_applicability: HorizonApplicability
    heavy_rain_applicability: HorizonApplicability
    revival_applicability: HorizonApplicability
    model_versions: Dict[str, HorizonModelVersion]


class Statistical730DayOutlook(BaseModel):
    forecast_status: HorizonForecastStatus
    disclaimer: str

    horizon_7_14d: HorizonForecast = Field(alias="7_14d")
    horizon_15_21d: HorizonForecast = Field(alias="15_21d")
    horizon_22_30d: HorizonForecast = Field(alias="22_30d")


class AgronomicAdvisoryResponse(BaseModel):
    location: AgronomicAdvisoryLocation
    advisory: AgronomicAdvisory
    supporting_outlook: Statistical730DayOutlook
    crop_stage: Optional[str] = None
    planned_sowing_date: Optional[str] = None


class ForecastResponse(BaseModel):
    panchayat_id: str
    panchayat_name: str
    block_id: str
    block_name: str
    district_id: str
    district_name: str
    current_system_date: str = "2026-09-13"
    data_as_of: str = "2026-09-08"
    forecast_reference_date: str = "2026-09-08"
    data_freshness_status: DataFreshnessStatus = "CURRENT"
    event_applicability: Dict[str, str] = Field(default_factory=dict)
    onset_probability: Optional[float] = Field(default=None, ge=0, le=1)
    false_onset_probability: Optional[float] = Field(default=None, ge=0, le=1)
    dry_spell_5d_probability: Optional[float] = Field(default=None, ge=0, le=1)
    severe_break_7d_probability: Optional[float] = Field(default=None, ge=0, le=1)
    heavy_rain_probability: Optional[float] = Field(default=None, ge=0, le=1)
    revival_probability: Optional[float] = Field(default=None, ge=0, le=1)
    risk_levels: RiskLevels
    advisory: AgronomicAdvisory
    model_versions: Dict[str, str]
    forecast_status: ForecastStatus
    timestamp: str
    disclaimer: str
    statistical_7_30_day_outlook: Statistical730DayOutlook


class HealthResponse(BaseModel):
    service_status: Literal["ok"]
    engine_version: str
    forecast_status: ForecastStatus
    model_availability: Dict[str, bool]
