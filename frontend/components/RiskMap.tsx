"use client";

import type { RiskMap } from "@/types/api";
import maplibregl, { type Map } from "maplibre-gl";
import { useEffect, useRef } from "react";
import { MapPinned } from "lucide-react";
import { LoadingState } from "./LoadingState";
import { ErrorState } from "./ErrorState";

function collectCoordinates(value: unknown, result: Array<[number, number]>): void {
  if (!Array.isArray(value)) return;
  if (value.length >= 2 && typeof value[0] === "number" && typeof value[1] === "number") { result.push([value[0], value[1]]); return; }
  value.forEach((item) => collectCoordinates(item, result));
}

export function RiskMap({ data, loading, error, onRetry }: { data: RiskMap | null; loading: boolean; error?: string; onRetry: () => void }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<Map | null>(null);
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    mapRef.current = new maplibregl.Map({ container: containerRef.current, style: { version: 8, sources: {}, layers: [{ id: "background", type: "background", paint: { "background-color": "#e8eee9" } }] }, center: [0, 0], zoom: 1 });
    mapRef.current.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    return () => { mapRef.current?.remove(); mapRef.current = null; };
  }, []);
  useEffect(() => {
    if (!data || !mapRef.current) return;
    const map = mapRef.current;
    const draw = () => {
      if (map.getSource("risk-map")) (map.getSource("risk-map") as maplibregl.GeoJSONSource).setData(data as never);
      else { map.addSource("risk-map", { type: "geojson", data: data as never }); map.addLayer({ id: "risk-fill", type: "fill", source: "risk-map", paint: { "fill-color": "#4c8b68", "fill-opacity": .35 } }); map.addLayer({ id: "risk-line", type: "line", source: "risk-map", paint: { "line-color": "#2f6b52", "line-width": 1.2 } }); }
      const coordinates: Array<[number, number]> = []; data.features.forEach((feature) => collectCoordinates(feature.geometry?.coordinates, coordinates));
      if (coordinates.length) { const bounds = coordinates.reduce((result, coordinate) => result.extend(coordinate), new maplibregl.LngLatBounds(coordinates[0], coordinates[0])); map.fitBounds(bounds, { padding: 40, maxZoom: 10, duration: 0 }); }
    };
    if (map.loaded()) draw(); else map.once("load", draw);
  }, [data]);
  return <section className="overflow-hidden border border-slate-200 bg-white"><div className="flex items-center justify-between border-b border-slate-200 px-5 py-4"><div className="flex items-center gap-2"><MapPinned className="h-4 w-4 text-moss" /><h2 className="font-display text-lg font-semibold">Supported risk map</h2></div>{data && <span className="text-xs text-slate-500">{data.features.length} mapped areas</span>}</div><div className="relative h-[360px] bg-[#e8eee9] sm:h-[430px]">{loading && <div className="absolute inset-0 z-10 flex items-center justify-center bg-white/80"><LoadingState label="Loading risk map..." /></div>}{error && <div className="absolute inset-0 z-10 flex items-center justify-center p-5"><ErrorState message={error} onRetry={onRetry} /></div>} {!loading && !error && !data && <div className="absolute inset-0 z-10 flex items-center justify-center p-5 text-sm text-slate-500">No risk map data available.</div>}<div ref={containerRef} className="h-full w-full" /></div></section>;
}