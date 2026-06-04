/* Brand-logo chip. Most logos are local monochrome SVGs (downloaded from Simple
 * Icons) rendered white/colored on a brand-colored rounded chip. OpenAI is drawn
 * inline because its brand mark isn't redistributable via the CDN. */
import type { LogoName } from "@/lib/flow";

const REGISTRY: Record<LogoName, { src?: string; bg: string; pad?: number }> = {
  databricks: { src: "/logos/databricks.svg", bg: "#FF3621" },
  duckdb: { src: "/logos/duckdb.svg", bg: "#0B1F3A" },
  mlflow: { src: "/logos/mlflow.svg", bg: "#0194E2" },
  langgraph: { src: "/logos/langchain.svg", bg: "#1C3C3C" },
  langchain: { src: "/logos/langchain.svg", bg: "#0E5C4A" },
  guardrails: { bg: "#16A34A" }, // inline below
  fastapi: { src: "/logos/fastapi.svg", bg: "#009688" },
  nextjs: { src: "/logos/nextdotjs.svg", bg: "#000000" },
  python: { src: "/logos/python.svg", bg: "#2B5B84" },
  spark: { src: "/logos/spark.svg", bg: "#E25A1C" },
  openai: { bg: "#0B0B0B" }, // inline below
};

function GuardrailsMark({ size }: { size: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="#ffffff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2 4 5v6c0 5 3.5 8 8 11 4.5-3 8-6 8-11V5z" />
      <path d="M9 12l2 2 4-4" />
    </svg>
  );
}

function OpenAIMark({ size }: { size: number }) {
  // Simplified six-fold "blossom" suggestion of the OpenAI knot.
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="#ffffff" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 3.2c1.7-1 3.9-.5 5 1.2.6 1 .7 2.1.4 3.1 1 .5 1.8 1.4 2 2.6.4 2-.9 3.9-2.8 4.4.1 1.1-.3 2.2-1.2 3-1.5 1.3-3.8 1.2-5.2-.3-.9.6-2 .8-3.1.5-2-.5-3.2-2.5-2.7-4.4-1-.6-1.7-1.6-1.8-2.8-.2-2 1.3-3.7 3.2-4 .2-1.1.9-2.1 1.9-2.6 1-.5 2.1-.5 3.1-.1z" />
      <path d="M12 8.2v7.6M8.6 9.9l6.8 3.9M15.4 9.9l-6.8 3.9" />
    </svg>
  );
}

export default function TechLogo({
  logo,
  size = 26,
  rounded = "rounded-lg",
}: {
  logo: LogoName;
  size?: number;
  rounded?: string;
}) {
  const cfg = REGISTRY[logo];
  return (
    <span
      className={`grid shrink-0 place-items-center ${rounded} shadow-sm ring-1 ring-black/5`}
      style={{ background: cfg.bg, width: size, height: size }}
    >
      {logo === "guardrails" ? (
        <GuardrailsMark size={Math.round(size * 0.62)} />
      ) : logo === "openai" || !cfg.src ? (
        <OpenAIMark size={Math.round(size * 0.62)} />
      ) : (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={cfg.src}
          alt={`${logo} logo`}
          loading="lazy"
          style={{ width: Math.round(size * 0.6), height: Math.round(size * 0.6) }}
          className="object-contain"
        />
      )}
    </span>
  );
}
