import { STATUS_LABEL, STATUS_STYLE, type Status } from "@/lib/architecture";

/* Compact key: status meaning (Live/Stage-1/Planned) + Frontend/Backend zones. */
const STATUSES: Status[] = ["live", "stage1", "planned"];

export default function Legend() {
  return (
    <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-[12px] text-gray-500">
      <div className="flex items-center gap-3">
        {STATUSES.map((s) => (
          <span key={s} className="flex items-center gap-1.5">
            <span className={`h-2.5 w-2.5 rounded-full ${STATUS_STYLE[s].dot}`} />
            {STATUS_LABEL[s]}
          </span>
        ))}
      </div>
      <span className="hidden h-4 w-px bg-uhc-blue-soft sm:block" />
      <div className="flex items-center gap-3">
        <span className="flex items-center gap-1.5">
          <span className="h-2.5 w-4 rounded-sm bg-uhc-blue-soft ring-1 ring-uhc-blue-bright/40" />
          Backend
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2.5 w-4 rounded-sm bg-optum-orange/15 ring-1 ring-optum-orange/40" />
          Frontend
        </span>
      </div>
    </div>
  );
}
