"use client";

import { STATUS_STYLE, type ArchNode } from "@/lib/architecture";
import Icon from "./icons";

type Accent = "blue" | "orange";

interface NodeCardProps {
  node: ArchNode;
  accent: Accent;
  /** Entrance stagger delay in ms. */
  delay: number;
  selected: boolean;
  /** Dim when another node is hovered and this one is unrelated. */
  dimmed: boolean;
  /** Spotlight when it's the hovered node or related to it. */
  spotlight: boolean;
  onSelect: (id: string) => void;
  onHover: (id: string | null) => void;
}

export default function NodeCard({
  node,
  accent,
  delay,
  selected,
  dimmed,
  spotlight,
  onSelect,
  onHover,
}: NodeCardProps) {
  const iconWrap =
    accent === "orange"
      ? "bg-optum-orange/10 text-optum-orange"
      : "bg-uhc-blue-soft text-uhc-blue-bright";

  return (
    <button
      type="button"
      onClick={() => onSelect(node.id)}
      onMouseEnter={() => onHover(node.id)}
      onMouseLeave={() => onHover(null)}
      onFocus={() => onHover(node.id)}
      onBlur={() => onHover(null)}
      style={{ "--d": `${delay}ms` } as React.CSSProperties}
      className={`arch-fade-up group relative flex w-[170px] flex-col gap-2 rounded-xl border bg-white p-3 text-left shadow-card transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg focus:outline-none focus-visible:ring-2 focus-visible:ring-uhc-blue ${
        selected
          ? "border-uhc-blue ring-2 ring-uhc-blue arch-glow"
          : spotlight
          ? "border-uhc-blue-bright ring-1 ring-uhc-blue-bright"
          : "border-uhc-blue-soft hover:ring-1 hover:ring-uhc-blue-bright"
      } ${dimmed ? "opacity-40" : "opacity-100"}`}
    >
      <div className="flex items-start justify-between">
        <span className={`grid h-9 w-9 place-items-center rounded-lg ${iconWrap}`}>
          <Icon name={node.icon} size={18} />
        </span>
        <span
          className={`mt-1 h-2.5 w-2.5 rounded-full ${STATUS_STYLE[node.status].dot}`}
          title={node.status}
        />
      </div>
      <div>
        <div className="text-[13px] font-semibold leading-tight text-uhc-blue">{node.label}</div>
        <div className="mt-0.5 text-[11px] leading-snug text-gray-500">{node.tagline}</div>
      </div>
      {node.hint && (
        <span className="mt-auto inline-flex w-fit items-center gap-1 rounded-full bg-uhc-blue-soft px-2 py-0.5 text-[10px] font-semibold text-uhc-blue-bright">
          ▸ {node.hint}
        </span>
      )}
    </button>
  );
}
