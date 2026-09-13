"use client";

"use client";

import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

import { api } from "@/lib/api";
import RiskLegend from "./RiskLegend";

interface RiskMapProps {
  selectedPanchayat: string;
  onPanchayatSelect: (id: string) => void;
}

export function RiskMap({
  selectedPanchayat,
  onPanchayatSelect,
}: RiskMapProps) {

  const mapContainer = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);

  useEffect(() => {
    if (!mapContainer.current) return;

    const map = new maplibregl.Map({
      container: mapContainer.current,

      // Replace this with your team's approved MapLibre style.
      style: {
        version: 8,
        sources: {},
        layers: [
          {
            id: "background",
            type: "background",
            paint: {
              "background-color": "#eef2f5",
            },
          },
        ],
      },

      center: [87.855, 22.986],
      zoom: 6,
    });

    map.addControl(
      new maplibregl.NavigationControl(),
      "top-right"
    );

    mapRef.current = map;

    async function loadRiskMap() {
      try {
        const data = await api.getRiskMap();

        map.on("load", () => {

          map.addSource("risk-map", {
            type: "geojson",
            data,
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

                "VERY HIGH",
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

            const feature = event.features?.[0];

            if (!feature) return;

            const id = feature.properties?.panchayat_id;

            if (id === undefined) return;

            onPanchayatSelect(String(id));
          });

          map.on("mouseenter", "risk-fill", () => {
            map.getCanvas().style.cursor = "pointer";
          });

          map.on("mouseleave", "risk-fill", () => {
            map.getCanvas().style.cursor = "";
          });
        });

      } catch (error) {
        console.error("Risk map loading failed:", error);
      }
    }

    loadRiskMap();

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [onPanchayatSelect]);

  // Highlight selected Panchayat
  useEffect(() => {

    const map = mapRef.current;

    if (!map || !map.getSource("risk-map")) {
      return;
    }

    if (!selectedPanchayat) {
      return;
    }

    map.setFilter(
      "selected-risk-outline",
      [
        "==",
        ["get", "panchayat_id"],
        selectedPanchayat,
      ]
    );

  }, [selectedPanchayat]);

  // Add selection layer after map load
  useEffect(() => {

    const map = mapRef.current;

    if (!map) return;

    const addSelectionLayer = () => {

      if (!map.getLayer("selected-risk-outline")) {

        map.addLayer({
          id: "selected-risk-outline",
          type: "line",
          source: "risk-map",

          paint: {
            "line-color": "#111827",
            "line-width": 4,
          },

          filter: [
            "==",
            ["get", "panchayat_id"],
            "",
          ],
        });
      }
    };

    if (map.loaded()) {
      addSelectionLayer();
    } else {
      map.once("load", addSelectionLayer);
    }

  }, []);

  return (
    <div className="relative h-full min-h-[500px] overflow-hidden rounded-xl border border-slate-200 bg-slate-100">

      <div
        ref={mapContainer}
        className="absolute inset-0"
      />

      <RiskLegend />

    </div>
  );
}

export default RiskMap;