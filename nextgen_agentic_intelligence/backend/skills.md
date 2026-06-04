# skills.md — NextGen Agentic Intelligence

> The operating manual for the agent fleet: the **DeepAgent runtime**, how the
> supervisor **delegates**, every **subagent**, the **tool logic**, the **skills**
> and **hooks**, and the **memory / data / governance / observability** layers.
>
> `agents.md` holds the high-level architecture narrative; **this file holds the
> tool logic and the runtime contract** the DRG agent and its peers follow.
>
> Status legend: 🟢 **Live** · 🟡 **Stage 1** (stub / mock, real data pending) ·
> ⚪ **Planned** (vision, not yet built).

---

## 1. Mental model — the layered agentic platform

Read bottom-to-top; a request flows up and signals flow back down.

```
Observation / Signal      validate signals · capture feedback · regenerate   (frontend)
        ▲ feedback loop
Agentic Layer             Supervisor DeepAgent → specialist agents → subagents → report
        ▲
Memory Layer              In-memory (DuckDB) · Procedural (skills) · Long-term (LakeBase)
        ▲
Context Layer             CMS reference · embeddings · clusters · similarity tables
        ▲
Data Layer                Claims · Appeals · NDB Provider · Network · Member · Call-Center
```

Cross-cutting rails span every layer:

- **Observability — MLflow** ⚪: a trace, eval and metric for every agent step.
- **Data Governance — Databricks Unity Catalog** ⚪: lineage, access control, audit.

---

## 2. The DeepAgent runtime (LangChain `deepagents` + LangGraph)

The supervisor and each subagent are **deep agents** built with
`deepagents.create_deep_agent` (see `backend/app/agent.py`). A deep agent is a
compiled LangGraph graph with five built-in capabilities:

| Capability | What it is | In this codebase |
|---|---|---|
| **Planner** | `write_todos` — the agent decomposes the task into a todo list and works it | 🟢 supervisor plans every request |
| **Virtual filesystem** | scratch "files" the agent reads/writes as working memory | 🟢 built-in to deepagents |
| **Memory** | `MemorySaver` checkpointer → per-thread conversation memory | 🟢 `agent.py` (falls back gracefully on older builds) |
| **Skills** | folders of Markdown decision logic loaded into a subagent | 🟢 DRG agent loads `drg_clinical_evidence` |
| **Delegation** | the built-in **`task`** tool hands a self-contained instruction to a named subagent | 🟢 supervisor routes via `task` |
| **Hooks** | pre/post-model and pre/post-tool interception points | see §7 |

**Model:** OpenAI **GPT-5.5** (`backend/app/config.py`, `MODEL`). GPT-5-family
sampling params are left at defaults to avoid 400s.

---

## 3. Supervisor — plan & route

`SUPERVISOR_PROMPT` (`backend/app/prompts.py`). The supervisor **never answers
specialist questions itself** — it plans with todos, then delegates with `task`.

**Routing table:**

| Intent | Route to | Status |
|---|---|---|
| DRG coding shift / migration, ICD drivers, provider outliers, upcoding | `drg-agent` | 🟡 |
| Appeals — status, volumes, overturn rates, reasons, timelines | `appeals-agent` | 🟡 |
| Call-center — volumes, reasons, handle time, complaints | `callcenter-agent` | 🟡 |
| CMS reference — DRG added/deleted/recoded, IPPS rules, CC/MCC | `context-agent` | 🟢 |
| Public-web facts — current events, latest CMS rule changes, news | `search-agent` | 🟢 |
| Ad-hoc data/analytics over connected Databricks datasets | `data-agent` (Text2SQL) | 🟢 (only when a Genie space is configured) |

When delegating it passes the DRG family / code / state / year-range / TIN the
user mentioned, then summarizes the specialist's findings and **names the
specialist** that produced the answer.

---

## 4. Subagents

