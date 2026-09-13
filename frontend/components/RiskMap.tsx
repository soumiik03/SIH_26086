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
  selectedBlockId: string;
  onBlockSelect: (id: string) => void;
}

const errorMessage = (error: unknown) =>
  error instanceof ApiError ? error.message : "Unable to load risk map data.";

export function RiskMap({ selectedBlockId, onBlockSelect }: RiskMapProps) {
  const mapContainer = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const selectedBlockIdRef = useRef(selectedBlockId);
  const onBlockSelectRef = useRef(onBlockSelect);
  const [data, setData] = useState<RiskMapData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  selectedBlockIdRef.current = selectedBlockId;
  onBlockSelectRef.current = onBlockSelect;

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
    const container = mapContainer.current;
    if (!container) return;

    console.log("[RiskMap] Initializing MapLibre instance. Container dims:", container.clientWidth, "x", container.clientHeight);
    const map = new maplibregl.Map({
      container,
      style: {
        version: 8,
        sources: {},
        layers: [
          {
            id: "background",
            type: "background",
            paint: { "background-color": "#f1f5f9" },
          },
        ],
      },
      center: [87.85, 24.43],
      zoom: 6.5,
    });

    (window as any).__map = map;

    map.addControl(new maplibregl.NavigationControl(), "top-right");
    mapRef.current = map;

    map.on("error", (e) => {
      console.error("[RiskMap] MapLibre error event:", e);
    });

    map.on("click", "risk-fill", (event) => {
      const id = event.features?.[0]?.properties?.block_id;
      console.log("[RiskMap] Click on risk-fill, block_id:", id);
      if (id !== undefined && onBlockSelectRef.current) {
        onBlockSelectRef.current(String(id));
      }
    });

    map.on("mouseenter", "risk-fill", () => {
      map.getCanvas().style.cursor = "pointer";
    });

    map.on("mouseleave", "risk-fill", () => {
      map.getCanvas().style.cursor = "";
    });

    const resizeObserver = new ResizeObserver(() => {
      map.resize();
    });
    resizeObserver.observe(container);

    return () => {
      resizeObserver.disconnect();
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // When data arrives or changes, add/update GeoJSON source and layers
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !data) return;

    const geoJsonData = {
      ...data,
      features: data.features.filter((feature) => feature.geometry !== null),
    } as unknown as GeoJSON.FeatureCollection;

    console.log("[RiskMap] Updating source with features:", geoJsonData.features.length);

    const updateSourceAndLayers = () => {
      try {
        map.resize();

        const existingSource = map.getSource("risk-map") as maplibregl.GeoJSONSource | undefined;
        if (existingSource) {
          existingSource.setData(geoJsonData);
          console.log("[RiskMap] Existing source 'risk-map' updated with setData");
        } else {
          map.addSource("risk-map", {
            type: "geojson",
            data: geoJsonData,
          });
          console.log("[RiskMap] Source 'risk-map' added");
        }

        if (!map.getLayer("risk-fill")) {
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
                "#22c55e",
              ],
              "fill-opacity": 0.65,
            },
          });
          console.log("[RiskMap] Layer 'risk-fill' added");
        }

        if (!map.getLayer("risk-outline")) {
          map.addLayer({
            id: "risk-outline",
            type: "line",
            source: "risk-map",
            paint: {
              "line-color": "#334155",
              "line-width": 1.2,
              "line-opacity": 0.8,
            },
          });
          console.log("[RiskMap] Layer 'risk-outline' added");
        }

        if (!map.getLayer("selected-risk-outline")) {
          map.addLayer({
            id: "selected-risk-outline",
            type: "line",
            source: "risk-map",
            paint: {
              "line-color": "#0f172a",
              "line-width": 4,
              "line-opacity": 1.0,
            },
            filter: ["==", ["get", "block_id"], selectedBlockIdRef.current || ""],
          });
          console.log("[RiskMap] Layer 'selected-risk-outline' added");
        }

        // Calculate bounding box from GeoJSON
        let minLon = 180, minLat = 90, maxLon = -180, maxLat = -90;
        let count = 0;
        const scanCoords = (coords: any) => {
          if (typeof coords[0] === "number") {
            const [lon, lat] = coords;
            if (lon < minLon) minLon = lon;
            if (lon > maxLon) maxLon = lon;
            if (lat < minLat) minLat = lat;
            if (lat > maxLat) maxLat = lat;
            count++;
          } else if (Array.isArray(coords)) {
            for (const c of coords) scanCoords(c);
          }
        };

        for (const f of geoJsonData.features) {
          if (f.geometry && "coordinates" in f.geometry) {
            scanCoords((f.geometry as any).coordinates);
          }
        }

        console.log(`[RiskMap] Scanned ${count} coordinates. Bounds: [${minLon}, ${minLat}] to [${maxLon}, ${maxLat}]`);
        if (minLon < maxLon && minLat < maxLat) {
          map.fitBounds(
            [
              [minLon, minLat],
              [maxLon, maxLat],
            ],
            { padding: 30, duration: 0 }
          );
          console.log("[RiskMap] fitBounds called with calculated bounds. New center:", map.getCenter(), "zoom:", map.getZoom());
        }
      } catch (err) {
        console.error("[RiskMap] Error updating source/layers:", err);
      }
    };

    if (map.loaded()) {
      updateSourceAndLayers();
    } else {
      map.once("load", updateSourceAndLayers);
    }
  }, [data]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.getLayer("selected-risk-outline")) return;

    map.setFilter("selected-risk-outline", [
      "==",
      ["get", "block_id"],
      selectedBlockId,
    ]);
  }, [selectedBlockId]);

  return (
    <section className="space-y-3">
      {error && <ErrorState message={error} onRetry={() => window.location.reload()} />}
      {!loading && !error && data && data.features.length === 0 && (
        <EmptyState message="No risk map data available." />
      )}
      <div className="relative h-[380px] sm:h-[480px] lg:h-[620px] w-full overflow-hidden rounded-xl border border-slate-200 bg-slate-100 shadow-sm">
        <div ref={mapContainer} className="absolute inset-0" />
        {loading && (
          <div className="absolute inset-0 z-20 flex items-center justify-center bg-slate-100/75 backdrop-blur-[2px]">
            <LoadingState label="Loading block-level risk map..." />
          </div>
        )}
        <RiskLegend />
      </div>
    </section>
  );
}

export default RiskMap;
