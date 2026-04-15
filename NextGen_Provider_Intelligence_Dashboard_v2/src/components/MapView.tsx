"use client";

import { useState, useMemo } from "react";
import DeckGL from "@deck.gl/react";
import { GeoJsonLayer, ScatterplotLayer } from "@deck.gl/layers";
import { HeatmapLayer, HexagonLayer } from "@deck.gl/aggregation-layers";
import { LightingEffect, AmbientLight, DirectionalLight } from "@deck.gl/core";
import type { MapViewState, PickingInfo, Layer } from "@deck.gl/core";
import { webgl2Adapter } from "@luma.gl/webgl";
import { luma } from "@luma.gl/core";
import { feature } from "topojson-client";
import type { Topology, GeometryCollection } from "topojson-specification";
import usTopology from "@/data/us-states-topo.json";
import { Hospital, BubbleMetric, MapMode } from "@/lib/types";
import { ORG_TYPE_COLORS } from "@/lib/colors";

luma.registerAdapters([webgl2Adapter]);
const DEVICE_PROPS = { adapters: [webgl2Adapter], type: "webgl" as const };

const usStatesGeoJson = feature(
  usTopology as unknown as Topology,
  (usTopology as unknown as Topology).objects.states as GeometryCollection
);

const usNationGeoJson = feature(
  usTopology as unknown as Topology,
  (usTopology as unknown as Topology).objects.nation as GeometryCollection
);

const INITIAL_VIEW: MapViewState = {
  latitude: 39.8,
  longitude: -98.5,
  zoom: 3.8,
  pitch: 0,
  bearing: 0,
};

const US_BOUNDS = {
  minLng: -170,
  maxLng: -60,
  minLat: 18,
  maxLat: 72,
};
const MIN_ZOOM = 2.5;
const MAX_ZOOM = 12;

function clampView(vs: MapViewState): MapViewState {
  return {
    ...vs,
    longitude: Math.max(US_BOUNDS.minLng, Math.min(US_BOUNDS.maxLng, vs.longitude)),
    latitude: Math.max(US_BOUNDS.minLat, Math.min(US_BOUNDS.maxLat, vs.latitude)),
    zoom: Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, vs.zoom)),
  };
}

const HEATMAP_COLORS: [number, number, number, number][] = [
  [65, 182, 196, 0],
  [44, 127, 184, 80],
  [37, 52, 148, 140],
  [255, 170, 0, 180],
  [255, 56, 96, 220],
  [190, 0, 60, 255],
];

const HEX_COLORS: [number, number, number][] = [
  [65, 182, 196],
  [44, 127, 184],
  [37, 52, 148],
  [255, 170, 0],
  [255, 56, 96],
  [190, 0, 60],
];

const ambientLight = new AmbientLight({ color: [255, 255, 255], intensity: 1.0 });
const dirLight = new DirectionalLight({
  color: [255, 255, 255],
  intensity: 0.8,
  direction: [-10, -8, -5],
});
const lightingEffect = new LightingEffect({ ambientLight, dirLight });

interface Props {
  data: Hospital[];
  metric: BubbleMetric;
  mapMode: MapMode;
  highlightNpi?: string;
}

