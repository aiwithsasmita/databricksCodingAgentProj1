"use client";

import { useMemo } from "react";
import dynamic from "next/dynamic";
import type { Data as PlotlyData } from "plotly.js";
import { Hospital } from "@/lib/types";
import { ORG_TYPE_HEX } from "@/lib/colors";
import type { OrgType } from "@/lib/types";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

const orgOrder: OrgType[] = ["Hospital", "Nursing Home", "Clinic", "Rehab Center"];
const orgColors = orgOrder.map((o) => ORG_TYPE_HEX[o]);

interface Props {
  data: Hospital[];
}

export default function ProviderUniverse({ data }: Props) {
  const stats = useMemo(() => {
    const totalPayment = data.reduce((s, d) => s + d.totalPayment, 0);
    const totalClaims = data.reduce((s, d) => s + d.claimCount, 0);
    const totalBeds = data.reduce((s, d) => s + d.bedCount, 0);
    const uniqueStates = new Set(data.map((d) => d.serviceAddress.state)).size;
    return { totalPayment, totalClaims, totalBeds, uniqueStates };
  }, [data]);

  const byOrgType = useMemo(() => {
    const counts: Record<string, number> = {};
    const payments: Record<string, number> = {};
    for (const d of data) {
      counts[d.orgType] = (counts[d.orgType] || 0) + 1;
      payments[d.orgType] = (payments[d.orgType] || 0) + d.totalPayment;
    }
    return {
      labels: orgOrder,
      counts: orgOrder.map((o) => counts[o] || 0),
      payments: orgOrder.map((o) => payments[o] || 0),
    };
  }, [data]);

  const bySpecialty = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const d of data) {
      counts[d.specialty] = (counts[d.specialty] || 0) + 1;
    }
    const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]);
    return { labels: sorted.map(([l]) => l), values: sorted.map(([, v]) => v) };
  }, [data]);

  const byBilling = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const d of data) {
      counts[d.billingPattern] = (counts[d.billingPattern] || 0) + 1;
    }
    const order = ["High Volume", "Moderate", "Low Volume", "Outlier"];
    return {
      labels: order,
      values: order.map((o) => counts[o] || 0),
    };
  }, [data]);

  const byState = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const d of data) {
      counts[d.serviceAddress.state] = (counts[d.serviceAddress.state] || 0) + 1;
    }
    const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 15);
    return { labels: sorted.map(([l]) => l), values: sorted.map(([, v]) => v) };
  }, [data]);

  const efficiencyByOrg = useMemo(() => {
    const sums: Record<string, { total: number; count: number }> = {};
    for (const d of data) {
      if (!sums[d.orgType]) sums[d.orgType] = { total: 0, count: 0 };
      sums[d.orgType].total += d.billingEfficiency;
      sums[d.orgType].count += 1;
    }
    return {
      labels: orgOrder,
      values: orgOrder.map(
        (o) => sums[o] ? Math.round((sums[o].total / sums[o].count) * 100) : 0
      ),
    };
  }, [data]);

  const plotLayout = {
    paper_bgcolor: "transparent",
    plot_bgcolor: "transparent",
    font: { family: "var(--font-geist-sans), system-ui, sans-serif", color: "#374151", size: 11 },
    margin: { l: 50, r: 20, t: 36, b: 50 },
    height: 260,
  };

  const plotConfig = { displayModeBar: false, responsive: true };

  return (
    <div className="bg-gray-50 px-6 py-6">
      <div className="mb-6 grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="Total Providers" value={data.length.toLocaleString()} color="text-blue-600" />
        <StatCard label="Total Payment" value={`$${(stats.totalPayment / 1e6).toFixed(1)}M`} color="text-emerald-600" />
        <StatCard label="Total Claims" value={stats.totalClaims.toLocaleString()} color="text-violet-600" />
        <StatCard label="States Covered" value={String(stats.uniqueStates)} color="text-rose-500" />
      </div>

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <ChartCard title="Providers by Organization Type">
          <Plot
            data={[{
              type: "bar",
              x: byOrgType.labels,
              y: byOrgType.counts,
              marker: { color: orgColors },
            } as PlotlyData]}
            layout={{ ...plotLayout, xaxis: { tickangle: 0 }, yaxis: { title: { text: "Count" } } }}
            config={plotConfig}
            className="w-full"
          />
        </ChartCard>

        <ChartCard title="Total Payment by Organization Type">
          <Plot
            data={[{
              type: "bar",
              x: byOrgType.labels,
              y: byOrgType.payments.map((v) => v / 1e6),
              marker: { color: orgColors },
            } as PlotlyData]}
            layout={{ ...plotLayout, xaxis: { tickangle: 0 }, yaxis: { title: { text: "Payment ($M)" } } }}
            config={plotConfig}
            className="w-full"
          />
        </ChartCard>

        <ChartCard title="Provider Distribution by Specialty">
          <Plot
            data={[{
              type: "bar",
              x: bySpecialty.values,
              y: bySpecialty.labels,
              orientation: "h",
              marker: { color: "#2962FF" },
            } as PlotlyData]}
            layout={{
              ...plotLayout,
              xaxis: { title: { text: "Count" } },
              yaxis: { autorange: "reversed" as const },
              margin: { ...plotLayout.margin, l: 110 },
            }}
            config={plotConfig}
            className="w-full"
          />
        </ChartCard>

        <ChartCard title="Billing Pattern Breakdown">
          <Plot
            data={[{
              type: "pie",
              labels: byBilling.labels,
              values: byBilling.values,
              hole: 0.45,
              marker: { colors: ["#2962FF", "#00B894", "#FF3860", "#8E44DF"] },
              textinfo: "label+percent",
              textposition: "outside",
            }]}
            layout={{ ...plotLayout, showlegend: false, margin: { l: 20, r: 20, t: 20, b: 20 } }}
            config={plotConfig}
            className="w-full"
          />
        </ChartCard>

        <ChartCard title="Top 15 States by Provider Count">
          <Plot
            data={[{
              type: "bar",
              x: byState.labels,
              y: byState.values,
              marker: {
                color: byState.values.map((_, i) => {
                  const t = i / Math.max(byState.values.length - 1, 1);
                  return `rgba(41, 98, 255, ${1 - t * 0.6})`;
                }),
              },
            } as PlotlyData]}
            layout={{ ...plotLayout, xaxis: { tickangle: -45 }, yaxis: { title: { text: "Count" } } }}
            config={plotConfig}
            className="w-full"
          />
        </ChartCard>

        <ChartCard title="Avg Billing Efficiency by Org Type">
          <Plot
            data={[{
              type: "bar",
              x: efficiencyByOrg.labels,
              y: efficiencyByOrg.values,
              marker: { color: orgColors },
              text: efficiencyByOrg.values.map((v) => `${v}%`),
              textposition: "outside" as const,
            } as PlotlyData]}
            layout={{
              ...plotLayout,
              yaxis: { title: { text: "Efficiency (%)" }, range: [0, 105] },
            }}
            config={plotConfig}
            className="w-full"
          />
        </ChartCard>
      </div>
    </div>
  );
}

function StatCard({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white px-5 py-4 shadow-sm">
      <p className="text-xs font-medium uppercase tracking-wider text-gray-400">{label}</p>
      <p className={`mt-1 text-2xl font-bold ${color}`}>{value}</p>
    </div>
  );
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
      <h3 className="mb-2 text-sm font-semibold text-gray-700">{title}</h3>
      {children}
    </div>
  );
}
