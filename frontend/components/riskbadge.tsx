import type { RiskLevel } from "@/types/api";

interface RiskBadgeProps {
  level: RiskLevel;
}

export default function RiskBadge({
  level,
}: RiskBadgeProps) {
  const styles: Record<RiskLevel, string> = {
    LOW: "bg-green-100 text-green-700",
    MODERATE: "bg-yellow-100 text-yellow-700",
    HIGH: "bg-orange-100 text-orange-700",
    VERY_HIGH: "bg-red-100 text-red-700",
    UNAVAILABLE: "bg-slate-100 text-slate-600",
  };

  return (
    <span
      className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${styles[level]}`}
    >
      {level.replace("_", " ")}
    </span>
  );
}
