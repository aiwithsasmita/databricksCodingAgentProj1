"use client";

import { useState, Fragment } from "react";
import { Hospital } from "@/lib/types";
import { ORG_TYPE_HEX } from "@/lib/colors";

interface Props {
  data: Hospital[];
}

function Badge({ label, color }: { label: string; color: string }) {
  return (
    <span
      className="inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold text-white"
      style={{ backgroundColor: color }}
    >
      {label}
    </span>
  );
}

function DetailCard({ h }: { h: Hospital }) {
  return (
    <tr>
      <td colSpan={7} className="bg-uhc-orange-light px-6 py-4">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-uhc-gray-dark">
              NPI & Organization
            </h4>
            <p className="mt-1 text-sm">
              <span className="font-mono font-semibold text-uhc-navy">
                {h.npi}
              </span>
            </p>
            <p className="text-sm text-uhc-gray-dark">{h.orgType}</p>
            <p className="text-sm text-uhc-gray-dark">{h.specialty}</p>
          </div>
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-uhc-gray-dark">
              Service Address
            </h4>
            <p className="mt-1 text-sm">{h.serviceAddress.street}</p>
            <p className="text-sm">
              {h.serviceAddress.city}, {h.serviceAddress.state}{" "}
              {h.serviceAddress.zip}
            </p>
            <h4 className="mt-3 text-xs font-semibold uppercase tracking-wider text-uhc-gray-dark">
              Billing Address
            </h4>
            <p className="mt-1 text-sm">{h.billingAddress.street}</p>
            <p className="text-sm">
              {h.billingAddress.city}, {h.billingAddress.state}{" "}
              {h.billingAddress.zip}
            </p>
          </div>
          <div>
            <h4 className="text-xs font-semibold uppercase tracking-wider text-uhc-gray-dark">
              Billing Metrics
            </h4>
            <div className="mt-1 space-y-1 text-sm">
              <p>
                <span className="font-semibold">Efficiency:</span>{" "}
                {(h.billingEfficiency * 100).toFixed(0)}%
              </p>
              <p>
                <span className="font-semibold">Claims:</span>{" "}
                {h.claimCount.toLocaleString()}
              </p>
              <p>
                <span className="font-semibold">Total Payment:</span> $
                {h.totalPayment.toLocaleString()}
              </p>
              <p>
                <span className="font-semibold">Bed Count:</span>{" "}
                {h.bedCount.toLocaleString()}
              </p>
              <p>
                <span className="font-semibold">Pattern:</span>{" "}
                {h.billingPattern}
              </p>
            </div>
          </div>
        </div>
      </td>
    </tr>
  );
}

export default function HospitalTable({ data }: Props) {
  const [expandedNpi, setExpandedNpi] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const perPage = 10;
  const totalPages = Math.ceil(data.length / perPage);
  const slice = data.slice(page * perPage, (page + 1) * perPage);

  const toggle = (npi: string) =>
    setExpandedNpi((prev) => (prev === npi ? null : npi));

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b-2 border-uhc-navy bg-uhc-navy text-white">
            <th className="px-4 py-3 font-semibold">Name</th>
            <th className="px-4 py-3 font-semibold">Org Type</th>
            <th className="px-4 py-3 font-semibold">Specialty</th>
            <th className="px-4 py-3 font-semibold">State</th>
            <th className="px-4 py-3 font-semibold text-right">Payment</th>
            <th className="px-4 py-3 font-semibold text-right">Beds</th>
            <th className="px-4 py-3 font-semibold">Billing Pattern</th>
          </tr>
        </thead>
        <tbody>
          {slice.map((h, i) => (
            <Fragment key={h.npi}>
              <tr
                onClick={() => toggle(h.npi)}
                className={`cursor-pointer border-b border-uhc-gray transition hover:bg-uhc-orange-light ${
                  i % 2 === 0 ? "bg-white" : "bg-uhc-gray-light"
                } ${expandedNpi === h.npi ? "bg-uhc-orange-light" : ""}`}
              >
                <td className="px-4 py-3 font-medium text-uhc-navy">
                  {h.name}
                </td>
                <td className="px-4 py-3">
                  <Badge label={h.orgType} color={ORG_TYPE_HEX[h.orgType]} />
                </td>
                <td className="px-4 py-3">{h.specialty}</td>
                <td className="px-4 py-3">{h.serviceAddress.state}</td>
                <td className="px-4 py-3 text-right font-mono">
                  ${h.totalPayment.toLocaleString()}
                </td>
                <td className="px-4 py-3 text-right font-mono">
                  {h.bedCount}
                </td>
                <td className="px-4 py-3">{h.billingPattern}</td>
              </tr>
              {expandedNpi === h.npi && <DetailCard h={h} />}
            </Fragment>
          ))}
          {slice.length === 0 && (
            <tr>
              <td
                colSpan={7}
                className="px-4 py-12 text-center text-uhc-gray-dark"
              >
                No providers match the current filters.
              </td>
            </tr>
          )}
        </tbody>
      </table>

      {totalPages > 1 && (
        <div className="flex items-center justify-between border-t border-uhc-gray bg-white px-4 py-3">
          <p className="text-sm text-uhc-gray-dark">
            Showing {page * perPage + 1}–
            {Math.min((page + 1) * perPage, data.length)} of {data.length}
          </p>
          <div className="flex gap-1">
            <button
              onClick={() => setPage(Math.max(0, page - 1))}
              disabled={page === 0}
              className="rounded border border-uhc-gray px-3 py-1 text-sm font-medium transition hover:bg-uhc-gray-light disabled:opacity-40"
            >
              Prev
            </button>
            {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
              const p =
                totalPages <= 5
                  ? i
                  : Math.max(0, Math.min(page - 2, totalPages - 5)) + i;
              return (
                <button
                  key={p}
                  onClick={() => setPage(p)}
                  className={`rounded px-3 py-1 text-sm font-medium transition ${
                    p === page
                      ? "bg-uhc-navy text-white"
                      : "border border-uhc-gray hover:bg-uhc-gray-light"
                  }`}
                >
                  {p + 1}
                </button>
              );
            })}
            <button
              onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
              disabled={page >= totalPages - 1}
              className="rounded border border-uhc-gray px-3 py-1 text-sm font-medium transition hover:bg-uhc-gray-light disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
