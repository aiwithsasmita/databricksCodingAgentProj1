/* Business-facing content for the architecture page: the objective banner and
 * each agent's use cases + maturity. Kept separate from the runtime flow spec
 * (flow.ts). Copy style: formal, no contractions, no hyphenated compounds. */
import type { IconName } from "@/lib/architecture";

export type Maturity = "mature" | "progress";

export const MATURITY_LABEL: Record<Maturity, string> = {
  mature: "Mature · Live",
  progress: "In Progress · Stage",
};
export const MATURITY_STYLE: Record<Maturity, { dot: string; chip: string }> = {
  mature: { dot: "bg-emerald-500", chip: "bg-emerald-50 text-emerald-700 ring-emerald-200" },
  progress: { dot: "bg-amber-500", chip: "bg-amber-50 text-amber-700 ring-amber-200" },
};

export const OBJECTIVE = {
  headline: "Agentic Intelligence Layer",
  lead:
    "Surfacing DRG trends, severity shifts and upcoding; tracking appeals and denial trends; reading call center calls for intent and sentiment to lift the provider experience; researching new CMS guideline changes and modeling their impact on Claims and Appeals; pinpointing the geographies where DRG utilization runs hot and recommending the new geos or providers whose behavior is drifting toward the ones we have already flagged; and designing control and treatment groups for any experiment.",
  body:
    "They are autonomous and always on, continuously monitoring and analyzing Call Center, Appeals and Claims data to surface high value signals on their own. We have fed them deep business knowledge so they read healthcare data and coding logic the way our experts do. When the business responds to a signal from the frontend, the agents take that feedback, work on it, and regenerate the signal, getting sharper with every loop.",
  highlights: [
    { title: "Fed with business knowledge", text: "Grounded in our healthcare data and coding logic, so they reason like domain experts." },
    { title: "Self sufficient to new logic", text: "In an ever changing world, creators simply describe the new logic and the agents absorb it and put it to work, with no rebuild needed." },
    { title: "Writes code on the fly", text: "For new logic an agent writes the code, asks for human feedback, refines, executes, and publishes the result." },
    { title: "Explainable and reliable", text: "Every agent shows its work, exactly how it reached the final result." },
    { title: "Human approved by design", text: "For any new ad hoc question, nothing executes until a human approves." },
  ],
  stat: { value: "$22M+", label: "in savings opportunities surfaced to date" },
};

export interface AgentCard {
  id: string;
  name: string;
  tagline: string;
  icon: IconName;
  maturity: Maturity;
  useCases: string[];
}

export const AGENT_CARDS: AgentCard[] = [
  {
    id: "drg",
    name: "DRG Agent",
    tagline: "Coding shift, upcoding and provider opportunity",
    icon: "agent",
    maturity: "mature",
    useCases: [
      "DRG trend analysis across 900+ DRG families",
      "Upcoding and super outlier detection",
      "Provider opportunity benchmarking",
      "DRG severity shift identification (no CC/MCC → CC → MCC)",
      "Top ICD trend within each DRG family",
      "Geographic hotspots where DRG utilization runs high",
    ],
  },
  {
    id: "websearch",
    name: "WebResearch Agent",
    tagline: "External change intelligence",
    icon: "search",
    maturity: "mature",
    useCases: [
      "Trend analytics for new DRG, ICD and CPT codes",
      "New policy and CMS rule change intelligence",
      "New DRG relative weight and provider Case Mix Index shifts",
      "Tracks the downstream impact of these changes on Claims and Appeals and shares the signal",
    ],
  },
  {
    id: "callcenter",
    name: "Call Center Agent",
    tagline: "Voice of member and provider intelligence",
    icon: "signal",
    maturity: "progress",
    useCases: [
      "Reads the intent of every member and provider call",
      "Overall sentiment by call category",
      "Early signals on emerging trends: new drug queries, new procedure queries, churning providers",
      "Lifts the overall provider and member experience",
    ],
  },
  {
    id: "appeals",
    name: "Appeals Agent",
    tagline: "Spend and denial foresight",
    icon: "shield",
    maturity: "progress",
    useCases: [
      "Predicts incremental or avoidable spend",
      "Appeals volume and denial trend signals",
      "Overturn rate and appeal reason analysis",
    ],
  },
  {
    id: "provider-similarity",
    name: "Provider Similarity Agent",
    tagline: "True peer benchmarking",
    icon: "embedding",
    maturity: "mature",
    useCases: [
      "Benchmarks each provider only against true peers: same organization type, geography, taxonomy, contract and network",
      "Compares operational efficiency across the peer set",
      "Flags providers whose behavior is drifting toward already flagged outliers",
      "Recommends the new geos or providers likely to show the same pattern next",
    ],
  },
  {
    id: "referral-network",
    name: "Referral Network Agent",
    tagline: "Referral patterns and network integrity",
    icon: "embedding",
    maturity: "progress",
    useCases: [
      "Maps how providers refer to one another and where care actually flows",
      "Detects leakage and inappropriate out of network steering",
      "Surfaces referral hotspots and recommends high value in network paths",
      "Network integrity and continuity of care signals",
    ],
  },
  {
    id: "claim-similarity",
    name: "Claim Similarity Agent",
    tagline: "Similar claim cohorts for fair analysis",
    icon: "tool",
    maturity: "progress",
    useCases: [
      "Builds control and treatment cohorts from similar claims: same member risk, age, plan, ICD or diagnostic",
      "Explains why similar members get different treatment plans across providers",
      "Identifies geo hotspots where a cohort utilization runs high",
      "Powers fair, apples to apples provider comparison",
    ],
  },
];
