import type { RiskLevels } from "@/types/api";
import RiskBadge from "./riskbadge";

interface ForecastPanelProps {
  riskLevels: RiskLevels;
}

export default function ForecastPanel({
  riskLevels,
}: ForecastPanelProps) {
  return (
    <div className="border border-slate-200 bg-white p-5 sm:p-6">
      <div className="mb-5 flex items-center gap-2">
        <div className="h-4 w-4 rounded-full bg-moss" />
        <h3 className="font-display text-lg font-semibold">
          Risk profile
        </h3>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        {Object.entries(riskLevels).map(([name, level]) => (
          <div
            key={name}
            className="border border-slate-100 p-3"
          >
            <p className="mb-2 text-xs capitalize text-slate-500">
              {name.replaceAll("_", " ")}
            </p>

            <RiskBadge level={level} />
          </div>
        ))}
      </div>
    </div>
  );
}