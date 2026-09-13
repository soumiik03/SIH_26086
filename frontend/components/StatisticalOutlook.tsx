import type { HorizonForecast, Statistical730DayOutlook } from "@/types/api";
import ProbabilityCard from "./probability";

interface StatisticalOutlookPanelProps {
  outlook: Statistical730DayOutlook;
}

const horizons = [
  { key: "7_14d", label: "7–14 days" },
  { key: "15_21d", label: "15–21 days" },
  { key: "22_30d", label: "22–30 days" },
] as const;

const events: Array<{
  key: keyof HorizonForecast;
  label: string;
}> = [
  { key: "dry_spell_probability", label: "Dry spell" },
  { key: "severe_break_probability", label: "Severe break" },
  { key: "heavy_rain_probability", label: "Heavy rain" },
  { key: "revival_probability", label: "Revival" },
];

export default function StatisticalOutlookPanel({
  outlook,
}: StatisticalOutlookPanelProps) {
  return (
    <div className="border border-slate-200 bg-white p-5 sm:p-6">
      <div className="mb-5">
        <p className="text-xs font-bold uppercase tracking-[.16em] text-moss">
          Extended statistical outlook
        </p>

        <h3 className="mt-2 font-display text-xl font-semibold text-ink">
          7–30 day probabilistic outlook
        </h3>

        <p className="mt-1 text-sm text-slate-500">
          Statistical model probabilities by forecast window.
        </p>
      </div>

      <div className="space-y-6">
   {horizons.map(({ key, label }) => {
  const horizon = outlook[key];

  return (
            <div key={key}>
              <h4 className="mb-3 text-sm font-semibold text-ink">
                {label}
              </h4>

              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                {events.map(({ key: eventKey, label: eventLabel }) => (
                  <ProbabilityCard
                    key={eventKey}
                    label={eventLabel}
                    probability={horizon[eventKey] as number}
                  />
                ))}
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-6 border-t border-slate-200 pt-4">
        <p className="text-xs font-semibold uppercase tracking-[.14em] text-slate-500">
          {outlook.forecast_status}
        </p>

        <p className="mt-2 text-xs leading-5 text-slate-500">
          {outlook.disclaimer}
        </p>
      </div>
    </div>
  );
}