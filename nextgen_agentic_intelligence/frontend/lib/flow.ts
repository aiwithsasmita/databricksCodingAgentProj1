/* Scene spec for the interactive Agentic Flow canvas (/architecture).
 *
 * One responsive SVG with a fixed viewBox. Top: the agentic runtime flow
 * (Human → Supervisor → specialist agents → analysis subagent + shared Text2SQL
 * → report → observation). Below it, three foundation layer bands the agents
 * draw from — Memory, Context, Data — with data flowing UP into the agent layer.
 * Cross-cutting rails frame it: Observability (MLflow) on top, Data Governance
 * (Unity Catalog) on the bottom.
 *
 * Coordinates live in VIEW.w x VIEW.h space; nodes carry top-left x/y + w/h.
 * Status badges (live / stage1 / planned) are grounded in the real backend.
 */
import type { IconName, NodeDetail, Status } from "@/lib/architecture";

export const VIEW = { w: 1480, h: 1180 };

export type LogoName =
  | "databricks"
  | "duckdb"
  | "mlflow"
  | "langgraph"
  | "langchain"
  | "guardrails"
  | "openai"
  | "fastapi"
  | "nextjs"
  | "python"
  | "spark";

export type NodeKind =
  | "human"
  | "supervisor"
  | "agent"
  | "subagent"
  | "report"
  | "observation"
  | "data"
  | "context"
  | "memory";

export interface FlowNode {
  id: string;
  label: string;
  sublabel: string;
  kind: NodeKind;
  icon: IconName;
  status?: Status;
  logo?: LogoName;
  chips?: string[];
  x: number;
  y: number;
  w: number;
  h: number;
  detail: NodeDetail;
}

export type EdgeKind = "route" | "delegate" | "subagent" | "merge" | "signal" | "feedback" | "data";

export interface FlowEdge {
  from: string;
  to: string;
  kind: EdgeKind;
  label?: string;
  fromSide?: "left" | "right" | "top" | "bottom";
  toSide?: "left" | "right" | "top" | "bottom";
  labelDx?: number;
  labelDy?: number;
}

