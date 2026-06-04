"use client";

import type { Layer } from "@/lib/architecture";
import NodeCard from "./NodeCard";

interface LayerBandProps {
  layer: Layer;
  /** Base stagger index so cards across bands cascade in order. */
  baseDelay: number;
  selectedId: string | null;
  hoveredId: string | null;
  /** Ids to spotlight (hovered node + its relations). Empty = nothing hovered. */
  spotlightIds: Set<string>;
  onSelect: (id: string) => void;
  onHover: (id: string | null) => void;
}

export default function LayerBand({
  layer,
  baseDelay,
  selectedId,
  hoveredId,
  spotlightIds,
  onSelect,
  onHover,
}: LayerBandProps) {
  const isFrontend = layer.zone === "frontend";
  const accent = isFrontend ? "orange" : "blue";
  const hovering = hoveredId !== null;

  return (
    <section
      className={`relative rounded-2xl border p-4 sm:p-5 ${
        isFrontend
          ? "border-optum-orange/30 bg-gradient-to-br from-optum-orange/5 to-white"
          : "border-uhc-blue-soft bg-gradient-to-br from-uhc-blue-soft/40 to-white"
      }`}
    >
      <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2.5">
          <span
            className={`h-7 w-1.5 rounded-full ${isFrontend ? "bg-optum-orange" : "bg-uhc-blue-bright"}`}
          />
          <div>
            <h2 className="text-[15px] font-bold tracking-tight text-uhc-blue">{layer.title}</h2>
            <span
              className={`text-[10px] font-semibold uppercase tracking-[0.16em] ${
                isFrontend ? "text-optum-orange" : "text-uhc-blue-bright"
              }`}
            >
              {layer.zone}
            </span>
          </div>
        </div>
        <p className="max-w-xl text-[12px] leading-snug text-gray-500">{layer.blurb}</p>
      </div>

      <div className="flex flex-wrap gap-3">
        {layer.nodes.map((node, i) => (
          <NodeCard
            key={node.id}
            node={node}
            accent={accent}
            delay={baseDelay + i * 45}
            selected={selectedId === node.id}
            spotlight={hovering && spotlightIds.has(node.id)}
            dimmed={hovering && !spotlightIds.has(node.id)}
            onSelect={onSelect}
            onHover={onHover}
          />
        ))}
      </div>
    </section>
  );
}
