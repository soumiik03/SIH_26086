const riskLevels = [
  { label: "Low", color: "#22c55e" },
  { label: "Moderate", color: "#facc15" },
  { label: "High", color: "#f97316" },
  { label: "Very high", color: "#dc2626" },
];

export default function RiskLegend() {
  return (
    <div className="absolute bottom-4 left-4 z-10 border border-slate-200 bg-white/95 p-3 shadow-lg backdrop-blur-sm">
      <p className="mb-2 text-xs font-semibold uppercase tracking-[.14em] text-slate-600">
        Risk level
      </p>
      <div className="grid gap-2">
        {riskLevels.map((level) => (
          <div key={level.label} className="flex items-center gap-2 text-xs font-medium text-slate-700">
            <span
              aria-hidden="true"
              className="h-3 w-3 rounded-sm"
              style={{ backgroundColor: level.color }}
            />
            <span>{level.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
