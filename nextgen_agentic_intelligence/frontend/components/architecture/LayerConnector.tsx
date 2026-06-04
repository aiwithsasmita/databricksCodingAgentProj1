/* Vertical connector drawn between two stacked layer bands. Always shows an
 * upward animated "flow up" line (blue). When `feedback` is set (the boundary
 * between Observation and the Agentic layer) it also shows a downward orange
 * "feedback / regenerate" arrow, closing the learning loop. */
export default function LayerConnector({
  label,
  feedback = false,
}: {
  label: string;
  feedback?: boolean;
}) {
  return (
    <div className="relative flex h-12 items-center justify-center">
      <svg width="100%" height="48" viewBox="0 0 600 48" preserveAspectRatio="none" className="absolute inset-0">
        {/* upward flow (blue) */}
        <line x1="280" y1="46" x2="280" y2="2" stroke="#0066B3" strokeWidth="2" className="arch-flow-up" />
        <path d="M280 2 l-4 7 h8 z" fill="#0066B3" />
        {feedback && (
          <>
            {/* downward feedback (orange) */}
            <line x1="320" y1="2" x2="320" y2="46" stroke="#FF612B" strokeWidth="2" className="arch-flow-down" />
            <path d="M320 46 l-4 -7 h8 z" fill="#FF612B" />
          </>
        )}
      </svg>
      <div className="relative z-10 flex items-center gap-3 rounded-full border border-uhc-blue-soft bg-white px-3 py-1 text-[10px] font-semibold shadow-sm">
        <span className="flex items-center gap-1 text-uhc-blue-bright">↑ {label}</span>
        {feedback && (
          <span className="flex items-center gap-1 border-l border-uhc-blue-soft pl-3 text-optum-orange">
            ↺ feedback · regenerate
          </span>
        )}
      </div>
    </div>
  );
}