/* ── Agentic flow nodes (explicit placement) ───────────────────────────── */
const FLOW_NODES: FlowNode[] = [
  {
    id: "human",
    label: "Human",
    sublabel: "asks · approves · gives feedback",
    kind: "human",
    icon: "agent",
    x: 50,
    y: 341,
    w: 128,
    h: 100,
    detail: {
      summary:
        "The analyst or reviewer. Asks questions in the chat UI, approves ad-hoc SQL, and validates the signals the agents surface — their feedback is what the agents learn from.",
      io: { inputs: ["Natural-language question"], outputs: ["Approvals / edits", "Feedback on signals"] },
    },
  },
  {
    id: "supervisor",
    label: "Supervisor",
    sublabel: "DeepAgent · plans & routes",
    kind: "supervisor",
    icon: "agent",
    status: "live",
    logo: "langgraph",
    chips: ["Plan · write_todos", "Skills", "Hooks", "Memory", "task ▸ delegate"],
    x: 232,
    y: 306,
    w: 232,
    h: 170,
    detail: {
      summary:
        "A LangGraph deep agent (deepagents `create_deep_agent`). It plans the work with todos, keeps working memory in a virtual filesystem + a MemorySaver checkpointer, and delegates specialized work to the agents through the built-in `task` tool. It routes; it never answers specialist questions itself.",
      responsibilities: [
        "Plan the request with write_todos",
        "Keep working memory (virtual files + per-thread MemorySaver)",
        "Route to the right specialist via the `task` tool",
        "Summarize each agent's findings for the user",
      ],
      governance: ["DeepAgent runtime: planner + virtual filesystem + skills + hooks", "backend/app/agent.py · SUPERVISOR_PROMPT"],
      notes: "Live — backend/app/agent.py builds the supervisor with deepagents + GPT-5.5 + MemorySaver.",
    },
  },
  {
    id: "drg",
    label: "DRG Agent",
    sublabel: "shift · trends · upcoding",
    kind: "agent",
    icon: "agent",
    status: "live",
    x: 535,
    y: 96,
    w: 186,
    h: 74,
    detail: {
      summary:
        "Mature, built-out agent. Across 900+ DRG families it surfaces DRG trends, provider-opportunity benchmarking, the top ICD trend per family, DRG-shift identification (no CC/MCC → CC → MCC) and upcoding signals. Loads the `drg_clinical_evidence` Skill and runs the 22-tool Analysis subagent.",
      responsibilities: [
        "DRG trend analysis across 900+ families",
        "Upcoding & super-outlier detection",
        "Provider-opportunity benchmarking",
        "DRG severity-shift identification + top-ICD-per-family",
      ],
      governance: ["Skill: backend/skills/drg_clinical_evidence/SKILL.md", "skills.md · agents.md"],
      notes: "Built out — backend/app/subagents/drg_agent.py (mock tools today, optional Databricks Genie).",
    },
  },
  {
    id: "websearch",
    label: "WebResearch Agent",
    sublabel: "external change intel",
    kind: "agent",
    icon: "search",
    status: "live",
    x: 535,
    y: 182,
    w: 186,
    h: 74,
    detail: {
      summary:
        "Mature agent. Tracks the outside world — new DRG / ICD / CPT codes, CMS policy and rule changes, new DRG relative-weight changes and provider Case Mix Index shifts — then analyzes how those changes ripple into Claims and Appeals and shares the signal. Answers CMS reference from ingested IPPS data and runs live web research.",
      responsibilities: [
        "Trend analytics for new DRG / ICD / CPT codes",
        "New policy & CMS rule-change intelligence",
        "New DRG relative-weight & provider Case Mix Index shifts",
        "Impact of those changes on Claims & Appeals → signal",
      ],
      notes: "Built out — backend/app/subagents/context_agent.py + search_agent.py (CMS tools + web_search).",
    },
  },
  {
    id: "callcenter",
    label: "Call Center Agent",
    sublabel: "voice-of-member intel",
    kind: "agent",
    icon: "signal",
    status: "stage1",
    x: 535,
    y: 268,
    w: 186,
    h: 74,
    detail: {
      summary:
        "Reads every member & provider call to understand the intent of the call and the overall sentiment per call category, and raises early signals on emerging trends — new-drug queries, new-procedure queries, churning providers — to lift the provider & member experience.",
      responsibilities: [
        "Intent of each member & provider call",
        "Overall sentiment by call category",
        "Early signals: new-drug / new-procedure queries, churning providers",
        "Improve the overall provider & member experience",
      ],
      notes: "In progress (Stage) — backend/app/subagents/callcenter_agent.py (mock tool today).",
    },
  },
  {
    id: "appeals",
    label: "Appeals Agent",
    sublabel: "spend & denial foresight",
    kind: "agent",
    icon: "shield",
    status: "stage1",
    x: 535,
    y: 354,
    w: 186,
    h: 74,
    detail: {
      summary:
        "Forecasts the cost story behind appeals — predicts incremental / avoidable spend and raises appeals-volume, denial-trend and overturn-rate signals.",
      responsibilities: ["Predict incremental / avoidable spend", "Appeals-volume & denial-trend signals", "Overturn-rate & appeal-reason analysis"],
      notes: "In progress (Stage) — backend/app/subagents/appeals_agent.py (mock tool today).",
    },
  },
  {
    id: "provider-similarity",
    label: "Provider Similarity",
    sublabel: "true peer benchmarking",
    kind: "agent",
    icon: "embedding",
    status: "live",
    x: 535,
    y: 440,
    w: 186,
    h: 74,
    detail: {
      summary:
        "Compares each provider only against true peers — same organization type, geography, taxonomy, contract, network and operational efficiency — and surfaces the behavior patterns and outliers that emerge among like-for-like providers.",
      responsibilities: [
        "Peer match on org type, geo, taxonomy, contract & network",
        "Compare operational efficiency across the peer set",
        "Flag providers drifting toward already-flagged outliers",
        "Recommend new geos / providers likely to show the pattern next",
      ],
      notes: "In progress (Stage). Backed by the Provider Similarity table in the context layer.",
    },
  },
  {
    id: "referral-network",
    label: "Referral Network",
    sublabel: "referral patterns · leakage",
    kind: "agent",
    icon: "embedding",
    status: "stage1",
    x: 535,
    y: 526,
    w: 186,
    h: 74,
    detail: {
      summary:
        "Maps provider-to-provider referral patterns, detects leakage and steering, and raises network-integrity and continuity-of-care signals.",
      responsibilities: ["Map referral patterns & where care flows", "Detect leakage & out-of-network steering", "Surface referral hotspots & recommend in-network paths", "Network-integrity & continuity-of-care signals"],
      notes: "In progress (Stage). Backed by the Referral Networks graph in the context layer.",
    },
  },
  {
    id: "claim-similarity",
    label: "Claim Similarity",
    sublabel: "similar-claim cohorts",
    kind: "agent",
    icon: "tool",
    status: "stage1",
    x: 535,
    y: 612,
    w: 186,
    h: 74,
    detail: {
      summary:
        "Builds control & treatment cohorts from similar claims — same member risk, age, plan, ICD / diagnostic — so we can explain why similar members get different treatment plans across providers, and compare providers apples-to-apples.",
      responsibilities: [
        "Cohort similar claims (member risk, age, plan, ICD / diagnostic)",
        "Control & treatment groups for any experiment",
        "Explain differing treatment plans across like providers",
        "Identify geo hotspots where a cohort's utilization runs high",
      ],
      notes: "In progress (Stage). Backed by the Claim Similarity table in the context layer.",
    },
  },
  {
    id: "analysis",
    label: "Analysis Subagent",
    sublabel: "DRG · 22-tool suite",
    kind: "subagent",
    icon: "tool",
    status: "planned",
    chips: ["Shift-Score", "Provider Sim", "Claim Sim", "Top-ICD", "+18"],
    x: 805,
    y: 96,
    w: 206,
    h: 100,
    detail: {
      summary:
        "The DRG agent's analytical engine. Runs the 22-tool suite (Shift-Score, Provider Similarity, Claim Similarity, Top-ICD-Shift, Upcoding-Detect, …) and hands the findings to Report Generation; the two interact until the report is complete.",
      tools: [
        { name: "Shift-Score Identification", status: "stage1" },
        { name: "Provider Similarity", status: "planned" },
        { name: "Claim Similarity", status: "planned" },
        { name: "Top-ICD-Shift", status: "stage1" },
        { name: "Provider Utilization", status: "stage1" },
        { name: "Upcoding Detection", status: "planned" },
        { name: "… +16 more", status: "planned" },
      ],
      notes: "3 tools exist today as Stage-1 mocks; the full 22-tool suite is planned.",
    },
  },
  {
    id: "text2sql",
    label: "Text2SQL",
    sublabel: "ad-hoc · shared by all agents",
    kind: "subagent",
    icon: "sql",
    status: "live",
    chips: ["any agent", "human approves", "→ DuckDB + LakeBase"],
    x: 805,
    y: 330,
    w: 206,
    h: 100,
    detail: {
      summary:
        "A shared ad-hoc capability available to EVERY agent — not just DRG. For any unknown question an agent generates SQL, pauses for a human to approve or edit, executes on Databricks Genie, then caches the approved SQL to DuckDB + LakeBase for instant reuse. Approved queries can be registered as reusable tools from the frontend.",
      responsibilities: [
        "run_saved_sql → reuse previously approved SQL",
        "genie_generate_sql → candidate SQL",
        "execute_sql → PAUSE for human approve / edit / reject",
        "Cache approved query → DuckDB + LakeBase",
      ],
      tools: [
        { name: "run_saved_sql", status: "live" },
        { name: "genie_generate_sql", status: "live" },
        { name: "execute_sql (HITL interrupt)", status: "live" },
        { name: "register approved query as tool", status: "planned" },
      ],
      notes: "Live — backend/app/subagents/data_agent.py + backend/app/genie/hitl_tools.py; offered to all agents.",
    },
  },
  {
    id: "report",
    label: "Report Generation",
    sublabel: "assembles the signal",
    kind: "report",
    icon: "report",
    status: "planned",
    x: 1078,
    y: 327,
    w: 200,
    h: 136,
    detail: {
      summary:
        "Consumes every agent's findings — DRG analysis, Text2SQL results and the other specialists' signals — and assembles one complete signal. If anything is missing it loops back until the report is whole.",
      notes: "Vision component — not yet implemented.",
    },
  },
  {
    id: "observation",
    label: "Observation / Signal",
    sublabel: "validate · feedback",
    kind: "observation",
    icon: "signal",
    status: "planned",
    chips: ["Business validation", "Feedback store"],
    x: 1292,
    y: 331,
    w: 180,
    h: 128,
    detail: {
      summary:
        "The surfaced (frontend) layer. The business validates the signals and gives feedback; the feedback is persisted and fed back to the agents, which autonomously regenerate improved signals — the learning flywheel.",
      io: { inputs: ["Report / signals"], outputs: ["Validated signals", "Feedback → agents"] },
      notes: "Vision component — surfaced in the frontend; not yet implemented.",
    },
  },
];

