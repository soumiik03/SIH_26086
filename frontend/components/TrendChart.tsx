"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { Statistical730DayOutlook } from "@/types/api";

interface TrendChartProps {
  outlook: Statistical730DayOutlook;
}

export default function TrendChart({ outlook }: TrendChartProps) {
  const chartData = [
    {
      horizon: "7–14d",
      "Dry spell": Number(((outlook["7_14d"]?.dry_spell_probability ?? 0) * 100).toFixed(1)),
      "Severe break": Number(((outlook["7_14d"]?.severe_break_probability ?? 0) * 100).toFixed(1)),
      "Heavy rain": Number(((outlook["7_14d"]?.heavy_rain_probability ?? 0) * 100).toFixed(1)),
      "Revival": Number(((outlook["7_14d"]?.revival_probability ?? 0) * 100).toFixed(1)),
    },
    {
      horizon: "15–21d",
      "Dry spell": Number(((outlook["15_21d"]?.dry_spell_probability ?? 0) * 100).toFixed(1)),
      "Severe break": Number(((outlook["15_21d"]?.severe_break_probability ?? 0) * 100).toFixed(1)),
      "Heavy rain": Number(((outlook["15_21d"]?.heavy_rain_probability ?? 0) * 100).toFixed(1)),
      "Revival": Number(((outlook["15_21d"]?.revival_probability ?? 0) * 100).toFixed(1)),
    },
    {
      horizon: "22–30d",
      "Dry spell": Number(((outlook["22_30d"]?.dry_spell_probability ?? 0) * 100).toFixed(1)),
      "Severe break": Number(((outlook["22_30d"]?.severe_break_probability ?? 0) * 100).toFixed(1)),
      "Heavy rain": Number(((outlook["22_30d"]?.heavy_rain_probability ?? 0) * 100).toFixed(1)),
      "Revival": Number(((outlook["22_30d"]?.revival_probability ?? 0) * 100).toFixed(1)),
    },
  ];

  return (
    <div className="mt-5 border-t border-slate-100 pt-5">
      <div className="mb-3 flex items-center justify-between">
        <p className="text-xs font-bold uppercase tracking-[.14em] text-slate-600">
          30-Day Probability Trajectory
        </p>
        <span className="text-[11px] text-slate-500">Multi-horizon trend</span>
      </div>
      <div className="h-60 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={chartData}
            margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
          >
            <defs>
              <linearGradient id="colorDry" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#c56d3d" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#c56d3d" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorBreak" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#dc2626" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#dc2626" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorRain" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#2563eb" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#2563eb" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis
              dataKey="horizon"
              tick={{ fill: "#64748b", fontSize: 12 }}
              tickLine={false}
              axisLine={{ stroke: "#cbd5e1" }}
            />
            <YAxis
              unit="%"
              domain={[0, 100]}
              tick={{ fill: "#64748b", fontSize: 11 }}
              tickLine={false}
              axisLine={{ stroke: "#cbd5e1" }}
            />
            <Tooltip
              formatter={(value: number) => [`${value}%`]}
              contentStyle={{
                backgroundColor: "#ffffff",
                borderColor: "#e2e8f0",
                borderRadius: "8px",
                fontSize: "12px",
                boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
              }}
            />
            <Legend
              wrapperStyle={{ fontSize: "12px", paddingTop: "8px" }}
              iconType="circle"
            />
            <Area
              type="monotone"
              dataKey="Dry spell"
              stroke="#c56d3d"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorDry)"
            />
            <Area
              type="monotone"
              dataKey="Severe break"
              stroke="#dc2626"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorBreak)"
            />
            <Area
              type="monotone"
              dataKey="Heavy rain"
              stroke="#2563eb"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorRain)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
