import type { AgronomicAdvisory } from "@/types/api";
import { Sprout } from "lucide-react";

interface AdvisoryCardProps {
  advisory: AgronomicAdvisory;
}

export default function AdvisoryCard({
  advisory,
}: AdvisoryCardProps) {
  return (
    <div className="border border-[#cde3d4] bg-[#edf7ef] p-5 sm:p-6">
      <div className="flex items-start gap-3">
        <Sprout className="mt-1 h-5 w-5 shrink-0 text-moss" />

        <div>
          <p className="text-xs font-bold uppercase tracking-[.16em] text-moss">
            Agronomic advisory
          </p>

          <h3 className="mt-2 font-display text-lg font-semibold text-ink">
            {advisory.headline}
          </h3>

          <p className="mt-2 text-sm leading-6 text-slate-600">
            {advisory.recommended_action}
          </p>
        </div>
      </div>
    </div>
  );
}