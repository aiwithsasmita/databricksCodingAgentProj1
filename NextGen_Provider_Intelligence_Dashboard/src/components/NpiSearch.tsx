"use client";

import { useState, useMemo } from "react";
import { Hospital } from "@/lib/types";
import { hospitals } from "@/lib/dummy-data";
import { findSimilarProviders, SimilarProvider } from "@/lib/similarity";
import { ORG_TYPE_HEX } from "@/lib/colors";

interface Props {
  MapView: React.ComponentType<{
    data: Hospital[];
    metric: "totalPayment" | "bedCount";
    mapMode: "scatter";
    highlightNpi?: string;
  }>;
}

export default function NpiSearch({ MapView }: Props) {
  const [query, setQuery] = useState("");
  const [searchedNpi, setSearchedNpi] = useState<string | null>(null);

  const npiList = useMemo(
    () => hospitals.map((h) => ({ npi: h.npi, name: h.name })),
    []
  );

  const suggestions = useMemo(() => {
    if (query.length < 2) return [];
    const q = query.toLowerCase();
    return npiList
      .filter((h) => h.npi.includes(q) || h.name.toLowerCase().includes(q))
      .slice(0, 8);
  }, [query, npiList]);

  const target = useMemo(
    () => (searchedNpi ? hospitals.find((h) => h.npi === searchedNpi) ?? null : null),
    [searchedNpi]
  );

  const similarResults: SimilarProvider[] = useMemo(() => {
    if (!target) return [];
    return findSimilarProviders(target, hospitals, 10);
  }, [target]);

  const mapData = useMemo(() => {
    if (!target) return [];
    return [target, ...similarResults.map((s) => s.hospital)];
  }, [target, similarResults]);

  const handleSelect = (npi: string) => {
    setSearchedNpi(npi);
    setQuery("");
  };

  const handleSearch = () => {
    const match = hospitals.find(
      (h) => h.npi === query || h.name.toLowerCase() === query.toLowerCase()
    );
    if (match) {
      setSearchedNpi(match.npi);
      setQuery("");
    }
  };

  return (
    <div className="flex flex-col">
      {/* Search Bar */}
      <div className="border-b border-gray-200 bg-uhc-navy px-6 py-4">
        <div className="mx-auto max-w-2xl">
          <label className="mb-2 block text-xs font-semibold uppercase tracking-wider text-white/70">
            Search Provider by NPI or Name
          </label>
          <div className="relative">
            <div className="flex gap-2">
              <div className="relative flex-1">
                <svg
                  className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/40"
                  fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
                </svg>
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                  placeholder="e.g. 1000000000 or Metro General Hospital"
                  className="w-full rounded-lg border border-white/20 bg-white/10 py-2.5 pl-10 pr-4 text-sm text-white placeholder-white/40 outline-none transition focus:border-uhc-orange focus:ring-1 focus:ring-uhc-orange"
                />
              </div>
              <button
                onClick={handleSearch}
                className="rounded-lg bg-uhc-orange px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-uhc-orange/90"
              >
                Search
              </button>
              {searchedNpi && (
                <button
                  onClick={() => { setSearchedNpi(null); setQuery(""); }}
                  className="rounded-lg border border-white/20 px-4 py-2.5 text-sm font-medium text-white/70 transition hover:bg-white/10"
                >
                  Clear
                </button>
              )}
            </div>

            {suggestions.length > 0 && !searchedNpi && (
              <div className="absolute top-full left-0 z-50 mt-1 w-full rounded-lg border border-gray-200 bg-white shadow-xl">
                {suggestions.map((s) => (
                  <button
                    key={s.npi}
                    onClick={() => handleSelect(s.npi)}
                    className="flex w-full items-center gap-3 px-4 py-2.5 text-left text-sm transition hover:bg-gray-50"
                  >
                    <span className="font-mono text-xs text-gray-400">{s.npi}</span>
                    <span className="font-medium text-gray-700">{s.name}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {!target ? (
        <div className="flex flex-1 flex-col items-center justify-center bg-gray-50 py-24">
          <svg className="mb-4 h-16 w-16 text-gray-300" fill="none" viewBox="0 0 24 24" strokeWidth={1} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
          </svg>
          <p className="text-lg font-semibold text-gray-400">Enter an NPI or provider name to find similar providers</p>
          <p className="mt-1 text-sm text-gray-400">
            Try: <button onClick={() => handleSelect("1000000000")} className="text-blue-500 underline">1000000000</button>
            {" or "}
            <button onClick={() => handleSelect("1000888888")} className="text-blue-500 underline">1000888888</button>
          </p>
        </div>
      ) : (
        <>
          {/* Target Provider Card */}
          <div className="border-b border-gray-200 bg-white px-6 py-4">
            <div className="flex items-start gap-6">
              <div className="flex-1">
                <div className="flex items-center gap-3">
                  <span className="rounded bg-uhc-navy px-2 py-0.5 text-xs font-bold text-white">TARGET</span>
                  <h2 className="text-lg font-bold text-gray-800">{target.name}</h2>
                </div>
                <div className="mt-2 flex flex-wrap gap-x-6 gap-y-1 text-sm text-gray-500">
                  <span><span className="font-semibold text-gray-700">NPI:</span> {target.npi}</span>
                  <span><span className="font-semibold text-gray-700">Type:</span> {target.orgType}</span>
                  <span><span className="font-semibold text-gray-700">Specialty:</span> {target.specialty}</span>
                  <span><span className="font-semibold text-gray-700">State:</span> {target.serviceAddress.state}</span>
                  <span><span className="font-semibold text-gray-700">Payment:</span> ${target.totalPayment.toLocaleString()}</span>
                  <span><span className="font-semibold text-gray-700">Claims:</span> {target.claimCount.toLocaleString()}</span>
                  <span><span className="font-semibold text-gray-700">Pattern:</span> {target.billingPattern}</span>
                  <span><span className="font-semibold text-gray-700">Efficiency:</span> {(target.billingEfficiency * 100).toFixed(0)}%</span>
                </div>
              </div>
              <div className="text-right">
                <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">Similar Found</p>
                <p className="text-3xl font-bold text-uhc-orange">{similarResults.length}</p>
              </div>
            </div>
          </div>

          {/* Map with target + similar */}
          <MapView
            data={mapData}
            metric="totalPayment"
            mapMode="scatter"
            highlightNpi={target.npi}
          />

          {/* Similar Providers Table */}
          <div className="bg-white">
            <div className="border-b border-gray-200 px-6 py-3">
              <h3 className="text-sm font-bold text-gray-700">
                Top {similarResults.length} Similar Providers
              </h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b-2 border-uhc-navy bg-uhc-navy text-white">
                    <th className="px-4 py-3 font-semibold">#</th>
                    <th className="px-4 py-3 font-semibold">Score</th>
                    <th className="px-4 py-3 font-semibold">Name</th>
                    <th className="px-4 py-3 font-semibold">NPI</th>
                    <th className="px-4 py-3 font-semibold">Org Type</th>
                    <th className="px-4 py-3 font-semibold">Specialty</th>
                    <th className="px-4 py-3 font-semibold">State</th>
                    <th className="px-4 py-3 font-semibold text-right">Payment</th>
                    <th className="px-4 py-3 font-semibold">Pattern</th>
                    <th className="px-4 py-3 font-semibold">Why Similar</th>
                  </tr>
                </thead>
                <tbody>
                  {similarResults.map((r, i) => (
                    <tr
                      key={r.hospital.npi}
                      className={`border-b border-gray-100 transition hover:bg-blue-50 ${
                        i % 2 === 0 ? "bg-white" : "bg-gray-50"
                      }`}
                    >
                      <td className="px-4 py-3 font-mono text-xs text-gray-400">{i + 1}</td>
                      <td className="px-4 py-3">
                        <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-bold text-white ${
                          r.score >= 80 ? "bg-green-500" :
                          r.score >= 60 ? "bg-yellow-500" :
                          r.score >= 40 ? "bg-orange-500" :
                          "bg-gray-400"
                        }`}>
                          {r.score}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-medium text-gray-800">{r.hospital.name}</td>
                      <td className="px-4 py-3 font-mono text-xs text-gray-500">{r.hospital.npi}</td>
                      <td className="px-4 py-3">
                        <span
                          className="inline-block rounded-full px-2 py-0.5 text-xs font-semibold text-white"
                          style={{ backgroundColor: ORG_TYPE_HEX[r.hospital.orgType] }}
                        >
                          {r.hospital.orgType}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-600">{r.hospital.specialty}</td>
                      <td className="px-4 py-3 text-gray-600">{r.hospital.serviceAddress.state}</td>
                      <td className="px-4 py-3 text-right font-mono text-gray-600">
                        ${r.hospital.totalPayment.toLocaleString()}
                      </td>
                      <td className="px-4 py-3 text-gray-600">{r.hospital.billingPattern}</td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap gap-1">
                          {r.reasons.slice(0, 3).map((reason) => (
                            <span
                              key={reason}
                              className="rounded bg-blue-100 px-1.5 py-0.5 text-[10px] font-medium text-blue-700"
                            >
                              {reason}
                            </span>
                          ))}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
