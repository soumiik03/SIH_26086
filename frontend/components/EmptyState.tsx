import { MapPinOff } from "lucide-react";

export function EmptyState({ message }: { message: string }) {
  return <div className="flex items-center gap-3 border border-dashed border-slate-300 px-4 py-5 text-sm text-slate-500"><MapPinOff className="h-4 w-4" />{message}</div>;
}