/* ── Foundation layer bands (auto-laid-out rows) ───────────────────────── */
type LayerItem = Omit<FlowNode, "x" | "y" | "w" | "h">;

const BAND_X = 184;
const BAND_W = 1230;
const BAND_GAP = 16;
const CARD_OFFSET = 16;
const CARD_H = 78;

function layoutBand(items: LayerItem[], bandY: number): FlowNode[] {
  const n = items.length;
  const w = (BAND_W - BAND_GAP * (n - 1)) / n;
  return items.map((it, i) => ({ ...it, x: BAND_X + i * (w + BAND_GAP), y: bandY + CARD_OFFSET, w, h: CARD_H }));
}

const MEMORY_ITEMS: LayerItem[] = [
  { id: "session-memory", label: "User Session Memory", sublabel: "per-thread chat context", kind: "memory", icon: "memory", status: "live", detail: { summary: "Per-thread conversation memory (LangGraph MemorySaver) so the chat keeps context across turns.", notes: "Live — MemorySaver in backend/app/agent.py." } },
  { id: "in-memory", label: "In-Memory", sublabel: "fast working state", kind: "memory", icon: "memory", status: "stage1", detail: { summary: "Ephemeral working memory for the current run — the deep agent's virtual filesystem and scratch state.", notes: "Stage-1 — deepagents virtual filesystem." } },
  { id: "duckdb", label: "DuckDB", sublabel: "approved-SQL cache", kind: "memory", icon: "memory", status: "stage1", logo: "duckdb", detail: { summary: "Fast local store / cache of human-approved SQL so blessed questions skip re-approval.", notes: "Stage-1 — backend/data/saved_queries.json; DuckDB upgrade planned." } },
  { id: "procedural-memory", label: "Procedural Memory", sublabel: "skills & playbooks", kind: "memory", icon: "memory", status: "stage1", detail: { summary: "Reusable know-how loaded as Skills — e.g. the clinical-evidence playbook the DRG agent consults.", governance: ["backend/skills/drg_clinical_evidence/SKILL.md"], notes: "Stage-1 — clinical-evidence Skill loaded into the DRG agent." } },
  { id: "lakebase", label: "LakeBase", sublabel: "durable long-term (Databricks)", kind: "memory", icon: "database", status: "planned", logo: "databricks", detail: { summary: "Durable long-term memory on Databricks LakeBase — approved queries, learned signals and history beyond a thread.", notes: "Planned — Genie client exists; LakeBase long-term store not yet wired." } },
];

