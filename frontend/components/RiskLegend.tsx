const riskLevels = [
  { label: "Low", color: "#22c55e" },
  { label: "Moderate", color: "#facc15" },
  { label: "High", color: "#f97316" },
  { label: "Very high", color: "#dc2626" },
];

export default function RiskLegend() {
  return (
    <div className="absolute bottom-3 left-3 z-10 rounded-lg border border-slate-200/90 bg-white/95 p-2.5 shadow-md backdrop-blur-sm sm:bottom-4 sm:left-4 sm:p-3">
      <p className="mb-1.5 text-[11px] font-bold uppercase tracking-[.14em] text-slate-700 sm:mb-2 sm:text-xs">
        Block-level risk
      </p>
      <div className="grid grid-cols-2 gap-x-3 gap-y-1.5 sm:grid-cols-1 sm:gap-2">
        {riskLevels.map((level) => (
          <div key={level.label} className="flex items-center gap-1.5 text-[11px] font-medium text-slate-700 sm:text-xs">
            <span
              aria-hidden="true"
              className="h-2.5 w-2.5 rounded-sm sm:h-3 sm:w-3"
              style={{ backgroundColor: level.color }}
            />
            <span>{level.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