| Subagent | Role | Tools | Status |
|---|---|---|---|
| **drg-agent** | DRG shift analyst across FY2023→2026 (no CC/MCC → CC → MCC) | mock trio **or** live Genie tools; loads the clinical-evidence Skill | 🟡 |
| **context-agent** | CMS / MS-DRG reference from ingested IPPS Final Rule data | 8 CMS tools (§6.1) | 🟢 |
| **search-agent** | Free DuckDuckGo web research, always cites URLs | `web_search` | 🟢 |
| **appeals-agent** | Guards appeals questions | `appeals_lookup` (mock) | 🟡 |
| **callcenter-agent** | Guards call-center questions | `callcenter_lookup` (mock) | 🟡 |
| **data-agent** | Ad-hoc Text2SQL with human-in-the-loop approval | `run_saved_sql`, `genie_generate_sql`, `execute_sql` | 🟢 |

Subagents are assembled **lazily at agent-construction time** (`agent.py
_build_subagents`) so runtime Genie config decides live-vs-mock tools and whether
the data-agent is offered at all.

### 4.1 DRG agent — the two sub-paths

`DRG_AGENT_PROMPT` + a DATA SOURCE note (`backend/app/subagents/drg_agent.py`).
Workflow: tier mix by FY → ICD drivers of MCC migration → **clinical-evidence
verdict** (via Skill) → if no evidence, find high-utilizing TINs and flag
**super-outliers** → summarize with concrete numbers. It fans into two paths:

- **Path 1 — Analysis subagent → Report Generation** ⚪
  Runs the **22-tool suite** (§6.4). Output is handed to a **Report-Generation
  agent**; if the report is missing anything the two interact until it is whole.
  *Today:* 3 of the 22 exist as Stage-1 mocks.

- **Path 2 — Text2SQL subagent (human-in-the-loop)** 🟢
  For unknown ad-hoc questions it generates SQL, **pauses for a human to approve
  or edit**, executes on Databricks Genie, and caches the approved SQL to
  **DuckDB + LakeBase** for instant reuse. Approved queries can be **registered as
  a new tool from the frontend** ⚪.

---

## 5. Agent delegation contract

1. Supervisor receives the user turn, plans with `write_todos`.
2. Supervisor calls **`task(subagent_name, instruction)`** — a self-contained
   instruction (carries DRG family/code, state, FY range, TIN).
3. The subagent runs its own deep-agent loop with **only its own tools + skills**.
4. The subagent returns a concise, structured result.
5. Supervisor summarizes for the user and labels the producing specialist and
   whether figures are **live** or **illustrative mock**.

A subagent **never** calls another subagent; only the supervisor delegates.

---

## 6. Tool catalog & logic

### 6.1 CMS reference tools 🟢 — `backend/app/tools/cms_tools.py`
Real data, FY2023–FY2026, ingested from the CMS IPPS Final Rule files.

| Tool | Logic |
|---|---|
| `cms_drg_lookup(drg, fy)` | DRG title, MDC, MED/SURG, severity tier, relative weight, mean LOS, change history |
| `cms_drg_changes(fy, change_type)` | which MS-DRGs were added / deleted / retitled in a year |
| `cms_ipps_rule(fy)` | IPPS Final Rule: rule id, effective date, payment update %, provider factors (wage index, DSH, NTAP, quality) |
| `cms_search_drgs(query, fy)` | keyword search over DRG titles |
| `cms_compare_drg(drg, fy1, fy2)` | what changed for a DRG between two years |
| `cms_cc_mcc(icd10)` | is an ICD-10 code an MCC, CC, or neither (FY2026 lists) |
| `cms_icd10_updates(fy)` | counts of new/invalid ICD-10 codes and CC/MCC list changes |
| `cms_cc_mcc_changes(fy)` | exact codes added/deleted from the MCC and CC lists |

### 6.2 Web search 🟢 — `backend/app/tools/search_tools.py`
`web_search(query)` — DuckDuckGo with retry; returns title/url/snippet; the agent
synthesizes and **always cites URLs**.

### 6.3 Human-in-the-loop SQL 🟢 — `backend/app/genie/hitl_tools.py`
Exact order the data-agent must follow:

1. **`run_saved_sql(question)`** — if a human previously approved this question
   (`saved: true`), present results and STOP (no re-approval).
2. **`genie_generate_sql(question)`** — Genie proposes candidate SQL.
3. **`execute_sql(sql, question)`** — **pauses** for the human:
   - *approve / edit* → the (possibly edited) SQL runs, rows return, the SQL is
     saved for instant reuse;
   - *reject* → not run; ask how to adjust. Never retry unprompted.

