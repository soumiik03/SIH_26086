export type RiskLevel =
  | "LOW"
  | "MODERATE"
  | "HIGH"
  | "VERY_HIGH";

export interface ForecastResponse {
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

  risk_levels: {
    overall: RiskLevel;
    heavy_rain: RiskLevel;
    severe_break: RiskLevel;
    dry_spell: RiskLevel;
    false_onset: RiskLevel;
  };

  advisory: {
    headline: string;
    recommended_action: string;
  };

  model_versions: Record<string, string>;

  forecast_status:
    | "EXPERIMENTAL_OBSERVATION_STATE";

  timestamp: string;

  disclaimer: string;
}