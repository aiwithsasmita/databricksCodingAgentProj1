import { STATUS_LABEL, STATUS_STYLE, type Status } from "@/lib/architecture";

/* Pill that labels a node/tool as Live / Stage 1 / Planned. */
export default function StatusBadge({ status, size = "md" }: { status: Status; size?: "sm" | "md" }) {
  const style = STATUS_STYLE[status];
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full ring-1 ${style.chip} ${
        size === "sm" ? "px-1.5 py-0.5 text-[10px]" : "px-2 py-0.5 text-[11px]"
      } font-semibold`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${style.dot}`} />
      {STATUS_LABEL[status]}
    </span>
  );
}
