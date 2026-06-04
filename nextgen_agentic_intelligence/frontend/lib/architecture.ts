/* Single source of truth for the interactive architecture diagram (/architecture).
 *
 * The whole page renders from this spec — layers are drawn bottom-to-top
 * (Data at the bottom, Observation/Signal at the top). Each node carries a
 * status badge so the diagram doubles as an honest roadmap:
 *   - "live"    : implemented and working today
 *   - "stage1"  : implemented as a Stage-1 stub / mock, real data pending
 *   - "planned" : part of the vision, not yet built
 *
 * Status values are grounded in the real backend (backend/app/...), not guessed.
 */

export type Status = "live" | "stage1" | "planned";
export type Zone = "frontend" | "backend";
export type IconName =
  | "database"
  | "layers"
  | "memory"
  | "agent"
  | "signal"
  | "search"
  | "tool"
  | "sql"
  | "report"
  | "shield"
  | "cms"
  | "embedding";

export interface SubAgent {
  name: string;
  status: Status;
  detail: string;
}

export interface NodeDetail {
  summary: string;
  responsibilities?: string[];
  subAgents?: SubAgent[];
  tools?: { name: string; status: Status }[];
  io?: { inputs?: string[]; outputs?: string[] };
  governance?: string[];
  notes?: string;
}

export interface ArchNode {
  id: string;
  label: string;
  tagline: string;
  icon: IconName;
  status: Status;
  /** Optional hint chip rendered on the card (e.g. DRG agent fan-out). */
  hint?: string;
  detail: NodeDetail;
  /** Ids of related nodes — hovering this node spotlights them. */
  relatedIds?: string[];
}

export interface Layer {
  id: string;
  title: string;
  zone: Zone;
  blurb: string;
  nodes: ArchNode[];
}

export const STATUS_LABEL: Record<Status, string> = {
  live: "Live",
  stage1: "Stage 1",
  planned: "Planned",
};

/* Tailwind classes per status — emerald (live) / amber (stage-1) / slate (planned). */
export const STATUS_STYLE: Record<Status, { dot: string; chip: string }> = {
  live: { dot: "bg-emerald-500", chip: "bg-emerald-50 text-emerald-700 ring-emerald-200" },
  stage1: { dot: "bg-amber-500", chip: "bg-amber-50 text-amber-700 ring-amber-200" },
  planned: { dot: "bg-slate-400", chip: "bg-slate-100 text-slate-600 ring-slate-200" },
};

