"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, MapPin } from "lucide-react";

import { api } from "@/lib/api";

interface ForecastPanelProps {
  panchayatId: string;
}

export default function ForecastPanel({
  panchayatId,
}: ForecastPanelProps) {

  const [panchayat, setPanchayat] = useState<any>(null);
  const [forecast, setForecast] = useState<any>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {

    if (!panchayatId) {
      setPanchayat(null);
      setForecast(null);
      return;
    }

    async function loadData() {

      try {

        setLoading(true);
        setError("");

        const [panchayatData, forecastData] =
          await Promise.all([
            api.getPanchayat(panchayatId),
            api.getForecast(panchayatId),
          ]);

        setPanchayat(panchayatData);
        setForecast(forecastData);

      } catch (err) {

        console.error(err);

        setError(
          "Unable to load Panchayat forecast."
        );

      } finally {
        setLoading(false);
      }
    }

    loadData();

  }, [panchayatId]);

  if (!panchayatId) {
    return (
      <aside className="flex h-full min-h-[300px] items-center justify-center rounded-xl border border-slate-200 bg-white p-6">

        <div className="text-center">

          <MapPin className="mx-auto mb-3 h-8 w-8 text-slate-400" />

          <h2 className="font-semibold text-slate-800">
            Select a Panchayat
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            Select an area from the map or location controls
            to view forecast information.
          </p>

        </div>

      </aside>
    );
  }

  if (loading) {
    return (
      <aside className="rounded-xl border border-slate-200 bg-white p-6">
        <p className="text-sm text-slate-500">
          Loading Panchayat forecast...
        </p>
      </aside>
    );
  }

  if (error) {
    return (
      <aside className="rounded-xl border border-red-200 bg-white p-6">

        <AlertTriangle className="mb-2 h-6 w-6 text-red-500" />

        <p className="text-sm text-red-600">
          {error}
        </p>

      </aside>
    );
  }

  return (
    <aside className="rounded-xl border border-slate-200 bg-white">

      <div className="border-b border-slate-200 p-5">

        <p className="text-xs font-bold tracking-wider text-slate-500">
          SELECTED PANCHAYAT
        </p>

        <h2 className="mt-1 text-xl font-bold text-slate-900">
          {panchayat?.name ?? "Unknown Panchayat"}
        </h2>

      </div>

      <div className="space-y-5 p-5">

        <div>
          <p className="text-xs font-medium text-slate-500">
            RISK LEVEL
          </p>

          <p className="mt-1 text-lg font-bold text-slate-900">
            {panchayat?.risk_level ?? "Unavailable"}
          </p>
        </div>

        <div>
          <p className="mb-2 text-xs font-bold tracking-wider text-slate-500">
            FORECAST
          </p>

          <div className="rounded-lg bg-slate-50 p-4">

            <pre className="overflow-auto text-xs text-slate-700">
              {JSON.stringify(forecast, null, 2)}
            </pre>

          </div>
        </div>

      </div>

    </aside>
  );
}