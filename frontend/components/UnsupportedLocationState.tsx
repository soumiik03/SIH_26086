import { MapPinOff } from "lucide-react";

export function UnsupportedLocationState({ message }: { message: string }) {
  return (
    <div className="flex items-start gap-3 border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
      <MapPinOff className="mt-0.5 h-4 w-4 shrink-0" />
      <p>{message}</p>
    </div>
  );
}
