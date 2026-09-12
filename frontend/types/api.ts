export type RiskLevel = "LOW" | "MODERATE" | "HIGH" | "VERY_HIGH";
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
  risk_level: string;
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
}

export interface Forecast {
  panchayat_id: string;
  panchayat_name: string;
  block_id: string;
  block_name: string;
  district_id: string;
  district_name: string;
  onset_probability: number;
  false_onset_probability: number;
  dry_spell_5d_probability: number;
  severe_break_7d_probability: number;
  heavy_rain_probability: number;
  revival_probability: number;
  risk_levels: RiskLevels;
  advisory: AgronomicAdvisory;
  model_versions: Record<string, string>;
  forecast_status: ForecastStatus;
  timestamp: string;
  disclaimer: string;
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