const CONTEXT_ITEMS: LayerItem[] = [
  { id: "provider-embedding", label: "Provider Embedding", sublabel: "vector space of behavior", kind: "context", icon: "embedding", status: "planned", detail: { summary: "Dense vectors of each provider's coding & utilization behavior, enabling 'providers like this one' lookups.", notes: "Planned." } },
  { id: "claim-similarity-tbl", label: "Claim Similarity", sublabel: "similar-claim cohorts", kind: "context", icon: "embedding", status: "stage1", detail: { summary: "Similar claims grouped by member risk, age, plan, ICD / diagnostic and severity to build control & treatment cohorts — backs the Claim Similarity agent and answers why similar members get different treatment plans across providers.", notes: "In progress (Stage)." } },
  { id: "member-risk-scores", label: "Member Risk Scores", sublabel: "computed risk tiers", kind: "context", icon: "signal", status: "planned", detail: { summary: "Per-member risk scores derived from member risk data — used to risk-adjust utilization and shift signals.", notes: "Planned." } },
  { id: "cms-data", label: "CMS Data", sublabel: "IPPS Final Rule FY23–26", kind: "context", icon: "cms", status: "live", detail: { summary: "Authoritative MS-DRG reference from official CMS IPPS Final Rule files (FY2023–FY2026): DRG catalog, CC/MCC lists, ICD-10 updates, payment rules. 8 live tools.", notes: "Live — backend/data/cms/ + backend/app/tools/cms_tools.py." } },
  { id: "provider-similarity-tbl", label: "Provider Similarity", sublabel: "nearest-neighbor table", kind: "context", icon: "tool", status: "planned", detail: { summary: "Precomputed provider-to-provider distance over provider embeddings — backs the Provider Similarity agent.", notes: "Planned." } },
  { id: "referral-graph", label: "Referral Networks", sublabel: "provider referral graph", kind: "context", icon: "embedding", status: "planned", detail: { summary: "Graph of referral relationships between providers — backs the Referral Network agent (leakage & steering).", notes: "Planned." } },
];

