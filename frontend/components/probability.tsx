interface ProbabilityCardProps {
  label: string;
  probability: number | null | undefined;
  status?: "APPLICABLE" | "OUT_OF_SEASON" | "UNAVAILABLE";
}

export default function ProbabilityCard({
  label,
  probability,
  status,
}: ProbabilityCardProps) {
  const hasValue = typeof probability === "number" && Number.isFinite(probability);
  const percentage = hasValue ? probability * 100 : null;
  const formattedPercentage = percentage === null
    ? status === "OUT_OF_SEASON" ? "Out of season" : "Data unavailable"
    : `${percentage < 0.1 ? percentage.toFixed(2) : percentage.toFixed(1)}%`;
  return (
    <div className="rounded-xl border bg-white p-5 shadow-sm">
      <p className="text-sm text-gray-500">
        {label}
      </p>

      <p className="mt-2 text-3xl font-bold">
        {formattedPercentage}
      </p>

      <div className="mt-3 h-2 overflow-hidden rounded-full bg-gray-100">
        <div
          className="h-full rounded-full bg-blue-600"
          style={{ width: `${Math.min(100, Math.max(0, percentage === null ? 0 : percentage))}%` }}
        />
      </div>
    </div>
  );
}
