export type RiskLevel = "LOW" | "MODERATE" | "HIGH" | "VERY_HIGH" | "UNAVAILABLE";
export type ForecastStatus = "EXPERIMENTAL_OBSERVATION_STATE";

export interface HealthResponse {
  service_status: "ok";
  engine_version: string;
  forecast_status: ForecastStatus;
  model_availability: Record<string, boolean>;
}

export interface District {
  district_id: string;
  district_name: string;
  meteorological_key: string;
}

export interface Block {
  block_id: string;
  block_name: string;
  district_id: string;
  district_name: string;
  block_lgd_code: string | null;
  centroid_lat: number;
  centroid_lon: number;
  risk_level: RiskLevel;
}

export interface PanchayatListItem {
  panchayat_id: string;
  panchayat_name: string;
  block_id: string;
  block_name: string;
  district_name: string;
  gp_lgd_code: string | null;
  centroid_lat: number;
  centroid_lon: number;
  geometry: Record<string, unknown>;
}

export interface GeometryMetadata {
  geometry_type: string;
  centroid_lat: number;
  centroid_lon: number;
}

export interface Panchayat {
  panchayat_id: string;
  panchayat_name: string;
  block_id: string;
  block_name: string;
  district_id: string;
  district_name: string;
  district_lgd_code: string | null;
  block_lgd_code: string | null;
  gp_lgd_code: string | null;
  geometry: Record<string, unknown>;
  geometry_metadata: GeometryMetadata;
  support_status: "SUPPORTED_VERIFIED_SAFE_LAYER";
}

export interface RiskLevels {
  overall: RiskLevel;
  heavy_rain: RiskLevel;
  severe_break: RiskLevel;
  dry_spell: RiskLevel;
  false_onset: RiskLevel;
}

export interface AgronomicAdvisory {
  headline: string;
  recommended_action: string;
  action?: "SOW" | "WAIT" | "PREPARE_IRRIGATION";
  rule_id?: string;
  validity?: string;
}
export interface HorizonModelVersion {
  target_col: string;
  model_version: string;
  artifact_path: string;
  calibration_method: string;
  features_evaluated: number;
}

export interface HorizonForecast {
  dry_spell_probability: number | null;
  dry_spell_applicability?: "APPLICABLE" | "OUT_OF_SEASON" | "UNAVAILABLE";
  severe_break_probability: number | null;
  severe_break_applicability?: "APPLICABLE" | "OUT_OF_SEASON" | "UNAVAILABLE";
  heavy_rain_probability: number | null;
  heavy_rain_applicability?: "APPLICABLE" | "OUT_OF_SEASON" | "UNAVAILABLE";
  revival_probability: number | null;
  revival_applicability?: "APPLICABLE" | "OUT_OF_SEASON" | "UNAVAILABLE";
  forecast_status?: string;
  model_versions: Record<string, HorizonModelVersion>;
}

export interface Statistical730DayOutlook {
  forecast_status: "STATISTICAL_7_30_DAY_OUTLOOK";
  disclaimer: string;
  "7_14d": HorizonForecast;
  "15_21d": HorizonForecast;
  "22_30d": HorizonForecast;
}
export interface Forecast {
  panchayat_id: string;
  panchayat_name: string;
  block_id: string;
  block_name: string;
  district_id: string;
  district_name: string;
  current_system_date?: string;
  data_as_of?: string;
  forecast_reference_date?: string;
  data_freshness_status?: "CURRENT" | "STALE" | "UNAVAILABLE";
  event_applicability?: Record<string, "APPLICABLE" | "OUT_OF_SEASON" | "UNAVAILABLE">;
  onset_probability: number | null;
  false_onset_probability: number | null;
  dry_spell_5d_probability: number | null;
  severe_break_7d_probability: number | null;
  heavy_rain_probability: number | null;
  revival_probability: number | null;
  risk_levels: RiskLevels;
  advisory: AgronomicAdvisory;
  model_versions: Record<string, string>;
  forecast_status: ForecastStatus;
  timestamp: string;
  disclaimer: string;
  statistical_7_30_day_outlook: Statistical730DayOutlook;
}

export interface RiskMapFeature {
  type: "Feature";
  properties: Record<string, unknown>;
  geometry: Record<string, unknown> | null;
}

export interface RiskMap {
  type: "FeatureCollection";
  features: RiskMapFeature[];
  name: string | null;
  crs: Record<string, unknown> | null;
}
