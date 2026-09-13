import { CloudRain } from "lucide-react";

export default function Header() {
  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="flex items-center justify-between px-6 py-4">

        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-900">
            <CloudRain className="h-5 w-5 text-white" />
          </div>

          <div>
            <h1 className="text-xl font-bold tracking-tight text-slate-900">
              VARSHASENTINEL
            </h1>

            <p className="text-xs text-slate-500">
              Hyperlocal Monsoon Intelligence
            </p>
          </div>
        </div>

        <div className="hidden text-sm font-medium text-slate-500 sm:block">
          OFFICER DASHBOARD
        </div>

      </div>
    </header>
  );
}