/* Layers are declared bottom → top, exactly as the user reads the platform. */
export const LAYERS: Layer[] = [
  {
    id: "data",
    title: "Data Layer",
    zone: "backend",
    blurb: "Systems of record — the raw claims, appeals, provider, network and member data the platform reasons over.",
    nodes: [
      {
        id: "claims",
        label: "Claims",
        tagline: "DRG codes, comorbidities, procedures, cost",
        icon: "database",
        status: "planned",
        relatedIds: ["claim-embedding", "drg-agent"],
        detail: {
          summary:
            "Inpatient claim records — assigned MS-DRG, ICD-10 diagnosis/procedure codes, CC/MCC comorbidities, length of stay and paid amounts. The substrate for all DRG-shift and upcoding analysis.",
          io: {
            inputs: ["Claim feeds / 837I"],
            outputs: ["Claim embeddings", "DRG tier-mix aggregates"],
          },
          notes:
            "Not yet wired to a live source. DRG analysis currently runs on mock fixtures (backend/app/tools/mock_tools.py) with an optional Databricks Genie path.",
        },
      },
      {
        id: "appeals-data",
        label: "Appeals",
        tagline: "Appeal reasons, decisions, timelines",
        icon: "database",
        status: "stage1",
        relatedIds: ["appeals-agent"],
        detail: {
          summary:
            "Appeal case records — reason for appeal, overturn/upheld decision, decision timelines and volumes. Feeds the Appeals agent.",
          io: { outputs: ["Overturn / upheld rates", "Decision-time stats"] },
          notes: "Backed today by the mock `appeals_lookup` tool; a real Databricks Genie appeals space is planned.",
        },
      },
      {
        id: "ndb",
        label: "NDB Provider Data",
        tagline: "TIN, specialty, geography, contracts",
        icon: "database",
        status: "planned",
        relatedIds: ["provider-embedding", "provider-similarity"],
        detail: {
          summary:
            "National provider directory — TIN, specialty, geography and network participation. Anchors provider benchmarking and similarity.",
          notes: "Vision component — not yet present in the backend.",
        },
      },
      {
        id: "network",
        label: "Network & Contract Data",
        tagline: "In-network status, rates, restrictions",
        icon: "database",
        status: "planned",
        detail: {
          summary:
            "Contracted rates, in-network status and restrictions per provider/facility — context for provider-opportunity benchmarking.",
          notes: "Vision component — not yet present in the backend.",
        },
      },
      {
        id: "member",
        label: "Member Risk & Enrollment",
        tagline: "Risk scores, eligibility, enrollment history",
        icon: "database",
        status: "planned",
        detail: {
          summary:
            "Member-level risk scores, eligibility and enrollment history — used to risk-adjust utilization and shift signals.",
          notes: "Vision component — not yet present in the backend.",
        },
      },
      {
        id: "callcenter-data",
        label: "Call Center Data",
        tagline: "Call reasons, duration, sentiment, agent metrics",
        icon: "database",
        status: "stage1",
        relatedIds: ["callcenter-agent"],
        detail: {
          summary:
            "Call-center operations data — call volumes, top reasons, handle time, complaints and service level. Feeds the Call Center agent.",
          notes: "Backed today by the mock `callcenter_lookup` tool; a real Genie call-center space is planned.",
        },
      },
    ],
  },
  {
    id: "context",
    title: "Context Layer",
    zone: "backend",
    blurb: "Derived intelligence — embeddings, clusters, similarity tables and authoritative CMS reference that give the agents meaning.",
    nodes: [
      {
        id: "provider-embedding",
        label: "Provider Embedding",
        tagline: "Vector space of provider behavior",
        icon: "embedding",
        status: "planned",
        relatedIds: ["provider-similarity", "ndb"],
        detail: {
          summary:
            "Dense vector representation of each provider's coding & utilization behavior, enabling semantic 'providers like this one' lookups.",
          notes: "Vision component — not yet implemented.",
        },
      },
      {
        id: "diagnostic-clusters",
        label: "Diagnostic Clusters",
        tagline: "ICD codes grouped by clinical syndrome",
        icon: "embedding",
        status: "planned",
        detail: {
          summary:
            "ICD-10 codes grouped into clinical syndromes so shift analysis can reason at the syndrome level, not just the code level.",
          notes: "Vision component — not yet implemented.",
        },
      },
      {
        id: "claim-embedding",
        label: "Claim Embedding",
        tagline: "Vector space of claim content",
        icon: "embedding",
        status: "planned",
        relatedIds: ["claims"],
        detail: {
          summary:
            "Dense vector representation of claims, powering 'claims similar to this one' retrieval for outlier and upcoding detection.",
          notes: "Vision component — not yet implemented.",
        },
      },
      {
        id: "cms-data",
        label: "CMS Data",
        tagline: "IPPS Final Rule reference, FY2023–FY2026",
        icon: "cms",
        status: "live",
        relatedIds: ["context-agent"],
        detail: {
          summary:
            "Authoritative MS-DRG reference ingested from the official CMS IPPS Final Rule files (FY2023–FY2026): full DRG catalog, CC/MCC severity lists, ICD-10 updates and payment-rule changes.",
          tools: [
            { name: "cms_drg_lookup", status: "live" },
            { name: "cms_drg_changes", status: "live" },
            { name: "cms_ipps_rule", status: "live" },
            { name: "cms_search_drgs", status: "live" },
            { name: "cms_compare_drg", status: "live" },
            { name: "cms_cc_mcc", status: "live" },
            { name: "cms_icd10_updates", status: "live" },
            { name: "cms_cc_mcc_changes", status: "live" },
          ],
          io: {
            inputs: ["CMS IPPS Final Rule files"],
            outputs: ["DRG catalog", "CC/MCC lists", "Payment-rule deltas"],
          },
          notes:
            "Fully live — real data under backend/data/cms/, served by 8 tools in backend/app/tools/cms_tools.py.",
        },
      },
      {
        id: "referral-networks",
        label: "Referral Networks",
        tagline: "Provider-to-provider referral patterns",
        icon: "embedding",
        status: "planned",
        detail: {
          summary: "Graph of referral relationships between providers — context for steering and leakage analysis.",
          notes: "Vision component — not yet implemented.",
        },
      },
      {
        id: "provider-similarity",
        label: "Provider Similarity Table",
        tagline: "Precomputed provider-to-provider distance",
        icon: "tool",
        status: "planned",
        relatedIds: ["provider-embedding", "ndb"],
        detail: {
          summary:
            "Precomputed nearest-neighbor table over provider embeddings — the backing store for the Provider Similarity tool in the DRG agent's 22-tool suite.",
          notes: "Vision component — not yet implemented.",
        },
      },
    ],
  },
  {
    id: "memory",
    title: "Memory Layer",
    zone: "backend",
    blurb: "Where the platform remembers — fast in-memory state, learned procedures, and durable long-term storage.",
    nodes: [
      {
        id: "in-memory",
        label: "In-Memory · DuckDB",
        tagline: "Fast working state & approved-query cache",
        icon: "memory",
        status: "stage1",
        relatedIds: ["text2sql"],
        detail: {
          summary:
            "Fast, ephemeral working memory for the current run plus a cache of human-approved SQL so previously-blessed questions skip re-approval.",
          notes:
            "Today: LangGraph `MemorySaver` per-thread checkpointer + backend/data/saved_queries.json cache. A DuckDB-backed store is the planned upgrade.",
        },
      },
      {
        id: "procedural-memory",
        label: "Procedural Memory",
        tagline: "Skills & decision playbooks",
        icon: "memory",
        status: "stage1",
        relatedIds: ["drg-agent"],
        detail: {
          summary:
            "Reusable know-how the agents load as skills — e.g. the clinical-evidence playbook that decides whether an upward DRG severity shift is clinically justified.",
          governance: ["backend/skills/drg_clinical_evidence/SKILL.md"],
          notes: "Stage-1 placeholder rules are loaded into the DRG agent; validated criteria come in later stages.",
        },
      },
      {
        id: "long-term-memory",
        label: "Long-Term Memory · LakeBase",
        tagline: "Durable store on Databricks LakeBase",
        icon: "memory",
        status: "planned",
        relatedIds: ["text2sql"],
        detail: {
          summary:
            "Durable, queryable long-term memory on Databricks LakeBase — approved queries, learned signals and conversational history persisted beyond a single thread.",
          notes: "Vision component — the Databricks Genie client exists, but LakeBase long-term memory is not yet wired.",
        },
      },
    ],
  },
  {
    id: "agentic",
    title: "Agentic Layer",
    zone: "backend",
    blurb: "A supervisor deep-agent fans out to specialist agents. The DRG agent owns the 22-tool analysis suite and a human-in-the-loop Text2SQL path.",
    nodes: [
      {
        id: "context-agent",
        label: "Context Agent",
        tagline: "Deep web + CMS research",
        icon: "search",
        status: "live",
        relatedIds: ["cms-data"],
        detail: {
          summary:
            "Pulls the latest authoritative context: answers CMS/MS-DRG reference questions from the ingested IPPS data and runs live web research to surface the newest CMS rule changes and news.",
          responsibilities: [
            "Answer MS-DRG / CC-MCC / IPPS reference questions from CMS data",
            "Web-search the latest CMS Final Rule changes & news",
            "Keep the platform current with the newest published data",
          ],
          tools: [
            { name: "8 CMS reference tools", status: "live" },
            { name: "web_search (DuckDuckGo)", status: "live" },
          ],
          notes: "Live — backend/app/subagents/context_agent.py + search_agent.py.",
        },
      },
      {
        id: "drg-agent",
        label: "DRG Agent",
        tagline: "900+ DRG families · trends · shift · upcoding",
        icon: "agent",
        status: "stage1",
        hint: "2 sub-agents · 22 tools",
        relatedIds: [
          "claims",
          "cms-data",
          "procedural-memory",
          "tools-22",
          "report-agent",
          "text2sql",
        ],
        detail: {
          summary:
            "The analytical core. Across 900+ DRG families it surfaces DRG trends, provider-opportunity benchmarking, the top ICD trend in each DRG family, DRG-shift identification (no CC/MCC → CC → MCC) and upcoding signals. Governed by skills.md (tool logic) and agents.md (overall architecture).",
          responsibilities: [
            "DRG trend analysis across 900+ families",
            "Provider-opportunity benchmarking",
            "Top-ICD trend per DRG family",
            "DRG shift identification (no CC/MCC → CC → MCC)",
            "Upcoding / super-outlier detection",
          ],
          subAgents: [
            {
              name: "Analysis subagent → Report-Generation agent",
              status: "planned",
              detail:
                "Runs the 22-tool suite (Shift-Score, Provider-Similarity, Claim-Similarity, Top-ICD-Shift, Upcoding-Detect, …) and hands the findings to a Report-Generation agent. If the report is missing anything, the two agents interact until it is complete. 3 tools exist as Stage-1 mocks today; the full suite + report agent are planned.",
            },
            {
              name: "Text2SQL subagent (human-in-the-loop)",
              status: "live",
              detail:
                "For unknown / ad-hoc questions it writes a SQL query, a human approves or edits it, and once approved the result is stored back to DuckDB + LakeBase for reuse. Approved queries can be registered as new tools from the frontend.",
            },
          ],
          governance: ["skills.md — tool logic & architecture", "agents.md — overall architecture"],
          notes:
            "Stage-1 — backend/app/subagents/drg_agent.py runs mock tools with an optional Databricks Genie path.",
        },
      },
      {
        id: "tools-22",
        label: "22-Tool Suite",
        tagline: "Shift-Score · Similarity · Top-ICD · Upcoding…",
        icon: "tool",
        status: "planned",
        relatedIds: ["drg-agent", "report-agent", "provider-similarity"],
        detail: {
          summary:
            "The DRG agent's analytical toolbox — 22 specialized tools whose outputs feed the Report-Generation agent.",
          tools: [
            { name: "Shift-Score Identification", status: "stage1" },
            { name: "Provider Similarity", status: "planned" },
            { name: "Claim Similarity", status: "planned" },
            { name: "Top-ICD-Shift", status: "stage1" },
            { name: "Provider Utilization", status: "stage1" },
            { name: "Upcoding Detection", status: "planned" },
            { name: "Provider-Opportunity Benchmark", status: "planned" },
            { name: "DRG Trend", status: "planned" },
            { name: "… +14 more", status: "planned" },
          ],
          notes:
            "3 tools exist as Stage-1 mocks (drg_shift_lookup, icd_driver_lookup, provider_utilization_lookup); the remaining 19 are planned.",
        },
      },
      {
        id: "report-agent",
        label: "Report-Generation Agent",
        tagline: "Assembles findings into a report",
        icon: "report",
        status: "planned",
        relatedIds: ["drg-agent", "tools-22"],
        detail: {
          summary:
            "Consumes the 22-tool suite's output and assembles a complete report. If anything is missing it loops back to the analysis subagent until the report is whole.",
          notes: "Vision component — not yet implemented.",
        },
      },
      {
        id: "text2sql",
        label: "Text2SQL Agent",
        tagline: "Ad-hoc SQL · human approve / edit",
        icon: "sql",
        status: "live",
        hint: "human-in-the-loop",
        relatedIds: ["drg-agent", "in-memory", "long-term-memory"],
        detail: {
          summary:
            "The DRG agent's second path. For unknown ad-hoc queries it generates SQL, pauses for a human to approve or edit, then executes. Approved SQL is cached to DuckDB + LakeBase and can be registered as a reusable tool from the frontend.",
          responsibilities: [
            "Generate candidate SQL for ad-hoc questions",
            "Pause for human approve / edit (HITL interrupt)",
            "Execute approved SQL on Databricks Genie",
            "Cache approved query → store to DuckDB + LakeBase",
            "Let users register an approved query as a tool",
          ],
          tools: [
            { name: "run_saved_sql", status: "live" },
            { name: "genie_generate_sql", status: "live" },
            { name: "execute_sql (pauses for approval)", status: "live" },
            { name: "register approved query as tool", status: "planned" },
          ],
          notes:
            "Live — backend/app/subagents/data_agent.py + backend/app/genie/hitl_tools.py implement the approval workflow.",
        },
      },
      {
        id: "callcenter-agent",
        label: "Call Center Agent",
        tagline: "Guards call-center operations",
        icon: "shield",
        status: "stage1",
        relatedIds: ["callcenter-data"],
        detail: {
          summary:
            "Specialist that guards call-center operations — answers volume, top-reason, handle-time and complaint questions.",
          notes: "Stage-1 stub on a mock tool — backend/app/subagents/callcenter_agent.py; awaits a Genie space.",
        },
      },
      {
        id: "appeals-agent",
        label: "Appeals Agent",
        tagline: "Guards appeals",
        icon: "shield",
        status: "stage1",
        relatedIds: ["appeals-data"],
        detail: {
          summary:
            "Specialist that guards appeals — answers status, volume, overturn/upheld-rate, reason and timeline questions.",
          notes: "Stage-1 stub on a mock tool — backend/app/subagents/appeals_agent.py; awaits a Genie space.",
        },
      },
    ],
  },
  {
    id: "observation",
    title: "Observation / Signal Layer",
    zone: "frontend",
    blurb: "The surfaced layer (frontend): validate the business signals, capture feedback, and feed it back so the agents regenerate improved signals.",
    nodes: [
      {
        id: "business-validation",
        label: "Business Validation",
        tagline: "Validate signals against business reality",
        icon: "signal",
        status: "planned",
        detail: {
          summary:
            "Reviewers validate the agents' signals against business reality before they are acted on — the human checkpoint of the loop.",
          notes: "Vision component — surfaced in the frontend; not yet implemented.",
        },
      },
      {
        id: "feedback-loop",
        label: "Feedback Loop",
        tagline: "Capture corrections & approvals",
        icon: "signal",
        status: "planned",
        relatedIds: ["feedback-store", "drg-agent"],
        detail: {
          summary:
            "Captures reviewer corrections and approvals and routes them to the feedback store, closing the loop back to the Agentic layer.",
          notes: "Vision component — not yet implemented.",
        },
      },
      {
        id: "feedback-store",
        label: "Feedback Store (DB)",
        tagline: "Persisted feedback for regeneration",
        icon: "database",
        status: "planned",
        relatedIds: ["feedback-loop", "drg-agent"],
        detail: {
          summary:
            "Durable store of feedback. The Agentic layer reads from it and regenerates signals with improvement — the platform's learning flywheel.",
          notes: "Vision component — not yet implemented.",
        },
      },
    ],
  },
];

/* Flat id → node lookup for the detail panel and related-node highlighting. */
export const NODE_BY_ID: Record<string, ArchNode> = Object.fromEntries(
  LAYERS.flatMap((layer) => layer.nodes).map((node) => [node.id, node])
);