const DATA_ITEMS: LayerItem[] = [
  { id: "claims", label: "Claims Data", sublabel: "DRG · ICD · comorbidities · cost", kind: "data", icon: "database", status: "planned", detail: { summary: "Inpatient claim records — assigned MS-DRG, ICD-10 codes, CC/MCC comorbidities, length of stay, paid amounts.", notes: "Planned — DRG analysis runs on mock fixtures today." } },
  { id: "appeals-data", label: "Appeals Data", sublabel: "reasons · decisions · timelines", kind: "data", icon: "database", status: "stage1", detail: { summary: "Appeal cases — reason, overturn/upheld decision, timelines, volumes. Feeds the Appeals agent.", notes: "Stage-1 — mock appeals_lookup." } },
  { id: "ndb", label: "Provider Data (NDB)", sublabel: "TIN · specialty · geography", kind: "data", icon: "database", status: "planned", detail: { summary: "National provider directory — TIN, specialty, geography, network participation. Anchors benchmarking & similarity.", notes: "Planned." } },
  { id: "member-enroll", label: "Member Plan & Enrollment", sublabel: "eligibility · enrollment history", kind: "data", icon: "database", status: "planned", detail: { summary: "Member plan, eligibility and enrollment history.", notes: "Planned." } },
  { id: "member-risk-data", label: "Member Risk Data", sublabel: "HCC · risk factors", kind: "data", icon: "database", status: "planned", detail: { summary: "Member risk data (HCC conditions, risk factors) feeding the computed Member Risk Scores in the context layer.", notes: "Planned." } },
  { id: "network", label: "Network Data", sublabel: "in-network · contracted rates", kind: "data", icon: "database", status: "planned", detail: { summary: "Network participation and contracted rates per provider/facility — context for provider-opportunity benchmarking.", notes: "Planned." } },
  { id: "callcenter-data", label: "Call Center Data", sublabel: "calls · sentiment · handle time", kind: "data", icon: "database", status: "stage1", detail: { summary: "Call-center operations — volumes, top reasons, handle time, complaints, sentiment. Feeds the Call Center agent.", notes: "Stage-1 — mock callcenter_lookup." } },
];

