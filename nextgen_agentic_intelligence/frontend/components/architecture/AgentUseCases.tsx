import { AGENT_CARDS, MATURITY_LABEL, MATURITY_STYLE } from "@/lib/agents";
import Icon from "./icons";

/* Business use-cases per agent, shown above the runtime flow diagram. */
export default function AgentUseCases() {
  return (
    <section>
      <div className="mb-4 flex flex-wrap items-end justify-between gap-2">
        <div>
          <h2 className="text-[18px] font-bold tracking-tight text-uhc-blue">What each agent does</h2>
          <p className="text-[13px] text-gray-500">The business signal each autonomous agent is built to surface.</p>
        </div>
        <span className="inline-flex items-center gap-3 text-[11px] text-gray-500">
          <span className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" /> Mature · Live
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-amber-500" /> In Progress · Stage
          </span>
        </span>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {AGENT_CARDS.map((a) => {
          const m = MATURITY_STYLE[a.maturity];
          return (
            <div
              key={a.id}
              className="flex flex-col rounded-2xl border border-uhc-blue-soft bg-white p-4 shadow-card transition-shadow hover:shadow-lg"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2.5">
                  <span className="grid h-9 w-9 place-items-center rounded-lg bg-uhc-blue-soft text-uhc-blue-bright">
                    <Icon name={a.icon} size={18} />
                  </span>
                  <div className="leading-tight">
                    <div className="text-[14px] font-bold text-uhc-blue">{a.name}</div>
                    <div className="text-[11px] text-gray-500">{a.tagline}</div>
                  </div>
                </div>
                <span className={`inline-flex shrink-0 items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold ring-1 ${m.chip}`}>
                  <span className={`h-1.5 w-1.5 rounded-full ${m.dot}`} />
                  {MATURITY_LABEL[a.maturity]}
                </span>
              </div>

              <ul className="mt-3 space-y-1.5">
                {a.useCases.map((u) => (
                  <li key={u} className="flex gap-2 text-[12.5px] leading-snug text-gray-700">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-optum-orange" />
                    {u}
                  </li>
                ))}
              </ul>
            </div>
          );
        })}
      </div>
    </section>
  );
}
