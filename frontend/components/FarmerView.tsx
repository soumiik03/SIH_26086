"use client";

import type { Forecast, Panchayat } from "@/types/api";
import {
  CalendarDays,
  CheckCircle2,
  Clock,
  Droplets,
  HelpCircle,
  Info,
  ShieldAlert,
  Sprout,
} from "lucide-react";

interface FarmerViewProps {
  forecast: Forecast;
  panchayat: Panchayat;
}

type FarmerAction = "SOW" | "WAIT" | "PREPARE IRRIGATION";

/**
 * Derives the primary agricultural decision directly from the backend advisory.
 * NOTE: Per product specification, this does NOT use frontend probability thresholds
 * or heuristic rules. The decision reflects the action communicated by the backend advisory.
 */
function getFarmerAction(forecast: Forecast): FarmerAction | null {
  if (forecast.advisory?.action) {
    return forecast.advisory.action === "PREPARE_IRRIGATION"
      ? "PREPARE IRRIGATION"
      : forecast.advisory.action;
  }

  const headline = forecast.advisory?.headline?.toLowerCase() || "";
  const action = forecast.advisory?.recommended_action?.toLowerCase() || "";
  const combined = `${headline} ${action}`;
  if (!combined.trim() || combined.includes("unavailable")) return null;

  if (
    combined.includes("supplementary irrigation") ||
    combined.includes("prepare irrigation") ||
    (combined.includes("irrigation") && combined.includes("dry"))
  ) {
    return "PREPARE IRRIGATION";
  }

  if (
    combined.includes("avoid") ||
    combined.includes("defer") ||
    combined.includes("postpone") ||
    combined.includes("false onset") ||
    combined.includes("wait") ||
    combined.includes("precaution") ||
    combined.includes("warning") ||
    combined.includes("alert")
  ) {
    return "WAIT";
  }

  return null;
}

function formatPercent(probability: number | null | undefined): string {
  if (probability === null || probability === undefined || !Number.isFinite(probability)) return "Data unavailable";
  const percentage = probability * 100;
  if (percentage === 0) return "0%";
  if (percentage < 0.1) return `${percentage.toFixed(2)}%`;
  return `${percentage.toFixed(1)}%`;
}

