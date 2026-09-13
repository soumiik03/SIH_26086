export type RiskLevel =
  | "LOW"
  | "MODERATE"
  | "HIGH"
  | "VERY HIGH";

export interface District {
  id: string | number;
  name: string;
}

export interface Block {
  id: string | number;
  name: string;
  district_id?: string | number;
}

export interface Panchayat {
  id: string | number;
  name: string;
  block_id?: string | number;
  district_id?: string | number;
  risk_level?: RiskLevel;
}

export interface RiskMapProperties {
  panchayat_id: string | number;
  panchayat_name: string;
  risk_level: RiskLevel;
}

export interface RiskMapFeature {
  type: "Feature";
  id?: string | number;
  properties: RiskMapProperties;
  geometry: {
    type: string;
    coordinates: unknown;
  };
}

export interface RiskMapResponse {
  type: "FeatureCollection";
  features: RiskMapFeature[];
}

export interface Forecast {
  [key: string]: unknown;
}