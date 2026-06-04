"use client";

import { useEffect } from "react";
import type { IconName, NodeDetail, Status } from "@/lib/architecture";
import Icon from "./icons";
import StatusBadge from "./StatusBadge";

/* Minimal shape the panel needs — satisfied by both the layer spec (ArchNode)
 * and the flow spec (FlowNode). */
export interface PanelNode {
  id: string;
  label: string;
  icon: IconName;
  status?: Status;
  detail: NodeDetail;
  relatedIds?: string[];
}

interface DetailPanelProps {
  node: PanelNode | null;
  onClose: () => void;
  onSelect: (id: string) => void;
  /* Lookup for resolving relatedIds into clickable chips. */
  nodeById?: Record<string, { id: string; label: string; icon: IconName }>;
}

export default function DetailPanel({ node, onClose, onSelect, nodeById = {} }: DetailPanelProps) {
  const open = node !== null;

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  return (
    <>
      <div
        onClick={onClose}
        aria-hidden="true"
        className={`fixed inset-0 z-40 bg-uhc-blue/20 backdrop-blur-[1px] transition-opacity duration-300 ${
          open ? "opacity-100" : "pointer-events-none opacity-0"
        }`}
      />
      <aside
        role="dialog"
        aria-modal="true"
        aria-label={node ? `${node.label} details` : "Node details"}
        className={`chat-scroll fixed z-50 overflow-y-auto bg-white shadow-2xl transition-transform duration-300 ease-out
          inset-x-0 bottom-0 max-h-[85vh] rounded-t-2xl
          sm:inset-y-0 sm:left-auto sm:right-0 sm:bottom-auto sm:h-full sm:max-h-none sm:w-[420px] sm:max-w-[90vw] sm:rounded-none ${
            open ? "translate-y-0 sm:translate-x-0" : "translate-y-full sm:translate-y-0 sm:translate-x-full"
          }`}
      >
        {node && <PanelBody node={node} onClose={onClose} onSelect={onSelect} nodeById={nodeById} />}
      </aside>
    </>
  );
}

function PanelBody({
  node,
  onClose,
  onSelect,
  nodeById,
}: {
  node: PanelNode;
  onClose: () => void;
  onSelect: (id: string) => void;
  nodeById: Record<string, { id: string; label: string; icon: IconName }>;
}) {
  const d = node.detail;
  const hasResponsibilities = !!d.responsibilities && d.responsibilities.length > 0;
  const related = (node.relatedIds ?? []).map((id) => nodeById[id]).filter(Boolean);

  return (
    <div>
      <div className="h-1 w-full bg-gradient-to-r from-uhc-blue via-uhc-blue-bright to-optum-orange" />

      <div className="sticky top-0 z-10 flex items-start justify-between gap-3 border-b border-uhc-blue-soft bg-white/95 px-5 py-4 backdrop-blur">
        <div className="flex items-start gap-3">
          <span className="grid h-10 w-10 place-items-center rounded-lg bg-uhc-blue-soft text-uhc-blue-bright">
            <Icon name={node.icon} size={20} />
          </span>
          <div>
            <h3 className="text-[16px] font-bold leading-tight text-uhc-blue">{node.label}</h3>
            {node.status && (
              <div className="mt-1">
                <StatusBadge status={node.status} />
              </div>
            )}
          </div>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close"
          className="grid h-8 w-8 shrink-0 place-items-center rounded-full text-gray-400 transition-colors hover:bg-uhc-blue-soft hover:text-uhc-blue"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M18 6 6 18M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div className="space-y-5 px-5 py-5">
        <div>
          {hasResponsibilities ? (
            <>
              <h4 className="mb-2.5 text-[11px] font-bold uppercase tracking-[0.14em] text-gray-400">Responsibilities</h4>
              <ul className="space-y-2">
                {d.responsibilities!.map((r) => (
                  <li key={r} className="flex gap-2.5 text-[13.5px] leading-snug text-gray-700">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-optum-orange" />
                    {r}
                  </li>
                ))}
              </ul>
            </>
          ) : (
            <p className="text-[13.5px] leading-relaxed text-gray-700">{d.summary}</p>
          )}
        </div>

        {related.length > 0 && (
          <div>
            <h4 className="mb-2 text-[11px] font-bold uppercase tracking-[0.14em] text-gray-400">Connected to</h4>
            <div className="flex flex-wrap gap-1.5">
              {related.map((r) => (
                <button
                  key={r.id}
                  type="button"
                  onClick={() => onSelect(r.id)}
                  className="inline-flex items-center gap-1.5 rounded-full border border-uhc-blue-soft bg-white px-2.5 py-1 text-[11px] font-medium text-uhc-blue-bright transition-colors hover:bg-uhc-blue-soft"
                >
                  <Icon name={r.icon} size={12} />
                  {r.label}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
