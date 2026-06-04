"use client";

import { useMemo, useState } from "react";
import { LAYERS, NODE_BY_ID } from "@/lib/architecture";
import LayerBand from "./LayerBand";
import LayerConnector from "./LayerConnector";
import DetailPanel from "./DetailPanel";
import Legend from "./Legend";

/* Build a bidirectional adjacency map so hovering a node spotlights both the
 * nodes it points to and the nodes that point to it. */
function buildAdjacency(): Record<string, Set<string>> {
  const adj: Record<string, Set<string>> = {};
  const add = (a: string, b: string) => {
    (adj[a] ??= new Set()).add(b);
    (adj[b] ??= new Set()).add(a);
  };
  for (const layer of LAYERS) {
    for (const node of layer.nodes) {
      adj[node.id] ??= new Set();
      for (const rel of node.relatedIds ?? []) add(node.id, rel);
    }
  }
  return adj;
}

function shortName(title: string) {
  return title.replace(/ Layer$/, "").replace(/ \/ Signal$/, "");
}

export default function ArchitectureDiagram() {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  const adjacency = useMemo(buildAdjacency, []);

  // Render bands top → bottom (Observation at top, Data at bottom).
  const ordered = useMemo(() => [...LAYERS].reverse(), []);

  const spotlightIds = useMemo(() => {
    if (!hoveredId) return new Set<string>();
    const set = new Set<string>([hoveredId]);
    adjacency[hoveredId]?.forEach((id) => set.add(id));
    return set;
  }, [hoveredId, adjacency]);

  const selectedNode = selectedId ? NODE_BY_ID[selectedId] ?? null : null;

  return (
    <div className="relative">
      {/* Hero */}
      <div className="mb-7 text-center">
        <span className="inline-flex items-center gap-1.5 rounded-full bg-uhc-blue-soft px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-uhc-blue-bright">
          Platform Blueprint
        </span>
        <h1 className="mt-3 text-2xl font-bold tracking-tight text-uhc-blue sm:text-3xl">
          Agentic Intelligence Architecture
        </h1>
        <p className="mx-auto mt-2 max-w-2xl text-[13px] leading-relaxed text-gray-500">
          Five layers, bottom to top — data rises into context, memory and a fleet of specialist
          agents; signals surface to the frontend and feed back as improvement. Click any node for
          details.
        </p>
        <div className="mt-4 flex justify-center">
          <Legend />
        </div>
      </div>

      {/* Diagram with decorative side rails (lg+) */}
      <div className="grid gap-3 lg:grid-cols-[40px_minmax(0,1fr)_40px]">
        <Rail side="left" />

        <div>
          {ordered.map((layer, i) => (
            <div key={layer.id}>
              <LayerBand
                layer={layer}
                baseDelay={i * 70}
                selectedId={selectedId}
                hoveredId={hoveredId}
                spotlightIds={spotlightIds}
                onSelect={setSelectedId}
                onHover={setHoveredId}
              />
              {i < ordered.length - 1 && (
                <LayerConnector label={`feeds ${shortName(ordered[i].title)}`} feedback={i === 0} />
              )}
            </div>
          ))}
        </div>

        <Rail side="right" />
      </div>

      <DetailPanel node={selectedNode} onClose={() => setSelectedId(null)} onSelect={setSelectedId} />
    </div>
  );
}

/* Thin vertical rail labelling the overall flow direction. Decorative; lg+ only. */
function Rail({ side }: { side: "left" | "right" }) {
  const left = side === "left";
  return (
    <div className="relative hidden lg:block">
      <div
        className={`absolute inset-y-2 left-1/2 w-0.5 -translate-x-1/2 rounded-full ${
          left
            ? "bg-gradient-to-t from-uhc-blue via-uhc-blue-bright to-uhc-blue-bright"
            : "bg-gradient-to-b from-optum-orange/70 to-optum-orange/20"
        }`}
      />
      <div className="sticky top-24 flex justify-center">
        <span
          className={`whitespace-nowrap text-[10px] font-bold uppercase tracking-[0.22em] ${
            left ? "text-uhc-blue-bright" : "text-optum-orange"
          }`}
          style={{ writingMode: "vertical-rl", transform: left ? "rotate(180deg)" : "none" }}
        >
          {left ? "Data flows up ↑" : "↺ Feedback loop"}
        </span>
      </div>
    </div>
  );
}
