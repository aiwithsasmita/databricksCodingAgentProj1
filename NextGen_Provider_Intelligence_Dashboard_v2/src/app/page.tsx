"use client";

import { useState, useMemo } from "react";
import dynamic from "next/dynamic";
import { Filters, BubbleMetric, MapMode } from "@/lib/types";
import { hospitals } from "@/lib/dummy-data";
import { applyFilters, ALL } from "@/lib/filters";
import FilterBar from "@/components/FilterBar";
import HospitalTable from "@/components/HospitalTable";
import { ORG_TYPE_HEX } from "@/lib/colors";
import type { OrgType } from "@/lib/types";

const MapView = dynamic(() => import("@/components/MapView"), { ssr: false });
const ProviderUniverse = dynamic(
  () => import("@/components/ProviderUniverse"),
  { ssr: false }
);
const NpiSearch = dynamic(
  () => import("@/components/NpiSearch"),
  { ssr: false }
);

const defaultFilters: Filters = {
  specialty: ALL,
  billingPattern: ALL,
  serviceState: ALL,
  orgType: ALL,
};

const legendItems: { label: OrgType; color: string }[] = [
  { label: "Hospital", color: ORG_TYPE_HEX["Hospital"] },
  { label: "Nursing Home", color: ORG_TYPE_HEX["Nursing Home"] },
  { label: "Clinic", color: ORG_TYPE_HEX["Clinic"] },
  { label: "Rehab Center", color: ORG_TYPE_HEX["Rehab Center"] },
];

type PageView = "map" | "analytics" | "search";

export default function Home() {
  const [filters, setFilters] = useState<Filters>(defaultFilters);
  const [metric, setMetric] = useState<BubbleMetric>("totalPayment");
  const [mapMode, setMapMode] = useState<MapMode>("scatter");
  const [pageView, setPageView] = useState<PageView>("map");

  const filtered = useMemo(
    () => applyFilters(hospitals, filters),
    [filters]
  );

  return (
    <div className="flex min-h-screen flex-col">
      {/* Header */}
      <header className="flex items-center justify-between bg-uhc-navy-dark px-6 py-3">
        <div className="flex items-center gap-4">
          <img
            src="/uhc-logo-white.svg"
            alt="UnitedHealthcare"
            className="h-10 w-auto"
          />
          <div className="h-8 w-px bg-white/20" />
          <div>
            <h1 className="text-lg font-bold leading-tight text-white">
              NextGen Provider Intelligence Dashboard
            </h1>
            <p className="text-xs text-white/60">
              Provider Analytics &middot; UnitedHealthcare
            </p>
          </div>
        </div>
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-4">
            {legendItems.map((item) => (
              <div key={item.label} className="flex items-center gap-1.5">
                <span
                  className="inline-block h-3 w-3 rounded-full"
                  style={{ backgroundColor: item.color }}
                />
                <span className="text-xs text-white/70">{item.label}</span>
              </div>
            ))}
          </div>
        </div>
      </header>

      {/* App Description + Page Toggle */}
      <div className="border-b border-gray-200 bg-white px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="max-w-3xl">
            <p className="text-sm text-gray-600">
              Agentic AI-powered analytics platform for monitoring provider behavior
              across the UnitedHealthcare network. Analyze NPI-level billing patterns,
              geographic distribution, specialty mix, and payment trends to identify
              anomalies and optimize network performance.
            </p>
          </div>

          <div className="flex items-center gap-1 rounded-lg border border-gray-200 bg-gray-50 p-1">
            <button
              onClick={() => setPageView("map")}
              className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition ${
                pageView === "map"
                  ? "bg-white text-uhc-navy shadow-sm"
                  : "text-gray-500 hover:text-gray-700"
              }`}
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 6.75V15m6-6v8.25m.503 3.498 4.875-2.437c.381-.19.622-.58.622-1.006V4.82c0-.836-.88-1.38-1.628-1.006l-3.869 1.934c-.317.159-.69.159-1.006 0L9.503 3.252a1.125 1.125 0 0 0-1.006 0L3.622 5.689C3.24 5.88 3 6.27 3 6.695V19.18c0 .836.88 1.38 1.628 1.006l3.869-1.934c.317-.159.69-.159 1.006 0l4.994 2.497c.317.158.69.158 1.006 0Z" />
              </svg>
              Map View
            </button>
            <button
              onClick={() => setPageView("analytics")}
              className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition ${
                pageView === "analytics"
                  ? "bg-white text-uhc-navy shadow-sm"
                  : "text-gray-500 hover:text-gray-700"
              }`}
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
              </svg>
              Provider Universe
            </button>
            <button
              onClick={() => setPageView("search")}
              className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition ${
                pageView === "search"
                  ? "bg-white text-uhc-navy shadow-sm"
                  : "text-gray-500 hover:text-gray-700"
              }`}
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
              </svg>
              NPI Search
            </button>
          </div>
        </div>
      </div>

      {/* Page Content */}
      {pageView === "map" && (
        <>
          <FilterBar
            filters={filters}
            onChange={setFilters}
            metric={metric}
            onMetricChange={setMetric}
            mapMode={mapMode}
            onMapModeChange={setMapMode}
            resultCount={filtered.length}
          />
          <MapView
            data={filtered}
            metric={metric}
            mapMode={mapMode}
          />
          <div className="flex-1 bg-white">
            <HospitalTable data={filtered} />
          </div>
        </>
      )}
      {pageView === "analytics" && (
        <ProviderUniverse data={filtered} />
      )}
      {pageView === "search" && (
        <NpiSearch MapView={MapView} />
      )}
    </div>
  );
}
