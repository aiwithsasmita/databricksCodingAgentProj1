"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  BANDS,
  BUS_GAPS,
  BUS_X,
  EDGES,
  NODE_BY_ID,
  NODES,
  PLAY_SEQUENCE,
  TECH_STACK,
  VIEW,
  type EdgeKind,
  type FlowEdge,
  type FlowNode,
} from "@/lib/flow";
import { STATUS_STYLE } from "@/lib/architecture";
import Icon from "./icons";
import TechLogo from "./TechLogo";
import DetailPanel from "./DetailPanel";

/* ── Edge styling ───────────────────────────────────────────────────────── */
// Brightened for a dark canvas.
const EDGE_STYLE: Record<EdgeKind, { color: string; width: number; rev?: boolean }> = {
  route: { color: "#4FA8E8", width: 3 },
  delegate: { color: "#4FA8E8", width: 3 },
  subagent: { color: "#6CC6F2", width: 2.6 },
  merge: { color: "#8298C2", width: 2.4 },
  signal: { color: "#67B5FF", width: 3.6 },
  feedback: { color: "#FF7A45", width: 3, rev: true },
  data: { color: "#92A8CC", width: 2.2 },
};
const EDGE_KINDS: EdgeKind[] = ["route", "delegate", "subagent", "merge", "signal", "feedback", "data"];
const edgeId = (e: FlowEdge) => `${e.from}-${e.to}`;

/* ── Geometry ───────────────────────────────────────────────────────────── */
type Pt = { x: number; y: number };
type Side = "left" | "right" | "top" | "bottom";
const FEEDBACK_LANE = 708;

function anchor(n: FlowNode, side: Side): Pt {
  switch (side) {
    case "left": return { x: n.x, y: n.y + n.h / 2 };
    case "right": return { x: n.x + n.w, y: n.y + n.h / 2 };
    case "top": return { x: n.x + n.w / 2, y: n.y };
    case "bottom": return { x: n.x + n.w / 2, y: n.y + n.h };
  }
}
function off(p: Pt, side: Side, d: number): Pt {
  switch (side) {
    case "left": return { x: p.x - d, y: p.y };
    case "right": return { x: p.x + d, y: p.y };
    case "top": return { x: p.x, y: p.y - d };
    case "bottom": return { x: p.x, y: p.y + d };
  }
}
function sidesFor(e: FlowEdge, f: FlowNode, t: FlowNode): { fs: Side; ts: Side } {
  const dx = t.x + t.w / 2 - (f.x + f.w / 2);
  return { fs: e.fromSide ?? (dx >= 0 ? "right" : "left"), ts: e.toSide ?? (dx >= 0 ? "left" : "right") };
}
function geom(e: FlowEdge): { d: string; mid: Pt } {
  const f = NODE_BY_ID[e.from];
  const t = NODE_BY_ID[e.to];
  if (e.kind === "feedback") {
    const s = { x: f.x + f.w / 2, y: f.y + f.h };
    const en = { x: t.x + t.w / 2, y: t.y + t.h };
    return { d: `M ${s.x} ${s.y} C ${s.x} ${FEEDBACK_LANE}, ${en.x} ${FEEDBACK_LANE}, ${en.x} ${en.y}`, mid: { x: (s.x + en.x) / 2, y: 644 } };
  }
  const { fs, ts } = sidesFor(e, f, t);
  const s = anchor(f, fs);
  const en = anchor(t, ts);
  const kf = Math.max(34, (fs === "left" || fs === "right" ? Math.abs(en.x - s.x) : Math.abs(en.y - s.y)) * 0.5);
  const kt = Math.max(34, (ts === "left" || ts === "right" ? Math.abs(en.x - s.x) : Math.abs(en.y - s.y)) * 0.5);
  const c1 = off(s, fs, kf);
  const c2 = off(en, ts, kt);
  return { d: `M ${s.x} ${s.y} C ${c1.x} ${c1.y}, ${c2.x} ${c2.y}, ${en.x} ${en.y}`, mid: { x: (s.x + en.x) / 2, y: (s.y + en.y) / 2 } };
}

