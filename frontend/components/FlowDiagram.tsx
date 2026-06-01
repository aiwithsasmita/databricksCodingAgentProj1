"use client";

import { useEffect, useId, useRef, useState } from "react";

/* Renders a Mermaid flowchart (the agent's execution trace) into SVG. Themed to
 * the UHC/Optum palette. Falls back to showing the raw diagram code if Mermaid
 * fails to parse. */
export default function FlowDiagram({ code }: { code: string }) {
  const [svg, setSvg] = useState<string>("");
  const [error, setError] = useState<string>("");
  const rawId = useId().replace(/[^a-zA-Z0-9]/g, "");
  const mounted = useRef(true);

  useEffect(() => {
    mounted.current = true;
    (async () => {
      try {
        const mermaid = (await import("mermaid")).default;
        mermaid.initialize({
          startOnLoad: false,
          securityLevel: "strict",
          theme: "base",
          themeVariables: {
            primaryColor: "#E8F0FB",
            primaryBorderColor: "#0066B3",
            primaryTextColor: "#002677",
            lineColor: "#0066B3",
            fontFamily: "Inter, system-ui, sans-serif",
            fontSize: "13px",
          },
        });
        const { svg } = await mermaid.render(`flow-${rawId}`, code);
        if (mounted.current) setSvg(svg);
      } catch (e: any) {
        if (mounted.current) setError(e?.message || "Could not render the diagram.");
      }
    })();
    return () => {
      mounted.current = false;
    };
  }, [code, rawId]);

  if (error) {
    return (
      <div className="mt-2 rounded-lg border border-uhc-blue-soft bg-gray-50 p-3">
        <p className="mb-1 text-xs text-gray-500">Diagram source (render failed):</p>
        <pre className="overflow-x-auto whitespace-pre-wrap text-[11px] text-gray-700">{code}</pre>
      </div>
    );
  }

  return (
    <div
      className="mt-2 overflow-x-auto rounded-lg border border-uhc-blue-soft bg-white p-3 [&_svg]:mx-auto [&_svg]:h-auto [&_svg]:max-w-full"
      // eslint-disable-next-line react/no-danger
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
}
