import { Cloud, CloudOff } from "lucide-react";

export function ApiStatus({ connected, loading }: { connected: boolean; loading: boolean }) {
  const label = loading ? "Checking service" : connected ? "API connected" : "API unavailable";
  return <div className="inline-flex items-center gap-2 border border-white/15 bg-white/10 px-3 py-1.5 text-xs font-semibold tracking-wide text-white"><span className={`h-2 w-2 rounded-full ${loading ? "bg-amber-300" : connected ? "bg-lime-300" : "bg-red-300"}`} />{connected ? <Cloud className="h-3.5 w-3.5" /> : <CloudOff className="h-3.5 w-3.5" />}{label}</div>;
}