/* ── Component ──────────────────────────────────────────────────────────── */
export default function FlowCanvas() {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [playing, setPlaying] = useState(false);
  const [playStep, setPlayStep] = useState(0);
  const [motionOk, setMotionOk] = useState(true);

  useEffect(() => {
    const m = window.matchMedia("(prefers-reduced-motion: reduce)");
    const apply = () => setMotionOk(!m.matches);
    apply();
    m.addEventListener?.("change", apply);
    return () => m.removeEventListener?.("change", apply);
  }, []);

  useEffect(() => {
    if (!playing) return;
    if (playStep >= PLAY_SEQUENCE.length) {
      const id = setTimeout(() => {
        setPlaying(false);
        setPlayStep(0);
      }, 1100);
      return () => clearTimeout(id);
    }
    const id = setTimeout(() => setPlayStep((s) => s + 1), 780);
    return () => clearTimeout(id);
  }, [playing, playStep]);

  const neighbors = useMemo(() => {
    const m: Record<string, Set<string>> = {};
    for (const e of EDGES) {
      (m[e.from] ??= new Set()).add(e.to);
      (m[e.to] ??= new Set()).add(e.from);
    }
    return m;
  }, []);

  const litSet = useMemo(() => {
    if (!playing) return null;
    const s = new Set<string>();
    for (let i = 0; i < playStep && i < PLAY_SEQUENCE.length; i++) PLAY_SEQUENCE[i].forEach((id) => s.add(id));
    return s;
  }, [playing, playStep]);

  // Stable reference (feeds activeEdges' deps). `<= length` is intentional:
  // the final step lights the Observation group + feedback edge.
  const activeGroup = useMemo(
    () => (playing && playStep > 0 && playStep <= PLAY_SEQUENCE.length ? PLAY_SEQUENCE[playStep - 1] : []),
    [playing, playStep]
  );
  const activeEdges = useMemo(() => {
    const s = new Set<string>();
    if (!activeGroup.length) return s;
    for (const e of EDGES) if (activeGroup.includes(e.to)) s.add(edgeId(e));
    if (activeGroup.includes("observation")) for (const e of EDGES) if (e.kind === "feedback") s.add(edgeId(e));
    return s;
  }, [activeGroup]);

  const hoverEdges = useMemo(() => {
    const s = new Set<string>();
    if (!hoveredId || playing) return s;
    for (const e of EDGES) if (e.from === hoveredId || e.to === hoveredId) s.add(edgeId(e));
    return s;
  }, [hoveredId, playing]);

  const start = () => {
    setSelectedId(null);
    setHoveredId(null);
    setPlayStep(0);
    setPlaying(true);
  };
  const stop = () => {
    setPlaying(false);
    setPlayStep(0);
  };
  const handleClose = useCallback(() => setSelectedId(null), []);

  const selectedNode = selectedId
    ? { ...NODE_BY_ID[selectedId], relatedIds: [...(neighbors[selectedId] ?? [])] }
    : null;

  const nodeStateFor = (id: string): "lit" | "dim" | "spot" | "normal" => {
    if (playing && litSet) return litSet.has(id) ? "lit" : "dim";
    if (hoveredId) return id === hoveredId || neighbors[hoveredId]?.has(id) ? "spot" : "dim";
    return "normal";
  };
  const isDimEdge = (id: string) =>
    (!!hoveredId && !playing && !hoverEdges.has(id)) || (playing && !activeEdges.has(id));

  return (
    <div className="relative">
      {/* Slim toolbar (no hero panel) */}
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <button
            type="button"
            onClick={() => (playing ? stop() : start())}
            aria-label={playing ? "Stop flow animation" : "Play flow animation"}
            className={`inline-flex items-center gap-2 rounded-full px-4 py-2 text-[13px] font-semibold text-white shadow-sm transition-colors ${
              playing ? "bg-optum-orange hover:bg-optum-orange-dark" : "bg-uhc-blue hover:bg-uhc-blue-bright"
            }`}
          >
            {playing ? <StopGlyph /> : <PlayGlyph />}
            {playing ? "Stop" : "Play the flow"}
          </button>
          <span className="hidden text-[12px] text-gray-500 md:inline">
            Human → Supervisor → agents → report → signal · data rises from the layers below.
          </span>
        </div>
        <Legend />
      </div>

      {/* Scene */}
      <div className="overflow-x-auto rounded-2xl border border-[#1b3566] bg-[#07173a] shadow-card">
        <svg
          viewBox={`0 0 ${VIEW.w} ${VIEW.h}`}
          className="h-auto"
          style={{ width: "100%", minWidth: 1080, display: "block" }}
          role="img"
          aria-label="Agentic runtime flow with data, context and memory layers"
        >
          <defs>
            {EDGE_KINDS.map((k) => (
              <marker
                key={k}
                id={`arw-${k}`}
                viewBox="0 0 10 10"
                refX="8"
                refY="5"
                markerWidth="13"
                markerHeight="13"
                markerUnits="userSpaceOnUse"
                orient="auto-start-reverse"
              >
                <path d="M0 0 L10 5 L0 10 z" fill={EDGE_STYLE[k].color} />
              </marker>
            ))}
            <linearGradient id="obsGrad" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0" stopColor="#0e2a5e" />
              <stop offset="1" stopColor="#0b2350" />
            </linearGradient>
            <linearGradient id="govGrad" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0" stopColor="#0a1c3e" />
              <stop offset="1" stopColor="#102449" />
            </linearGradient>
            <linearGradient id="bgGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stopColor="#0a1f49" />
              <stop offset="1" stopColor="#061230" />
            </linearGradient>
          </defs>

          <rect x={0} y={0} width={VIEW.w} height={VIEW.h} fill="url(#bgGrad)" />

          {/* Backdrop rails + layer bands (non-interactive) */}
          <g style={{ pointerEvents: "none" }}>
            {/* Observability rail */}
            <rect x={40} y={20} width={1400} height={54} rx={14} fill="url(#obsGrad)" stroke="#2f54a0" />
            <foreignObject x={56} y={26} width={1372} height={42}>
              <div className="flex h-full items-center gap-3">
                <TechLogo logo="mlflow" size={26} />
                <span className="text-[14px] font-bold text-white">Observability · MLflow</span>
                <span className="text-[12px] text-[#86c6f4]">traces, evals &amp; metrics on every agent step</span>
                <span className="ml-auto rounded-full bg-white/10 px-2.5 py-0.5 text-[11px] font-semibold text-[#86c6f4] ring-1 ring-[#2f54a0]">
                  every run traced
                </span>
              </div>
            </foreignObject>
            {[348, 1178, 1382].map((cx, i) => (
              <line key={i} x1={cx} y1={74} x2={cx} y2={i === 0 ? 300 : 323} stroke="#2b8fe0" strokeWidth={1.4} strokeDasharray="2 7" strokeOpacity={0.35} />
            ))}

            {/* Layer bands */}
            {BANDS.map((b) => (
              <g key={b.id}>
                <rect x={40} y={b.y} width={1400} height={b.h} rx={16} fill="rgba(255,255,255,0.035)" stroke="rgba(120,160,220,0.16)" />
                <foreignObject x={48} y={b.y} width={132} height={b.h}>
                  <div className="flex h-full flex-col justify-center pl-1">
                    <span className="text-[13px] font-bold leading-tight text-[#dce8fa]">{b.title}</span>
                    <span className="text-[9.5px] font-semibold uppercase tracking-[0.14em] text-[#86c6f4]">{b.zone}</span>
                  </div>
                </foreignObject>
              </g>
            ))}

            {/* Data-flows-up bus arrows between bands and into the agents */}
            {BUS_GAPS.map(([y1, y2], gi) =>
              BUS_X.map((cx, xi) => (
                <line
                  key={`${gi}-${xi}`}
                  x1={cx}
                  y1={y1}
                  x2={cx}
                  y2={y2}
                  stroke="#92A8CC"
                  strokeWidth={2.6}
                  strokeDasharray="5 5"
                  markerEnd="url(#arw-data)"
                  className={motionOk ? "arch-edge-flow-rev" : ""}
                />
              ))
            )}

            {/* Governance rail */}
            <rect x={40} y={1124} width={1400} height={48} rx={14} fill="url(#govGrad)" stroke="rgba(120,160,220,0.2)" />
            <foreignObject x={56} y={1130} width={1372} height={36}>
              <div className="flex h-full items-center gap-3">
                <TechLogo logo="databricks" size={24} />
                <span className="text-[13px] font-bold text-white">Data Governance · Databricks Unity Catalog</span>
                <span className="text-[12px] text-white/70">lineage · access control · audit across every layer</span>
              </div>
            </foreignObject>
          </g>

          {/* Edges */}
          <g style={{ pointerEvents: "none" }}>
            {EDGES.map((e) => {
              const id = edgeId(e);
              const st = EDGE_STYLE[e.kind];
              const g = geom(e);
              const hot = activeEdges.has(id) || hoverEdges.has(id);
              const dim = isDimEdge(id);
              const flowCls = motionOk ? (st.rev ? "arch-edge-flow-rev" : "arch-edge-flow") : "";
              return (
                <g key={id} opacity={dim ? 0.14 : 1}>
                  {hot && <path d={g.d} fill="none" stroke={st.color} strokeWidth={st.width + 9} strokeOpacity={0.16} strokeLinecap="round" />}
                  <path d={g.d} fill="none" stroke={st.color} strokeWidth={st.width} strokeOpacity={0.22} strokeLinecap="round" />
                  <path id={`p-${id}`} d={g.d} fill="none" stroke={st.color} strokeWidth={hot ? st.width + 1.3 : st.width} strokeLinecap="round" markerEnd={`url(#arw-${e.kind})`} className={flowCls} />
                  {motionOk && (
                    <circle r={hot ? 4.2 : 2.6} fill={st.color} opacity={hot ? 1 : 0.65}>
                      <animateMotion dur={`${st.rev ? 2.8 : 1.9}s`} repeatCount="indefinite" keyPoints={st.rev ? "1;0" : "0;1"} keyTimes="0;1" calcMode="linear">
                        <mpath href={`#p-${id}`} />
                      </animateMotion>
                    </circle>
                  )}
                </g>
              );
            })}
          </g>

          {/* Nodes */}
          <g>
            {NODES.map((n) => (
              <foreignObject key={n.id} x={n.x} y={n.y} width={n.w} height={n.h} overflow="visible">
                <div className="h-full w-full">
                  <NodeCard
                    node={n}
                    state={nodeStateFor(n.id)}
                    selected={selectedId === n.id}
                    onSelect={setSelectedId}
                    onHover={playing ? noop : setHoveredId}
                  />
                </div>
              </foreignObject>
            ))}
          </g>

          {/* Edge labels (top layer, never hidden behind nodes) */}
          <g style={{ pointerEvents: "none" }}>
            {EDGES.filter((e) => e.label).map((e) => {
              const id = edgeId(e);
              if (isDimEdge(id)) return null;
              const g = geom(e);
              return <EdgeLabel key={id} x={g.mid.x + (e.labelDx ?? 0)} y={g.mid.y + (e.labelDy ?? 0)} text={e.label as string} color={EDGE_STYLE[e.kind].color} />;
            })}
          </g>
        </svg>
      </div>

      {/* Tech stack strip */}
      <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-2 rounded-xl border border-[#1b3566] bg-[#0c1f47] px-4 py-3 shadow-sm">
        <span className="text-[11px] font-bold uppercase tracking-[0.14em] text-[#7f99c4]">Stack</span>
        {TECH_STACK.map((t) => (
          <span key={t.label} className="inline-flex items-center gap-1.5 text-[12px] font-medium text-[#cfe0f5]">
            <TechLogo logo={t.logo} size={20} rounded="rounded-md" />
            {t.label}
          </span>
        ))}
      </div>

      <DetailPanel node={selectedNode} onClose={handleClose} onSelect={setSelectedId} nodeById={NODE_BY_ID} />
    </div>
  );
}

const noop = () => {};

/* ── Edge label chip ────────────────────────────────────────────────────── */
function EdgeLabel({ x, y, text, color }: { x: number; y: number; text: string; color: string }) {
  const w = text.length * 6.2 + 16;
  return (
    <g transform={`translate(${x - w / 2}, ${y - 10})`}>
      <rect width={w} height={20} rx={10} fill="#0c2150" stroke={color} strokeOpacity={0.6} />
      <text x={w / 2} y={14} textAnchor="middle" fontSize={11.5} fontWeight={700} fill="#d7e6fb">
        {text}
      </text>
    </g>
  );
}

/* ── Node card (HTML inside foreignObject) ─────────────────────────────── */
function NodeCard({
  node,
  state,
  selected,
  onSelect,
  onHover,
}: {
  node: FlowNode;
  state: "lit" | "dim" | "spot" | "normal";
  selected: boolean;
  onSelect: (id: string) => void;
  onHover: (id: string | null) => void;
}) {
  const isFrontend = node.kind === "observation" || node.kind === "human";
  const compact = node.kind === "data" || node.kind === "context" || node.kind === "memory";
  const horizontal = node.kind === "agent";

  const ring = selected
    ? "ring-2 ring-[#67B5FF]"
    : state === "lit"
    ? "ring-2 ring-optum-orange arch-node-lit"
    : state === "spot"
    ? isFrontend
      ? "ring-1 ring-optum-orange/70"
      : "ring-1 ring-[#4FA8E8]/70"
    : "ring-1 ring-transparent";

  const cardBg =
    node.kind === "supervisor"
      ? "bg-[#13327c] border-[#3f63b8]"
      : isFrontend
      ? "bg-[#172a52] border-optum-orange/45"
      : compact
      ? "bg-[#0d2350] border-[#21407e]"
      : "bg-[#102a5c] border-[#284c90]";

  const iconWrapCls = isFrontend ? "bg-optum-orange/15 text-optum-orange" : "bg-[#4FA8E8]/15 text-[#86c6f4]";
  const chipCls = isFrontend ? "bg-optum-orange/15 text-[#ffb494]" : "bg-[#4FA8E8]/14 text-[#9fcdf3]";

  const base = `flex h-full w-full rounded-xl border text-left shadow-lg transition-all duration-200 hover:-translate-y-0.5 ${ring} ${
    state === "dim" ? "opacity-40" : "opacity-100"
  } ${cardBg}`;

  // Agents (the agentic layer) use a horizontal layout with a large icon.
  if (horizontal) {
    return (
      <button
        type="button"
        onClick={() => onSelect(node.id)}
        onMouseEnter={() => onHover(node.id)}
        onMouseLeave={() => onHover(null)}
        className={`${base} items-center gap-3 p-2.5`}
      >
        <span className={`grid h-11 w-11 shrink-0 place-items-center rounded-xl ${iconWrapCls}`}>
          <Icon name={node.icon} size={26} />
        </span>
        <span className="min-w-0 flex-1">
          <div className="text-[14px] font-bold leading-tight text-[#e9effb]">{node.label}</div>
          <div className="text-[11px] leading-snug text-[#9bb3d8]">{node.sublabel}</div>
        </span>
        {node.status && <span className={`h-2.5 w-2.5 shrink-0 rounded-full ${STATUS_STYLE[node.status].dot}`} title={node.status} />}
      </button>
    );
  }

  return (
    <button
      type="button"
      onClick={() => onSelect(node.id)}
      onMouseEnter={() => onHover(node.id)}
      onMouseLeave={() => onHover(null)}
      className={`${base} flex-col ${compact ? "p-2" : "p-2.5"}`}
    >
      <div className="flex items-start justify-between gap-1">
        <span className="flex items-center gap-1.5">
          {node.logo ? (
            <TechLogo logo={node.logo} size={node.kind === "supervisor" ? 28 : 24} />
          ) : (
            <span className={`grid h-8 w-8 place-items-center rounded-md ${iconWrapCls}`}>
              <Icon name={node.icon} size={compact ? 16 : 18} />
            </span>
          )}
          {node.kind === "supervisor" && (
            <span className="rounded bg-[#4FA8E8] px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wide text-[#06173a]">DeepAgent</span>
          )}
        </span>
        {node.status && <span className={`mt-0.5 h-2.5 w-2.5 shrink-0 rounded-full ${STATUS_STYLE[node.status].dot}`} title={node.status} />}
      </div>

      <div className={compact ? "mt-1 leading-tight" : "mt-1.5 leading-tight"}>
        <div className={`font-bold text-[#e9effb] ${node.kind === "supervisor" ? "text-[15px]" : compact ? "text-[12px]" : "text-[13.5px]"}`}>{node.label}</div>
        <div className={`text-[#9bb3d8] ${compact ? "text-[10px]" : "text-[11px]"}`}>{node.sublabel}</div>
      </div>

      {node.chips && node.chips.length > 0 && (
        <div className="mt-auto flex flex-wrap gap-1 pt-1.5">
          {node.chips.map((c) => (
            <span key={c} className={`rounded px-1.5 py-0.5 text-[9.5px] font-semibold ${chipCls}`}>
              {c}
            </span>
          ))}
        </div>
      )}
    </button>
  );
}

/* ── Legend ─────────────────────────────────────────────────────────────── */
function Legend() {
  const edges: { kind: EdgeKind; label: string }[] = [
    { kind: "delegate", label: "delegate" },
    { kind: "subagent", label: "sub-agent" },
    { kind: "signal", label: "signal" },
    { kind: "feedback", label: "feedback" },
    { kind: "data", label: "data ↑" },
  ];
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-[11px] text-gray-500">
      <div className="flex items-center gap-3">
        {edges.map((e) => (
          <span key={e.kind} className="flex items-center gap-1.5">
            <span className="inline-block h-0.5 w-5 rounded" style={{ background: EDGE_STYLE[e.kind].color }} />
            {e.label}
          </span>
        ))}
      </div>
      <span className="hidden h-4 w-px bg-uhc-blue-soft sm:block" />
      <div className="flex items-center gap-3">
        {(["live", "stage1", "planned"] as const).map((s) => (
          <span key={s} className="flex items-center gap-1.5">
            <span className={`h-2.5 w-2.5 rounded-full ${STATUS_STYLE[s].dot}`} />
            {s === "stage1" ? "Stage 1" : s[0].toUpperCase() + s.slice(1)}
          </span>
        ))}
      </div>
    </div>
  );
}

function PlayGlyph() {
  return <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="M7 4v16l13-8z" /></svg>;
}
function StopGlyph() {
  return <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><rect x="5" y="5" width="14" height="14" rx="2" /></svg>;
}
