import type { Forecast } from "@/types/api";
import { CalendarDays, CheckCircle2 } from "lucide-react";
import ProbabilityCard from "./probability";
import ForecastPanel from "./forecastpanel";
import AdvisoryCard from "./advisory";
import StatisticalOutlookPanel from "./StatisticalOutlook";
const probabilityFields: Array<{
  key: keyof Pick<
    Forecast,
    | "onset_probability"
    | "false_onset_probability"
    | "dry_spell_5d_probability"
    | "severe_break_7d_probability"
    | "heavy_rain_probability"
    | "revival_probability"
  >;
  label: string;
}> = [
  { key: "onset_probability", label: "Onset" },
  { key: "false_onset_probability", label: "False onset" },
  { key: "dry_spell_5d_probability", label: "Dry spell · 5d" },
  { key: "severe_break_7d_probability", label: "Severe break · 7d" },
  { key: "heavy_rain_probability", label: "Heavy rain" },
  { key: "revival_probability", label: "Revival" },
];

export function ForecastSection({
  forecast,
}: {
  forecast: Forecast;
}) {
  return (
    <section className="animate-rise space-y-5">
      {/* Location + timestamp */}
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="mb-1 text-xs font-bold uppercase tracking-[.18em] text-moss">
            Verified forecast layer
          </p>

          <h2 className="font-display text-2xl font-semibold text-ink">
            {forecast.panchayat_name}
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            {forecast.block_name} · {forecast.district_name}
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs text-slate-500">
          <CalendarDays className="h-4 w-4" />
          Updated {new Date(forecast.timestamp).toLocaleString()}
        </div>
      </div>

      {/* Current forecast probabilities */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {probabilityFields.map(({ key, label }) => (
          <ProbabilityCard
            key={key}
            label={label}
            probability={forecast[key]}
          />
        ))}
      </div>

      {/* Risk + advisory */}
      <div className="grid gap-5 lg:grid-cols-[1.15fr_.85fr]">
        <ForecastPanel riskLevels={forecast.risk_levels} />

        <AdvisoryCard advisory={forecast.advisory} />
      </div>

      {/* Backend disclaimer */}
      <div className="flex items-start gap-2 border-t border-slate-200 pt-4 text-xs leading-5 text-slate-500">
        <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-moss" />
        {forecast.disclaimer}
      </div>
      <StatisticalOutlookPanel
  outlook={forecast.statistical_7_30_day_outlook}
/>
    </section>
  );
}