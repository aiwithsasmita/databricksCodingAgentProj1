"use client";

import { Filters, BubbleMetric, MapMode } from "@/lib/types";
import { hospitals } from "@/lib/dummy-data";
import { getUniqueValues, getUniqueStates, ALL } from "@/lib/filters";

const specialties = getUniqueValues(hospitals, "specialty");
const billingPatterns = getUniqueValues(hospitals, "billingPattern");
const orgTypes = getUniqueValues(hospitals, "orgType");
const serviceStates = getUniqueStates(hospitals, "serviceAddress");

interface Props {
  filters: Filters;
  onChange: (f: Filters) => void;
  metric: BubbleMetric;
  onMetricChange: (m: BubbleMetric) => void;
  mapMode: MapMode;
  onMapModeChange: (m: MapMode) => void;
  resultCount: number;
}

function Select({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (v: string) => void;
}) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-[11px] font-semibold uppercase tracking-wider text-white/70">
        {label}
      </label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-md border border-white/20 bg-white/10 px-3 py-1.5 text-sm text-white outline-none transition focus:border-uhc-orange focus:ring-1 focus:ring-uhc-orange"
      >
        <option value={ALL} className="text-foreground">
          All
        </option>
        {options.map((o) => (
          <option key={o} value={o} className="text-foreground">
            {o}
          </option>
        ))}
      </select>
    </div>
  );
}

const mapModes: { value: MapMode; label: string }[] = [
  { value: "scatter", label: "Bubbles" },
  { value: "heatmap", label: "Heatmap" },
  { value: "hexagon", label: "3D Hex" },
];

export default function FilterBar({
  filters,
  onChange,
  metric,
  onMetricChange,
  mapMode,
  onMapModeChange,
  resultCount,
}: Props) {
  const set = (key: keyof Filters, val: string) =>
    onChange({ ...filters, [key]: val });

  return (
    <div className="bg-uhc-navy px-6 py-4">
      <div className="flex flex-wrap items-end gap-4">
        <Select
          label="Specialty"
          value={filters.specialty}
          options={specialties}
          onChange={(v) => set("specialty", v)}
        />
        <Select
          label="Billing Pattern"
          value={filters.billingPattern}
          options={billingPatterns}
          onChange={(v) => set("billingPattern", v)}
        />
        <Select
          label="Service State"
          value={filters.serviceState}
          options={serviceStates}
          onChange={(v) => set("serviceState", v)}
        />
        <Select
          label="Org Type"
          value={filters.orgType}
          options={orgTypes}
          onChange={(v) => set("orgType", v)}
        />

        <div className="flex flex-col gap-1">
          <label className="text-[11px] font-semibold uppercase tracking-wider text-white/70">
            Bubble Size
          </label>
          <div className="flex overflow-hidden rounded-md border border-white/20">
            <button
              onClick={() => onMetricChange("totalPayment")}
              className={`px-3 py-1.5 text-sm font-medium transition ${
                metric === "totalPayment"
                  ? "bg-uhc-orange text-white"
                  : "bg-white/10 text-white/70 hover:bg-white/20"
              }`}
            >
              Payment
            </button>
            <button
              onClick={() => onMetricChange("bedCount")}
              className={`px-3 py-1.5 text-sm font-medium transition ${
                metric === "bedCount"
                  ? "bg-uhc-orange text-white"
                  : "bg-white/10 text-white/70 hover:bg-white/20"
              }`}
            >
              Beds
            </button>
          </div>
        </div>

        <div className="flex flex-col gap-1">
          <label className="text-[11px] font-semibold uppercase tracking-wider text-white/70">
            Map View
          </label>
          <div className="flex overflow-hidden rounded-md border border-white/20">
            {mapModes.map((m) => (
              <button
                key={m.value}
                onClick={() => onMapModeChange(m.value)}
                className={`px-3 py-1.5 text-sm font-medium transition ${
                  mapMode === m.value
                    ? "bg-uhc-teal text-white"
                    : "bg-white/10 text-white/70 hover:bg-white/20"
                }`}
              >
                {m.label}
              </button>
            ))}
          </div>
        </div>

        <div className="ml-auto flex items-end">
          <span className="rounded-full bg-uhc-orange/20 px-3 py-1.5 text-sm font-semibold text-white">
            {resultCount} providers
          </span>
        </div>
      </div>
    </div>
  );
}