Live Genie tools (`genie_<space>(question)`) are generated **one per configured
Genie space** (`backend/app/genie/tools.py`, `registry.py`).

### 6.4 DRG 22-tool analysis suite
The analysis subagent's toolbox. 🟡 = Stage-1 mock exists, ⚪ = planned.

`drg_shift_lookup` 🟡 · `icd_driver_lookup` 🟡 · `provider_utilization_lookup` 🟡 ·
Shift-Score Identification ⚪ · Provider Similarity ⚪ · Claim Similarity ⚪ ·
Top-ICD-Shift ⚪ · Upcoding Detection ⚪ · Provider-Opportunity Benchmark ⚪ ·
DRG Trend ⚪ · DRG-Family Roll-up ⚪ · Peer-Group Normalization ⚪ · …(to 22) ⚪

> Mock tools live in `backend/app/tools/mock_tools.py` and are clearly labelled
> illustrative until swapped for live Genie/Spark tools.

---

## 7. Skills & Hooks

### Skills (procedural memory) 🟡
A **Skill** is a folder of Markdown decision logic loaded into a subagent via the
deepagents `skills` argument. Today: **`backend/skills/drg_clinical_evidence/SKILL.md`**,
loaded by the DRG agent.

`drg_clinical_evidence` decision logic:
1. Look for corroborating clinical signals for an upward severity shift.
2. **Verdict rule:** evidence present → shift is justified; evidence absent →
   escalate.
3. **Escalation:** when no evidence, run provider-outlier analysis and flag
   super-outliers.
4. Output: shift → ICD drivers → clinical verdict → super-outliers (if escalated).

> Stage-1 rules are placeholders to be replaced with validated criteria + real
> corroborating-data tools.

**Authoring a new skill:** create `backend/skills/<name>/SKILL.md` with the
decision steps + output contract, then add `str(<dir>)` to the subagent's
`"skills": [...]`.

### Hooks ⚪
Deep-agent **hooks** are interception points around the model/tool loop. Planned
uses:

| Hook | Purpose |
|---|---|
| `pre_tool` | redact PHI, enforce Unity Catalog access before a tool runs |
| `post_tool` | log tool I/O to MLflow, attach lineage |
| `human_interrupt` | the SQL approval pause in `execute_sql` (already a HITL gate) |
| `pre_model` / `post_model` | inject context, run guardrail/eval checks on the answer |
| `on_feedback` | when Observation writes feedback, trigger signal regeneration |

---

## 8. Memory, data, governance, observability

- **In-memory · DuckDB** 🟡 — fast working state + approved-SQL cache. *Today:*
  `MemorySaver` + `backend/data/saved_queries.json`; DuckDB-backed store planned.
- **Long-term · Databricks LakeBase** ⚪ — durable approved queries, learned
  signals, history beyond a thread.
- **Live SQL · Databricks Genie** 🟡 — `backend/app/genie/` client + registry;
  activates when a space is configured.
- **CMS Data** 🟢 — `backend/data/cms/` (catalog, CC/MCC lists, ICD updates, rules).
- **Observability · MLflow** ⚪ — traces, evals, metrics on every step.
- **Governance · Databricks Unity Catalog** ⚪ — lineage, access control, audit.

---

## 9. The feedback flywheel (Observation / Signal)

The frontend Observation layer lets reviewers **validate** signals and capture
**feedback**, which is persisted. The agentic layer reads that feedback (via the
`on_feedback` hook) and **regenerates improved signals** — the platform's
learning loop. ⚪

---

## 10. Where things live

```
backend/app/agent.py            supervisor deep agent (planner, memory, delegation)
backend/app/prompts.py          SUPERVISOR_PROMPT + every subagent prompt
backend/app/subagents/          drg / context / search / appeals / callcenter / data agents
backend/app/tools/              cms_tools.py · mock_tools.py · search_tools.py
backend/app/genie/              client.py · registry.py · tools.py · hitl_tools.py
backend/skills/<name>/SKILL.md  procedural-memory skills (clinical-evidence today)
backend/data/cms/               ingested CMS reference data
frontend/app/architecture/      this architecture, rendered as an interactive flow
```
