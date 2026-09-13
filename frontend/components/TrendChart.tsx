"use client";

import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import type { Statistical730DayOutlook } from "@/types/api";

interface TrendChartProps { outlook: Statistical730DayOutlook; }

export default function TrendChart({ outlook }: TrendChartProps) {
  const percentage = (value: number | null | undefined) =>
    typeof value === "number" && Number.isFinite(value) ? value * 100 : null;
  const chartData = (["7_14d", "15_21d", "22_30d"] as const).map((key) => ({
    horizon: key === "7_14d" ? "7–14d" : key === "15_21d" ? "15–21d" : "22–30d",
    "Dry spell": percentage(outlook[key]?.dry_spell_probability),
    "Severe break": percentage(outlook[key]?.severe_break_probability),
    "Heavy rain": percentage(outlook[key]?.heavy_rain_probability),
    Revival: percentage(outlook[key]?.revival_probability),
  }));
  const numericValues = chartData.flatMap((row) =>
    [row["Dry spell"], row["Severe break"], row["Heavy rain"], row.Revival]
      .filter((value): value is number => typeof value === "number"),
  );
  const subtitle = numericValues.length === 0 ? "Data unavailable" : Math.max(...numericValues) < 1 ? "Low modeled probability" : "Multi-horizon trend";

  return (
    <div className="mt-5 border-t border-slate-100 pt-5">
      <div className="mb-3 flex items-center justify-between">
        <p className="text-xs font-bold uppercase tracking-[.14em] text-slate-600">30-Day Probability Trajectory</p>
        <span className="text-[11px] text-slate-500">{subtitle}</span>
      </div>
      <div className="h-60 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="colorDry" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#c56d3d" stopOpacity={0.25} /><stop offset="95%" stopColor="#c56d3d" stopOpacity={0} /></linearGradient>
              <linearGradient id="colorBreak" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#dc2626" stopOpacity={0.25} /><stop offset="95%" stopColor="#dc2626" stopOpacity={0} /></linearGradient>
              <linearGradient id="colorRain" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#2563eb" stopOpacity={0.25} /><stop offset="95%" stopColor="#2563eb" stopOpacity={0} /></linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="horizon" tick={{ fill: "#64748b", fontSize: 12 }} tickLine={false} axisLine={{ stroke: "#cbd5e1" }} />
            <YAxis unit="%" domain={[0, 100]} tick={{ fill: "#64748b", fontSize: 11 }} tickLine={false} axisLine={{ stroke: "#cbd5e1" }} />
            <Tooltip formatter={(value: number | string) => [typeof value === "number" ? `${value}%` : "Data unavailable"]} contentStyle={{ backgroundColor: "#ffffff", borderColor: "#e2e8f0", borderRadius: "8px", fontSize: "12px", boxShadow: "0 4px 12px rgba(0,0,0,0.08)" }} />
            <Legend wrapperStyle={{ fontSize: "12px", paddingTop: "8px" }} iconType="circle" />
            <Area type="monotone" dataKey="Dry spell" stroke="#c56d3d" strokeWidth={2} fillOpacity={1} fill="url(#colorDry)" />
            <Area type="monotone" dataKey="Severe break" stroke="#dc2626" strokeWidth={2} fillOpacity={1} fill="url(#colorBreak)" />
            <Area type="monotone" dataKey="Heavy rain" stroke="#2563eb" strokeWidth={2} fillOpacity={1} fill="url(#colorRain)" />
            <Area type="monotone" dataKey="Revival" stroke="#7c3aed" strokeWidth={2} fillOpacity={0} fill="none" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
