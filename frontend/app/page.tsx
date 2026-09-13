"use client";

import { useEffect, useState } from "react";
import {
  Activity,
  ArrowDown,
  Database,
  Droplets,
  ShieldCheck,
  Sprout,
} from "lucide-react";
import { api, ApiError } from "@/lib/api";
import type {
  Block,
  District,
  Forecast,
  Panchayat,
  PanchayatListItem,
} from "@/types/api";
import { ApiStatus } from "@/components/ApiStatus";
import { ErrorState } from "@/components/ErrorState";
import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { LocationSelector } from "@/components/LocationSelector";
import { ForecastSection } from "@/components/ForecastSection";
import { FarmerView } from "@/components/FarmerView";
import { RiskMap as RiskMapView } from "@/components/RiskMap";
import { UnsupportedLocationState } from "@/components/UnsupportedLocationState";

const errorMessage = (error: unknown, fallback: string) =>
  error instanceof ApiError ? error.message : fallback;

export default function Home() {
  const [mode, setMode] = useState<"officer" | "farmer">("officer");
  const [districts, setDistricts] = useState<District[]>([]);
  const [blocks, setBlocks] = useState<Block[]>([]);
  const [panchayats, setPanchayats] = useState<PanchayatListItem[]>([]);
  const [districtId, setDistrictId] = useState("");
  const [blockId, setBlockId] = useState("");
  const [panchayatId, setPanchayatId] = useState("");
  const [panchayat, setPanchayat] = useState<Panchayat | null>(null);
  const [forecast, setForecast] = useState<Forecast | null>(null);
  const [apiConnected, setApiConnected] = useState(false);
  const [healthLoading, setHealthLoading] = useState(true);
  const [initialError, setInitialError] = useState("");
  const [panchayatError, setPanchayatError] = useState("");
  const [forecastError, setForecastError] = useState("");
  const [unsupportedLocationError, setUnsupportedLocationError] = useState("");
  const [panchayatLoading, setPanchayatLoading] = useState(false);
  const [forecastLoading, setForecastLoading] = useState(false);

  const loadInitialData = async () => {
    setInitialError("");
    setHealthLoading(true);
    const [healthResult, locationResult] = await Promise.allSettled([
      api.health(),
      Promise.all([api.districts(), api.blocks()]),
    ]);

    setApiConnected(healthResult.status === "fulfilled");
    setHealthLoading(false);

    if (locationResult.status === "fulfilled") {
      setDistricts(locationResult.value[0]);
      setBlocks(locationResult.value[1]);
    } else {
      setInitialError(
        errorMessage(locationResult.reason, "Unable to load location data.")
      );
    }
  };

  useEffect(() => {
    void loadInitialData();
  }, []);

  const loadPanchayats = async (nextBlockId: string) => {
    setPanchayatError("");
    setPanchayats([]);
    if (!nextBlockId) return;

    setPanchayatLoading(true);
    try {
      setPanchayats(await api.panchayatsForBlock(nextBlockId));
    } catch (error) {
      setPanchayatError(errorMessage(error, "Unable to load Panchayat data."));
    } finally {
      setPanchayatLoading(false);
    }
  };

  const selectDistrict = (id: string) => {
    setDistrictId(id);
    setBlockId("");
    setPanchayatId("");
    setPanchayat(null);
    setForecast(null);
    setPanchayats([]);
  };

  const selectBlock = (id: string) => {
    setBlockId(id);
    setPanchayatId("");
    setPanchayat(null);
    setForecast(null);
    void loadPanchayats(id);
  };

  const selectBlockFromMap = (mapBlockId: string) => {
    const block = blocks.find((b) => b.block_id === mapBlockId);
    if (!block) return;
    setDistrictId(block.district_id);
    setBlockId(mapBlockId);
    setPanchayatId("");
    setPanchayat(null);
    setForecast(null);
    setForecastError("");
    setUnsupportedLocationError("");
    void loadPanchayats(mapBlockId);
  };

  const selectPanchayat = async (id: string) => {
    setPanchayatId(id);
    setPanchayat(null);
    setForecast(null);
    setForecastError("");
    setUnsupportedLocationError("");
    if (!id) return;

    setForecastLoading(true);
    try {
      const [details, selectedForecast] = await Promise.all([
        api.panchayat(id),
        api.forecast(id),
      ]);
      setPanchayat(details);
      setForecast(selectedForecast);
    } catch (error) {
      if (error instanceof ApiError && error.status === 404) {
        setUnsupportedLocationError(error.message);
      } else {
        setForecastError(errorMessage(error, "Unable to load forecast data."));
      }
    } finally {
      setForecastLoading(false);
    }
  };

  return (
    <main className="min-h-screen">
      {/* Header with Brand, Mode Switch, and Service Status */}
      <header className="relative overflow-hidden bg-[#18362b] text-white">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_82%_15%,rgba(174,211,159,.18),transparent_34%),linear-gradient(120deg,transparent_45%,rgba(255,255,255,.05)_45%,rgba(255,255,255,.05)_46%,transparent_46%)]" />
        <div className="relative mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[#d7edda] text-moss">
                <Droplets className="h-5 w-5" />
              </div>
              <div>
                <span className="font-display text-sm font-bold tracking-[.18em]">
                  VARSHASENTINEL
                </span>
                <span className="ml-2 hidden rounded bg-white/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-[#b8dbbd] sm:inline-block">
                  {mode === "farmer" ? "Farmer Mode" : "Officer Mode"}
                </span>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              {/* Officer ↔ Farmer Mode Switch */}
              <div
                role="tablist"
                aria-label="Application mode"
                className="flex items-center rounded-lg border border-[#2e5746] bg-[#122820] p-1 shadow-inner"
              >
                <button
                  type="button"
                  role="tab"
                  aria-selected={mode === "officer"}
                  onClick={() => setMode("officer")}
                  className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-semibold transition min-h-[38px] sm:px-4 sm:text-sm ${
                    mode === "officer"
                      ? "bg-[#d7edda] text-[#18362b] shadow-sm font-bold"
                      : "text-[#b8dbbd] hover:text-white"
                  }`}
                >
                  <ShieldCheck className="h-4 w-4" />
                  <span>Officer</span>
                </button>
                <button
                  type="button"
                  role="tab"
                  aria-selected={mode === "farmer"}
                  onClick={() => setMode("farmer")}
                  className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-semibold transition min-h-[38px] sm:px-4 sm:text-sm ${
                    mode === "farmer"
                      ? "bg-[#e5a93c] text-[#2c1d02] shadow-sm font-black"
                      : "text-[#b8dbbd] hover:text-white"
                  }`}
                >
                  <Sprout className="h-4 w-4" />
                  <span>Farmer</span>
                </button>
              </div>

              <ApiStatus connected={apiConnected} loading={healthLoading} />
            </div>
          </div>

          <div className="max-w-3xl pb-2 pt-10 sm:pt-14">
            <p className="mb-3 text-xs font-bold uppercase tracking-[.22em] text-[#b8dbbd]">
              Hyperlocal Monsoon Intelligence
            </p>
            <h1 className="font-display text-3xl font-semibold leading-[1.08] tracking-tight sm:text-5xl lg:text-6xl">
              {mode === "farmer" ? (
                <>
                  Actionable rainfall signals<br />
                  <span className="text-[#b8dbbd]">for confident sowing decisions.</span>
                </>
              ) : (
                <>
                  See the season<br />
                  <span className="text-[#b8dbbd]">before it shifts.</span>
                </>
              )}
            </h1>
            <p className="mt-4 max-w-xl text-xs leading-relaxed text-[#d7e4da] sm:text-sm sm:leading-6">
              {mode === "farmer"
                ? "A verified observation layer providing straightforward answers to 'Should I sow now?' based on real agrometeorological guidance."
                : "A verified observation layer for local rainfall risk, onset signals, and agronomic decisions across supported Panchayats."}
            </p>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <div className="mx-auto -mt-6 max-w-7xl space-y-6 px-4 pb-16 sm:px-6 lg:px-8">
        {/* Step 1: Location Hierarchy Selector */}
        <LocationSelector
          districts={districts}
          blocks={blocks}
          panchayats={panchayats}
          districtId={districtId}
          blockId={blockId}
          panchayatId={panchayatId}
          loadingPanchayats={panchayatLoading}
          error={panchayatError || initialError}
          onDistrictChange={selectDistrict}
          onBlockChange={selectBlock}
          onPanchayatChange={(id) => void selectPanchayat(id)}
          onRetry={() => void loadInitialData()}
        />

        {/* Dynamic States */}
        {forecastLoading && (
          <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <LoadingState label="Loading verified forecast from service..." />
          </section>
        )}
        {unsupportedLocationError && (
          <UnsupportedLocationState message={unsupportedLocationError} />
        )}
        {forecastError && (
          <ErrorState
            message={forecastError}
            onRetry={() => void selectPanchayat(panchayatId)}
          />
        )}

        {/* Dashboard Content:
            When a Panchayat is selected and loaded:
            - Desktop (lg:): Spatial 2-column layout (Map on left, Forecast Panel on right)
            - Mobile (< lg:): Stacked hierarchy (Location -> Map -> Risk -> Outlook -> Advisory)
            When no Panchayat is selected yet:
            - Full-width interactive Map with guidance cards
        */}
        {panchayat && forecast && !forecastLoading ? (
          <div className="space-y-6 lg:grid lg:grid-cols-12 lg:gap-8 lg:space-y-0 lg:items-start">
            {/* Map Column (Centerpiece on Desktop) */}
            <div className="lg:col-span-5 xl:col-span-5 lg:sticky lg:top-6 space-y-2.5">
              <div className="flex items-center justify-between px-1">
                <h2 className="text-xs font-bold uppercase tracking-[.18em] text-slate-700">
                  Block-Level Risk Map
                </h2>
                <span className="text-[11px] font-medium text-slate-500">
                  Click block polygon to select
                </span>
              </div>
              <RiskMapView
                selectedBlockId={blockId}
                onBlockSelect={selectBlockFromMap}
              />
            </div>

            {/* Forecast Panel Column (Officer or Farmer Mode) */}
            <div className="lg:col-span-7 xl:col-span-7">
              {mode === "farmer" ? (
                <FarmerView forecast={forecast} panchayat={panchayat} />
              ) : (
                <ForecastSection forecast={forecast} panchayat={panchayat} />
              )}
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="flex items-center justify-between px-1">
              <h2 className="text-xs font-bold uppercase tracking-[.18em] text-slate-700">
                Block-Level Risk Map
              </h2>
              <span className="text-xs text-slate-500">
                Select a block on the map or use the dropdown above
              </span>
            </div>
            <RiskMapView
              selectedBlockId={blockId}
              onBlockSelect={selectBlockFromMap}
            />

            {!panchayatId && !initialError && (
              <div className="grid gap-4 border-t border-slate-200 pt-4 sm:grid-cols-3">
                <div className="flex gap-3 py-3">
                  <Activity className="h-5 w-5 shrink-0 text-moss" />
                  <div>
                    <p className="text-sm font-semibold text-ink">Local signals</p>
                    <p className="mt-1 text-xs leading-5 text-slate-500">
                      Forecasts are scoped to verified administrative areas.
                    </p>
                  </div>
                </div>
                <div className="flex gap-3 py-3">
                  <Database className="h-5 w-5 shrink-0 text-moss" />
                  <div>
                    <p className="text-sm font-semibold text-ink">Verified layer</p>
                    <p className="mt-1 text-xs leading-5 text-slate-500">
                      Every value shown is retrieved from the forecast service.
                    </p>
                  </div>
                </div>
                <div className="flex gap-3 py-3">
                  <ArrowDown className="h-5 w-5 shrink-0 text-moss" />
                  <div>
                    <p className="text-sm font-semibold text-ink">Start with a location</p>
                    <p className="mt-1 text-xs leading-5 text-slate-500">
                      Choose a district, block, and Panchayat above.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {!districts.length && !healthLoading && !initialError && (
          <EmptyState message="No district data available." />
        )}
      </div>
    </main>
  );
}
