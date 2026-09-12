export function LoadingState({ label }: { label: string }) {
  return <div className="flex items-center gap-3 py-6 text-sm text-slate-500"><span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-200 border-t-moss" aria-hidden="true" />{label}</div>;
}