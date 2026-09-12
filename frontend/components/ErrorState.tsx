import { RefreshCw, TriangleAlert } from "lucide-react";

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return <div className="flex items-start gap-3 border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800"><TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" /><div className="flex-1"><p>{message}</p>{onRetry && <button onClick={onRetry} className="mt-2 inline-flex items-center gap-2 font-semibold underline underline-offset-4"><RefreshCw className="h-3.5 w-3.5" />Retry</button>}</div></div>;
}