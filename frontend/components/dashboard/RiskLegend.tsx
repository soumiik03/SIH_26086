const risks = [
  {
    label: "LOW",
    className: "bg-green-500",
  },
  {
    label: "MODERATE",
    className: "bg-yellow-400",
  },
  {
    label: "HIGH",
    className: "bg-orange-500",
  },
  {
    label: "VERY HIGH",
    className: "bg-red-600",
  },
];

export default function RiskLegend() {
  return (
    <div className="absolute bottom-4 left-4 z-10 rounded-lg border border-slate-200 bg-white p-3 shadow-md">

      <p className="mb-2 text-xs font-bold tracking-wide text-slate-700">
        RISK LEVEL
      </p>

      <div className="space-y-1.5">
        {risks.map((risk) => (
          <div
            key={risk.label}
            className="flex items-center gap-2 text-xs text-slate-600"
          >
            <span
              className={`h-3 w-3 rounded-full ${risk.className}`}
            />

            {risk.label}
          </div>
        ))}
      </div>

    </div>
  );
}