/* Band geometry (rect behind the cards) — bottom-to-top: Data, Context, Memory. */
export const BANDS: { id: string; title: string; zone: "backend"; y: number; h: number }[] = [
  { id: "memory", title: "Memory Layer", zone: "backend", y: 732, h: 104 },
  { id: "context", title: "Context Layer", zone: "backend", y: 868, h: 104 },
  { id: "data", title: "Data Layer", zone: "backend", y: 1004, h: 104 },
];

/* Upward "data flows up" arrows between bands and into the agent layer. */
export const BUS_X = [300, 620, 900, 1200];
export const BUS_GAPS: [number, number][] = [
  [728, 692], // memory → agent layer
  [864, 838], // context → memory
  [1000, 974], // data → context
];

export const NODES: FlowNode[] = [
  ...FLOW_NODES,
  ...layoutBand(MEMORY_ITEMS, 732),
  ...layoutBand(CONTEXT_ITEMS, 868),
  ...layoutBand(DATA_ITEMS, 1004),
];

export const NODE_BY_ID: Record<string, FlowNode> = Object.fromEntries(NODES.map((n) => [n.id, n]));

/* ── Edges (agentic flow only) ─────────────────────────────────────────── */
export const EDGES: FlowEdge[] = [
  { from: "human", to: "supervisor", kind: "route", label: "asks" },
  { from: "supervisor", to: "drg", kind: "delegate", label: "task ▸ delegate", labelDy: -30 },
  { from: "supervisor", to: "websearch", kind: "delegate" },
  { from: "supervisor", to: "callcenter", kind: "delegate" },
  { from: "supervisor", to: "appeals", kind: "delegate" },
  { from: "supervisor", to: "provider-similarity", kind: "delegate" },
  { from: "supervisor", to: "referral-network", kind: "delegate" },
  { from: "supervisor", to: "claim-similarity", kind: "delegate" },
  { from: "supervisor", to: "text2sql", kind: "delegate", label: "ad-hoc · all agents", labelDx: 150, labelDy: -8 },
  { from: "drg", to: "analysis", kind: "subagent", label: "analyze" },
  { from: "analysis", to: "report", kind: "merge", label: "findings" },
  { from: "text2sql", to: "report", kind: "merge", label: "results" },
  { from: "websearch", to: "report", kind: "merge" },
  { from: "callcenter", to: "report", kind: "merge" },
  { from: "appeals", to: "report", kind: "merge" },
  { from: "provider-similarity", to: "report", kind: "merge" },
  { from: "referral-network", to: "report", kind: "merge" },
  { from: "claim-similarity", to: "report", kind: "merge" },
  { from: "report", to: "observation", kind: "signal", label: "report", labelDy: -82 },
  { from: "observation", to: "supervisor", kind: "feedback", label: "feedback · regenerate", fromSide: "bottom", toSide: "bottom" },
];

/* Play-the-flow sequence — groups light up in order. */
export const PLAY_SEQUENCE: string[][] = [
  ["human"],
  ["supervisor"],
  ["drg", "websearch", "callcenter", "appeals", "provider-similarity", "referral-network", "claim-similarity", "text2sql"],
  ["analysis"],
  ["report"],
  ["observation"],
];

/* Technologies shown in the stack strip below the canvas. */
export const TECH_STACK: { logo: LogoName; label: string }[] = [
  { logo: "langgraph", label: "LangGraph · deepagents" },
  { logo: "langchain", label: "LangChain" },
  { logo: "guardrails", label: "Guardrails" },
  { logo: "databricks", label: "Databricks Genie + LakeBase" },
  { logo: "duckdb", label: "DuckDB" },
  { logo: "mlflow", label: "MLflow" },
  { logo: "spark", label: "Apache Spark" },
  { logo: "fastapi", label: "FastAPI" },
  { logo: "nextjs", label: "Next.js" },
  { logo: "python", label: "Python" },
];
