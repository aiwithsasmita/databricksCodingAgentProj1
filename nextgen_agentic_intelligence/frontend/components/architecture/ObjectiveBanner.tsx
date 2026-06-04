import { OBJECTIVE } from "@/lib/agents";

/* Top-of-page objective: what the Agentic Intelligence Layer does (lead), the
 * mission, the differentiators, and the savings stat. */
export default function ObjectiveBanner() {
  return (
    <section className="overflow-hidden rounded-2xl bg-gradient-to-br from-uhc-blue via-uhc-blue to-[#012a86] text-white shadow-card">
      <div className="grid gap-6 p-6 sm:p-8 lg:grid-cols-[1.7fr_1fr] lg:gap-10">
        <div>
          <h1 className="text-2xl font-bold tracking-tight sm:text-[28px]">{OBJECTIVE.headline}</h1>

          {/* Lead: what they do, on top */}
          <p className="mt-4 rounded-xl border-l-2 border-optum-orange bg-white/5 px-4 py-3 text-[13.5px] font-medium leading-relaxed text-white/90">
            {OBJECTIVE.lead}
          </p>

          <p className="mt-4 max-w-2xl text-[13.5px] leading-relaxed text-white/80">{OBJECTIVE.body}</p>
        </div>

        {/* Savings stat */}
        <div className="flex items-center">
          <div className="w-full rounded-2xl border border-white/15 bg-white/5 p-5 backdrop-blur-sm">
            <span className="bg-gradient-to-r from-white to-[#9cc2ff] bg-clip-text text-5xl font-extrabold tracking-tight text-transparent">
              {OBJECTIVE.stat.value}
            </span>
            <p className="mt-2 text-[13px] font-medium leading-snug text-white/80">{OBJECTIVE.stat.label}</p>
            <div className="mt-4 flex items-center gap-2 border-t border-white/10 pt-3 text-[11px] text-white/60">
              <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-400" />
              autonomous · always on · feedback driven
            </div>
          </div>
        </div>
      </div>

      {/* Differentiators */}
      <div className="border-t border-white/10 bg-black/10 px-6 py-5 sm:px-8">
        <div className="grid gap-x-6 gap-y-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
          {OBJECTIVE.highlights.map((h) => (
            <div key={h.title} className="flex gap-2.5">
              <CheckGlyph />
              <div>
                <div className="text-[12.5px] font-bold leading-tight text-white">{h.title}</div>
                <div className="mt-0.5 text-[11px] leading-snug text-white/65">{h.text}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function CheckGlyph() {
  return (
    <svg className="mt-0.5 shrink-0 text-optum-orange" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 6 9 17l-5-5" />
    </svg>
  );
}
