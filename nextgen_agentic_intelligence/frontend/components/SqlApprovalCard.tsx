"use client";

import { useState } from "react";

/* Human-in-the-loop SQL approval card. Shows the SQL the data-agent generated
 * (editable), and lets the user Approve & Run, Run Edited, or Reject. */
export interface SqlApprovalData {
  sql: string;
  question: string;
  allowed: string[];
}

interface Props {
  data: SqlApprovalData;
  resolved?: string; // set once a decision was made
  onDecision: (decision: "approve" | "edit" | "reject", editedSql: string | null) => void;
}

export default function SqlApprovalCard({ data, resolved, onDecision }: Props) {
  const [sql, setSql] = useState(data.sql);
  const edited = sql.trim() !== data.sql.trim();
  const disabled = !!resolved;
  const can = (d: string) => data.allowed.includes(d);

  return (
    <div className="flex justify-start">
      <div className="w-full max-w-[88%] rounded-2xl rounded-bl-sm border border-optum-orange/40 bg-optum-orange/5 px-4 py-3">
        <div className="mb-1 flex items-center gap-2">
          <span className="text-xs font-semibold text-optum-orange">
            Human approval needed — SQL to run
          </span>
          {resolved && (
            <span className="rounded-full bg-uhc-blue-soft px-2 py-0.5 text-[10px] font-semibold uppercase text-uhc-blue">
              {resolved}
            </span>
          )}
        </div>
        {data.question && (
          <p className="mb-2 text-xs text-gray-500">For: “{data.question}”</p>
        )}
        <textarea
          value={sql}
          onChange={(e) => setSql(e.target.value)}
          disabled={disabled}
          spellCheck={false}
          rows={Math.min(10, Math.max(3, sql.split("\n").length))}
          className="w-full resize-y rounded-lg border border-uhc-blue-soft bg-white p-3 font-mono text-[13px] leading-relaxed text-gray-800 outline-none focus:border-uhc-blue-bright disabled:bg-gray-50 disabled:text-gray-500"
        />
        {!resolved && (
          <div className="mt-3 flex flex-wrap items-center gap-2">
            {can("approve") && (
              <button
                onClick={() => onDecision("approve", null)}
                className="rounded-full bg-uhc-blue px-4 py-1.5 text-sm font-semibold text-white hover:bg-uhc-blue-bright"
              >
                Approve &amp; Run
              </button>
            )}
            {can("edit") && (
              <button
                onClick={() => onDecision("edit", sql)}
                disabled={!edited}
                title={edited ? "Run your edited SQL" : "Edit the SQL above to enable"}
                className="rounded-full bg-optum-orange px-4 py-1.5 text-sm font-semibold text-white hover:bg-optum-orange-dark disabled:opacity-40"
              >
                Run Edited
              </button>
            )}
            {can("reject") && (
              <button
                onClick={() => onDecision("reject", null)}
                className="rounded-full border border-gray-300 px-4 py-1.5 text-sm font-semibold text-gray-600 hover:bg-gray-50"
              >
                Reject
              </button>
            )}
            {edited && (
              <span className="text-[11px] text-optum-orange">edited — use “Run Edited”</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