export default function MapView({ data, metric, mapMode, highlightNpi }: Props) {
  const [viewState, setViewState] = useState<MapViewState>(INITIAL_VIEW);
  const [hovered, setHovered] = useState<{
    hospital: Hospital;
    x: number;
    y: number;
  } | null>(null);

  const maxVal = useMemo(() => {
    if (data.length === 0) return 1;
    return Math.max(...data.map((d) => d[metric]));
  }, [data, metric]);

  const handleHover = useMemo(
    () => (info: PickingInfo<Hospital>) => {
      if (info.object) {
        setHovered({ hospital: info.object, x: info.x!, y: info.y! });
      } else {
        setHovered(null);
      }
    },
    []
  );

  const layers = useMemo(() => {
    const result: Layer[] = [];

    result.push(
      new GeoJsonLayer({
        id: "us-nation-fill",
        data: usNationGeoJson,
        filled: true,
        stroked: false,
        getFillColor: [243, 244, 246, 255],
        pickable: false,
      })
    );

    result.push(
      new GeoJsonLayer({
        id: "us-states-borders",
        data: usStatesGeoJson,
        filled: false,
        stroked: true,
        getLineColor: [189, 195, 207, 255],
        lineWidthMinPixels: 1,
        lineWidthMaxPixels: 2,
        pickable: false,
      })
    );

    if (mapMode === "scatter") {
      result.push(
        new ScatterplotLayer<Hospital>({
          id: "scatter",
          data,
          pickable: true,
          opacity: 0.9,
          stroked: true,
          filled: true,
          radiusUnits: "pixels",
          lineWidthMinPixels: 1.5,
          getPosition: (d) => [d.longitude, d.latitude],
          getRadius: (d) => {
            if (highlightNpi && d.npi === highlightNpi) return 22;
            const ratio = d[metric] / maxVal;
            return 7 + ratio * 28;
          },
          getFillColor: (d) => {
            if (highlightNpi && d.npi === highlightNpi) return [255, 40, 40, 255];
            return [...ORG_TYPE_COLORS[d.orgType], 190];
          },
          getLineColor: (d) => {
            if (highlightNpi && d.npi === highlightNpi) return [255, 255, 255, 255];
            return [...ORG_TYPE_COLORS[d.orgType], 255];
          },
          updateTriggers: {
            getRadius: [metric, maxVal, highlightNpi],
            getFillColor: [highlightNpi],
            getLineColor: [highlightNpi],
          },
          onHover: handleHover,
        })
      );
    }

    if (mapMode === "heatmap") {
      result.push(
        new HeatmapLayer<Hospital>({
          id: "heatmap",
          data,
          getPosition: (d) => [d.longitude, d.latitude],
          getWeight: (d) => d[metric],
          radiusPixels: 60,
          intensity: 1.2,
          threshold: 0.05,
          colorRange: HEATMAP_COLORS,
          aggregation: "SUM",
        })
      );
    }

    if (mapMode === "hexagon") {
      result.push(
        new HexagonLayer<Hospital>({
          id: "hexagon",
          data,
          getPosition: (d) => [d.longitude, d.latitude],
          getElevationWeight: (d) => d[metric],
          getColorWeight: (d) => d[metric],
          elevationScale: metric === "totalPayment" ? 0.05 : 50,
          radius: 50000,
          extruded: true,
          pickable: true,
          coverage: 0.88,
          elevationRange: [0, 3000],
          colorRange: HEX_COLORS,
          material: {
            ambient: 0.64,
            diffuse: 0.6,
            shininess: 32,
          },
          updateTriggers: {
            getElevationWeight: [metric],
            getColorWeight: [metric],
          },
        })
      );
    }

    return result;
  }, [data, metric, maxVal, mapMode, highlightNpi, handleHover]);

  const currentView =
    mapMode === "hexagon"
      ? { ...viewState, pitch: Math.max(viewState.pitch ?? 0, 45) }
      : viewState;

  const effects = mapMode === "hexagon" ? [lightingEffect] : [];

  return (
    <div
      className="relative w-full"
      style={{ height: "65vh", background: "#dce4ed" }}
    >
      <DeckGL
        viewState={currentView}
        onViewStateChange={({ viewState: vs }) =>
          setViewState(clampView(vs as MapViewState))
        }
        controller={true}
        layers={layers}
        effects={effects}
        getCursor={({ isHovering }) => (isHovering ? "pointer" : "grab")}
        deviceProps={DEVICE_PROPS}
      />

      {mapMode === "scatter" && (
        <div className="absolute bottom-4 left-4 z-40 rounded-lg border border-gray-200 bg-white/90 px-3 py-2 shadow-md backdrop-blur-sm">
          <p className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-gray-500">
            Bubble = {metric === "totalPayment" ? "Payment" : "Bed Count"}
          </p>
          <div className="flex items-center gap-1">
            <span className="inline-block h-2 w-2 rounded-full bg-blue-500/50" />
            <span className="text-[10px] text-gray-400">Low</span>
            <span className="mx-1 inline-block h-4 w-4 rounded-full bg-blue-500/50" />
            <span className="text-[10px] text-gray-400">Mid</span>
            <span className="mx-1 inline-block h-6 w-6 rounded-full bg-blue-500/50" />
            <span className="text-[10px] text-gray-400">High</span>
          </div>
        </div>
      )}

      {mapMode === "heatmap" && (
        <div className="absolute bottom-4 left-4 z-40 rounded-lg border border-gray-200 bg-white/90 px-3 py-2 shadow-md backdrop-blur-sm">
          <p className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-gray-500">
            Density by {metric === "totalPayment" ? "Payment" : "Bed Count"}
          </p>
          <div className="flex items-center gap-0.5">
            {["#41B6C4", "#2C7FB8", "#253494", "#FFAA00", "#FF3860", "#BE003C"].map(
              (c) => (
                <span
                  key={c}
                  className="h-3 w-6 first:rounded-l last:rounded-r"
                  style={{ backgroundColor: c }}
                />
              )
            )}
          </div>
          <div className="mt-0.5 flex justify-between text-[9px] text-gray-400">
            <span>Low</span>
            <span>High</span>
          </div>
        </div>
      )}

      {mapMode === "hexagon" && (
        <div className="absolute bottom-4 left-4 z-40 rounded-lg border border-gray-200 bg-white/90 px-3 py-2 shadow-md backdrop-blur-sm">
          <p className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-gray-500">
            3D Hex: Height & Color = {metric === "totalPayment" ? "Payment" : "Beds"}
          </p>
          <p className="text-[9px] text-gray-400">
            Drag + right-click to rotate / tilt
          </p>
        </div>
      )}

      {hovered && (
        <div
          className="pointer-events-none absolute z-50 rounded-lg border border-gray-200 bg-white/95 px-4 py-3 shadow-xl backdrop-blur-sm"
          style={{
            left: hovered.x + 12,
            top: hovered.y + 12,
            maxWidth: 300,
          }}
        >
          <p className="text-sm font-bold text-uhc-navy">
            {hovered.hospital.name}
          </p>
          <div className="mt-1 space-y-0.5 text-xs text-gray-500">
            <p>
              <span className="font-semibold text-gray-700">Type:</span>{" "}
              {hovered.hospital.orgType}
            </p>
            <p>
              <span className="font-semibold text-gray-700">Billing:</span>{" "}
              {hovered.hospital.billingPattern}
            </p>
            <p>
              <span className="font-semibold text-gray-700">Efficiency:</span>{" "}
              {(hovered.hospital.billingEfficiency * 100).toFixed(0)}%
            </p>
            <p>
              <span className="font-semibold text-gray-700">Claims:</span>{" "}
              {hovered.hospital.claimCount.toLocaleString()}
            </p>
            <p>
              <span className="font-semibold text-gray-700">Payment:</span> $
              {hovered.hospital.totalPayment.toLocaleString()}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