export function FarmerView({ forecast, panchayat }: FarmerViewProps) {
  const primaryAction = getFarmerAction(forecast);
  const outlook = forecast.statistical_7_30_day_outlook;

  const actionTheme = {
    SOW: {
      border: "border-emerald-500",
      bg: "bg-emerald-50/90",
      textColor: "text-emerald-950",
      badgeBg: "bg-emerald-600 text-white",
      icon: <Sprout className="h-8 w-8 text-emerald-600 sm:h-10 sm:w-10" />,
      subtext: "Monsoon conditions favorable for field preparation & sowing",
    },
    WAIT: {
      border: "border-amber-500",
      bg: "bg-amber-50/90",
      textColor: "text-amber-950",
      badgeBg: "bg-amber-600 text-white",
      icon: <Clock className="h-8 w-8 text-amber-600 sm:h-10 sm:w-10" />,
      subtext: "Elevated risk detected. Hold off direct dry seeding",
    },
    "PREPARE IRRIGATION": {
      border: "border-sky-500",
      bg: "bg-sky-50/90",
      textColor: "text-sky-950",
      badgeBg: "bg-sky-600 text-white",
      icon: <Droplets className="h-8 w-8 text-sky-600 sm:h-10 sm:w-10" />,
      subtext: "Dry hiatus expected. Arrange supplementary water & conserve soil moisture",
    },
    UNAVAILABLE: {
      border: "border-slate-400",
      bg: "bg-slate-50",
      textColor: "text-slate-900",
      badgeBg: "bg-slate-600 text-white",
      icon: <HelpCircle className="h-8 w-8 text-slate-500 sm:h-10 sm:w-10" />,
      subtext: "No agronomic action is inferred while required forecast data are unavailable",
    },
  }[primaryAction ?? "UNAVAILABLE"];

  return (
    <div className="animate-rise space-y-6">
      {/* 1. Location Bar */}
      <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <span className="inline-block rounded bg-[#e8f2eb] px-2.5 py-1 text-xs font-bold uppercase tracking-[.16em] text-moss">
              Farmer Advisory View
            </span>
            <h2 className="mt-2 font-display text-2xl font-bold text-ink sm:text-3xl">
              {forecast.panchayat_name}
            </h2>
            <p className="mt-1 text-sm font-medium text-slate-600">
              {forecast.block_name} Block · {forecast.district_name} District
            </p>
          </div>

          <div className="flex flex-col items-start gap-1.5 text-xs text-slate-500 sm:items-end">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-3 py-1 font-medium text-slate-700">
              GP LGD: {panchayat.gp_lgd_code || "Standard"}
            </span>
            <span className="flex items-center gap-1 text-[11px]">
              <CalendarDays className="h-3.5 w-3.5" />
              Updated {new Date(forecast.timestamp).toLocaleDateString()}
            </span>
          </div>
        </div>
      </section>

      {/* 2. Dominant Primary Decision Card */}
      <section
        className={`relative overflow-hidden rounded-2xl border-2 ${actionTheme.border} ${actionTheme.bg} p-6 shadow-md sm:p-8`}
      >
        <div className="mb-2 flex items-center justify-between">
          <p className="text-xs font-bold uppercase tracking-[.2em] text-slate-600 sm:text-sm">
            Primary Decision
          </p>
          <span className="text-xs text-slate-500">Agrometeorological recommendation</span>
        </div>

        <h3 className="font-display text-xl font-extrabold text-slate-900 sm:text-2xl">
          Should I sow now?
        </h3>

        {/* Large Prominent Action Badge */}
        <div className="my-6 flex flex-col items-center justify-center gap-3 rounded-xl border border-white/60 bg-white/80 px-6 py-6 text-center shadow-inner sm:flex-row sm:justify-start sm:text-left">
          <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl bg-white shadow-sm ring-1 ring-slate-100 sm:h-20 sm:w-20">
            {actionTheme.icon}
          </div>
          <div>
            <div
              className={`inline-block rounded-lg px-4 py-1.5 font-display text-3xl font-black tracking-wider sm:text-4xl ${actionTheme.badgeBg}`}
            >
              {primaryAction ?? "ADVISORY UNAVAILABLE"}
            </div>
            <p className="mt-2 text-sm font-semibold text-slate-800">
              {forecast.advisory?.headline}
            </p>
            <p className="mt-0.5 text-xs text-slate-600">{actionTheme.subtext}</p>
          </div>
        </div>

        {/* Key Agricultural Risk Indicators (Farmer-Focused) */}
        <div className="border-t border-slate-200/80 pt-5">
          <p className="mb-3 text-xs font-bold uppercase tracking-[.14em] text-slate-700">
            Current Risk Signals for this Panchayat
          </p>
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-xl border border-slate-200/80 bg-white/95 p-4 shadow-sm">
              <span className="text-xs font-medium text-slate-500">
                Onset likelihood
              </span>
              <p className="mt-1 text-2xl font-bold text-ink">
                {formatPercent(forecast.onset_probability)}
              </p>
              <p className="mt-1 text-[11px] text-slate-500">
                Chance of active monsoon rains
              </p>
            </div>

            <div className="rounded-xl border border-slate-200/80 bg-white/95 p-4 shadow-sm">
              <span className="text-xs font-medium text-slate-500">
                Dry-spell risk (5-day)
              </span>
              <p className="mt-1 text-2xl font-bold text-ink">
                {formatPercent(forecast.dry_spell_5d_probability)}
              </p>
              <p className="mt-1 text-[11px] text-slate-500">
                Chance of rain pausing for 5+ days
              </p>
            </div>

            <div className="rounded-xl border border-slate-200/80 bg-white/95 p-4 shadow-sm">
              <span className="text-xs font-medium text-slate-500">
                False-onset risk
              </span>
              <p className="mt-1 text-2xl font-bold text-ink">
                {formatPercent(forecast.false_onset_probability)}
              </p>
              <p className="mt-1 text-[11px] text-slate-500">
                Risk of early rain followed by dry hiatus
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 3. Recommended Action (Backend Advisory) */}
      <section className="rounded-xl border border-[#cde3d4] bg-[#edf7ef] p-5 shadow-sm sm:p-6">
        <div className="flex items-start gap-3">
          <CheckCircle2 className="mt-0.5 h-6 w-6 shrink-0 text-moss" />
          <div className="space-y-2">
            <p className="text-xs font-bold uppercase tracking-[.16em] text-moss">
              Recommended Agronomic Action
            </p>
            <h4 className="font-display text-lg font-bold text-ink">
              {forecast.advisory?.headline}
            </h4>
            <p className="text-sm leading-relaxed text-slate-700">
              {forecast.advisory?.recommended_action}
            </p>
            <div className="flex items-center gap-1.5 pt-2 text-xs text-slate-500">
              <Info className="h-3.5 w-3.5 text-moss" />
              <span>
                Formulated following ICAR / IMD Agrometeorological Advisory Services (AAS) guidelines.
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* 4. Simplified 7–30 Day Outlook */}
      {outlook && (
        <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
          <div className="mb-4">
            <p className="text-xs font-bold uppercase tracking-[.16em] text-moss">
              Extended Horizon
            </p>
            <h4 className="mt-1 font-display text-xl font-bold text-ink">
              7–30 Day Outlook for Farm Planning
            </h4>
            <p className="mt-1 text-xs text-slate-500">
              Statistical model probabilities across the coming month. Use to plan seedbed and irrigation needs.
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            {/* Horizon 1: 7–14 days */}
            <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-4">
              <div className="mb-2.5 flex items-center justify-between border-b border-slate-200 pb-2">
                <span className="font-display text-sm font-bold text-ink">
                  7–14 Days
                </span>
                <span className="rounded bg-slate-200 px-2 py-0.5 text-[10px] font-semibold text-slate-700">
                  Week 2
                </span>
              </div>
              <ul className="space-y-2 text-xs">
                <li className="flex items-center justify-between">
                  <span className="text-slate-600">Chance of dry spell:</span>
                  <span className="font-bold text-ink">
                    {formatPercent(outlook["7_14d"]?.dry_spell_probability)}
                  </span>
                </li>
                <li className="flex items-center justify-between">
                  <span className="text-slate-600">Chance of heavy rain:</span>
                  <span className="font-bold text-ink">
                    {formatPercent(outlook["7_14d"]?.heavy_rain_probability)}
                  </span>
                </li>
                <li className="flex items-center justify-between">
                  <span className="text-slate-600">Severe break risk:</span>
                  <span className="font-bold text-ink">
                    {formatPercent(outlook["7_14d"]?.severe_break_probability)}
                  </span>
                </li>
              </ul>
            </div>

            {/* Horizon 2: 15–21 days */}
            <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-4">
              <div className="mb-2.5 flex items-center justify-between border-b border-slate-200 pb-2">
                <span className="font-display text-sm font-bold text-ink">
                  15–21 Days
                </span>
                <span className="rounded bg-slate-200 px-2 py-0.5 text-[10px] font-semibold text-slate-700">
                  Week 3
                </span>
              </div>
              <ul className="space-y-2 text-xs">
                <li className="flex items-center justify-between">
                  <span className="text-slate-600">Chance of dry spell:</span>
                  <span className="font-bold text-ink">
                    {formatPercent(outlook["15_21d"]?.dry_spell_probability)}
                  </span>
                </li>
                <li className="flex items-center justify-between">
                  <span className="text-slate-600">Chance of heavy rain:</span>
                  <span className="font-bold text-ink">
                    {formatPercent(outlook["15_21d"]?.heavy_rain_probability)}
                  </span>
                </li>
                <li className="flex items-center justify-between">
                  <span className="text-slate-600">Severe break risk:</span>
                  <span className="font-bold text-ink">
                    {formatPercent(outlook["15_21d"]?.severe_break_probability)}
                  </span>
                </li>
              </ul>
            </div>

            {/* Horizon 3: 22–30 days */}
            <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-4">
              <div className="mb-2.5 flex items-center justify-between border-b border-slate-200 pb-2">
                <span className="font-display text-sm font-bold text-ink">
                  22–30 Days
                </span>
                <span className="rounded bg-slate-200 px-2 py-0.5 text-[10px] font-semibold text-slate-700">
                  Week 4
                </span>
              </div>
              <ul className="space-y-2 text-xs">
                <li className="flex items-center justify-between">
                  <span className="text-slate-600">Chance of dry spell:</span>
                  <span className="font-bold text-ink">
                    {formatPercent(outlook["22_30d"]?.dry_spell_probability)}
                  </span>
                </li>
                <li className="flex items-center justify-between">
                  <span className="text-slate-600">Chance of heavy rain:</span>
                  <span className="font-bold text-ink">
                    {formatPercent(outlook["22_30d"]?.heavy_rain_probability)}
                  </span>
                </li>
                <li className="flex items-center justify-between">
                  <span className="text-slate-600">Severe break risk:</span>
                  <span className="font-bold text-ink">
                    {formatPercent(outlook["22_30d"]?.severe_break_probability)}
                  </span>
                </li>
              </ul>
            </div>
          </div>
        </section>
      )}

      {/* 5. Scientific Transparency & Disclaimer */}
      <section className="rounded-xl border border-slate-200 bg-white p-4 text-xs leading-relaxed text-slate-500">
        <div className="flex items-start gap-2.5">
          <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-slate-400" />
          <div className="space-y-1">
            <p className="font-semibold text-slate-700">
              Scientific Transparency Note
            </p>
            <p>
              {forecast.disclaimer} {outlook?.disclaimer}
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}

export default FarmerView;
