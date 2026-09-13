interface ProbabilityCardProps {
  label: string;
  probability: number;
}

export default function ProbabilityCard({
  label,
  probability,
}: ProbabilityCardProps) {
  const percentage = Math.round(probability * 100);

  return (
    <div className="rounded-xl border bg-white p-5 shadow-sm">
      <p className="text-sm text-gray-500">
        {label}
      </p>

      <p className="mt-2 text-3xl font-bold">
        {percentage}%
      </p>

      <div className="mt-3 h-2 overflow-hidden rounded-full bg-gray-100">
        <div
          className="h-full rounded-full bg-blue-600"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}