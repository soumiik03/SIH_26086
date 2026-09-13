"use client";

import { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

import { api, ApiError } from "@/lib/api";
import type { RiskMap as RiskMapData } from "@/types/api";
import { EmptyState } from "./EmptyState";
import { ErrorState } from "./ErrorState";
import { LoadingState } from "./LoadingState";
import RiskLegend from "./RiskLegend";

interface RiskMapProps {
  onPanchayatSelect: (id: string) => void;
}

const errorMessage = (error: unknown) =>
  error instanceof ApiError ? error.message : "Unable to load risk map data.";

export function RiskMap({ onPanchayatSelect }: RiskMapProps) {
  const mapContainer = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const [data, setData] = useState<RiskMapData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    const loadRiskMap = async () => {
      setLoading(true);
      setError("");

      try {
        const riskMap = await api.riskMap();
        if (!cancelled) setData(riskMap);
      } catch (riskMapError) {
        if (!cancelled) setError(errorMessage(riskMapError));
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    void loadRiskMap();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!data || !mapContainer.current) return;

    const geoJsonData = {
      ...data,
      features: data.features.filter((feature) => feature.geometry !== null),
    } as unknown as GeoJSON.FeatureCollection;

    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: {
        version: 8,
        sources: {},
        layers: [
          {
            id: "background",
            type: "background",
            paint: { "background-color": "#eef2f5" },
          },
        ],
      },
      center: [87.855, 22.986],
      zoom: 6,
    });

    map.addControl(new maplibregl.NavigationControl(), "top-right");
    mapRef.current = map;

    map.on("load", () => {
      map.addSource("risk-map", {
        type: "geojson",
        data: geoJsonData,
        promoteId: "panchayat_id",
      });

      map.addLayer({
        id: "risk-fill",
        type: "fill",
        source: "risk-map",
        paint: {
          "fill-color": [
            "match",
            ["get", "risk_level"],
            "LOW",
            "#22c55e",
            "MODERATE",
            "#facc15",
            "HIGH",
            "#f97316",
            "VERY_HIGH",
            "#dc2626",
            "#94a3b8",
          ],
          "fill-opacity": 0.55,
        },
      });

      map.addLayer({
        id: "risk-outline",
        type: "line",
        source: "risk-map",
        paint: {
          "line-color": "#475569",
          "line-width": 0.8,
          "line-opacity": 0.7,
        },
      });

      map.on("click", "risk-fill", (event) => {
        const id = event.features?.[0]?.properties?.panchayat_id;
        if (id !== undefined) onPanchayatSelect(String(id));
      });

      map.on("mouseenter", "risk-fill", () => {
        map.getCanvas().style.cursor = "pointer";
      });

      map.on("mouseleave", "risk-fill", () => {
        map.getCanvas().style.cursor = "";
      });
    });

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [data, onPanchayatSelect]);

  return (
    <section className="space-y-3">
      {loading && <LoadingState label="Loading risk map..." />}
      {error && <ErrorState message={error} onRetry={() => window.location.reload()} />}
      {!loading && !error && data && data.features.length === 0 && (
        <EmptyState message="No risk map data available." />
      )}
      {!loading && !error && data && data.features.length > 0 && (
        <div className="relative h-full min-h-[500px] overflow-hidden rounded-xl border border-slate-200 bg-slate-100">
          <div ref={mapContainer} className="absolute inset-0" />
          <RiskLegend />
        </div>
      )}
    </section>
  );
}

export default RiskMap;
