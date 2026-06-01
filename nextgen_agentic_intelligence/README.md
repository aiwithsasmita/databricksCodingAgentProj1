# NextGen Agentic Intelligence

> UnitedHealthcare · powered by Optum

A UnitedHealthcare / Optum healthcare-analytics platform built on LangChain
**`deepagents`**. A **supervisor deep agent** (GPT‑5.5) routes questions to
specialized subagents, served to a **Next.js** chat UI with **voice input**, a
**human-in-the-loop SQL** approval flow, and a **"Show flow"** execution diagram.

> The header recreates the UnitedHealthcare nested-U mark as a clean SVG
> (`frontend/public/uhc-mark.svg`) — swap in the official vector at that path when
> you have it.

> **Stage 1** delivers the working architecture end-to-end with the four
> subagents **stubbed** (correct routing, illustrative mock data). Later stages
> swap the stubs for live **Databricks Genie** tools, the real clinical-evidence
> skill, and an Excel-backed CMS context agent.

## Architecture

```
                       ┌─────────────────────────────┐
   user (text/voice) → │  Next.js chat UI (frontend)  │
                       └──────────────┬──────────────┘
                                      │ SSE  /api/chat
                       ┌──────────────▼──────────────┐
                       │  FastAPI (backend)          │
                       │  Supervisor DEEP AGENT       │  ← GPT-5.5
                       │  (deepagents + LangGraph)    │
                       │  plans · files · `task` tool │
                       └───┬────────┬────────┬────────┘
            task delegates │        │        │        │
                ┌──────────▼─┐ ┌────▼─────┐ ┌▼────────┐ ┌▼──────────┐
                │ drg-agent  │ │ appeals  │ │callcenter│ │ context   │
                │ +skill+3   │ │  -agent  │ │  -agent  │ │  -agent   │
                │ mock tools │ │          │ │          │ │ (CMS ref) │
                └────────────┘ └──────────┘ └──────────┘ └───────────┘
```

- **Supervisor**: built with `create_deep_agent(model, system_prompt, subagents=[…])`.
  Gets planning (`write_todos`), a virtual filesystem, and the `task` tool that
  spawns subagents in isolated context — all from `deepagents`. A `MemorySaver`
  checkpointer gives per-`thread_id` conversation memory.
- **drg-agent**: shift analysis (no CC/MCC → CC → MCC, national + statewise),
  ICD drivers, **clinical-evidence skill** (`backend/skills/drg_clinical_evidence/SKILL.md`),
  and provider/TIN super-outlier detection. Uses live **Databricks Genie** tools
  when configured (Stage 2), else 3 mock tools.
- **appeals-agent / callcenter-agent / context-agent**: stubbed specialists.
- **data-agent**: general Databricks **Genie** Q&A — appears when any `agent:"data"`
  space is configured (Stage 2). Routes ad-hoc data questions to live SQL.
- **search-agent**: free **DuckDuckGo** web search (no API key) for current
  events / external facts — `backend/app/tools/search_tools.py`.
- **Voice**: browser Web Speech API (no extra model) → GPT‑5.5 stays the only LLM.

## Repository layout

```
backend/    FastAPI + deepagents supervisor agent (Python)
frontend/   Next.js 14 chat UI (TypeScript, Tailwind)
```

See [the plan](#) and inline `# STAGE-1 MOCK` markers for what becomes real later.

## Prerequisites

- Python 3.11+ (tested on 3.14)
- Node.js 18+
- An OpenAI API key with access to the configured `MODEL` (default `gpt-5.5`)

## Run the backend

```powershell
cd backend
# One-shot: creates venv, installs deps, copies .env, starts the API
./run.ps1
```

Or manually:

```powershell
cd backend
python -m venv .venv
./.venv/Scripts/Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env   # then set a real OPENAI_API_KEY
uvicorn app.main:app --reload --port 8000
```

Health check: <http://localhost:8000/api/health> → `{"status":"ok","model":"gpt-5.5"}`

Smoke test (no API calls — verifies wiring):

```powershell
cd backend
./.venv/Scripts/python.exe tests/test_smoke.py
```

## Run the frontend

```powershell
cd frontend
npm install
Copy-Item .env.local.example .env.local   # NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

Open <http://localhost:3000>.

## Configuration

| Where | Var | Purpose |
| ----- | --- | ------- |
| `backend/.env` | `OPENAI_API_KEY` | OpenAI key (**fake placeholder by default**) |
| `backend/.env` | `MODEL` | LLM id, default `gpt-5.5` (change if your account differs) |
| `backend/.env` | `FRONTEND_ORIGIN` | CORS origin for the UI |
| `frontend/.env.local` | `NEXT_PUBLIC_API_URL` | Backend base URL |

> **`gpt-5.5`**: if you get `model_not_found`, set `MODEL` to a model your key can
> access. Sampling params are left default to avoid GPT‑5-family 400s.

## Try it

- *"Is DRG 871 (Septicemia) shifting toward MCC since 2023?"* → **drg-agent**
- *"Which MS-DRGs did CMS add in 2026?"* → **context-agent**
- *"What's our appeals overturn rate this year?"* → **appeals-agent**
- *"Top call-center reasons in the last 30 days?"* → **callcenter-agent**
- Tap the mic (Chrome/Edge) and speak any of the above.

## Security note

`backend/.env` holds secrets and is **git-ignored**. If you pasted a key in
plaintext anywhere, rotate it.

## Stage 2 — Databricks Genie (live data)

The DRG agent can query real data through the **Databricks Genie Conversation
API**. Each configured Genie space becomes its own tool (`genie_<name>`) that the
agent calls with a natural-language question; it returns the **generated SQL plus
result rows** as JSON. With no credentials configured, the DRG agent automatically
falls back to the Stage-1 mock tools, so the app always runs.

**Code:** [app/genie/client.py](backend/app/genie/client.py) (API wrapper),
[registry.py](backend/app/genie/registry.py) (space registry),
[tools.py](backend/app/genie/tools.py) (per-space tool factory), wired in
[subagents/drg_agent.py](backend/app/subagents/drg_agent.py).

**Configure (Azure, PAT auth)** in `backend/.env`:

```
DATABRICKS_HOST=https://adb-XXXXXXXXXXXX.azuredatabricks.net
DATABRICKS_TOKEN=dapiXXXXXXXX
# One entry per Genie space (single-line JSON). name -> tool genie_<name>.
GENIE_SPACES=[{"name":"drg_shift","space_id":"01ef...","agent":"drg","description":"DRG severity tier mix and coding shift by fiscal year, US and statewise."},{"name":"drg_providers","space_id":"01ef...","agent":"drg","description":"Provider/TIN-level utilization of DRG severity codes with state and national benchmarks."}]
```

**Verify the live connection** (run on a machine with network access to the
workspace — VPN/PrivateLink as needed):

```powershell
cd backend
./.venv/Scripts/python.exe scripts/genie_smoke.py <SPACE_ID> "How many DRG 871 cases by fiscal year?"
```

It prints the status, generated SQL, columns, and rows — confirming auth + space
ID + extraction before you wire it into the agent.

**Notes**
- Auth is PAT (`DATABRICKS_HOST`/`DATABRICKS_TOKEN`); the SDK also accepts CLI
  profiles / OAuth if you leave these blank.
- Results return inline (`data_array`) for normal sizes; very large results use
  presigned `EXTERNAL_LINKS` — the client flags this and asks you to aggregate.
- Genie free-tier throughput is ~5 questions/min/workspace; each tool call starts
  a fresh conversation (recommended for accuracy).

## Stage 3 — Human-in-the-loop SQL (data-agent)

The generic **data-agent** (backed by the NYC-taxi Genie space) generates SQL,
then **pauses for human approval** before running it — using deepagents'
`interrupt_on` middleware. The chat shows an **editable SQL card**: Approve & Run,
Run Edited, or Reject. Approved/edited queries are **saved** so the same question
later runs instantly with **no approval**.

Flow ([backend/app/genie/hitl_tools.py](backend/app/genie/hitl_tools.py),
[data_agent.py](backend/app/subagents/data_agent.py)):

```
ad-hoc data Q → run_saved_sql(q)   → cached approved SQL? run directly (no HITL)
              → genie_generate_sql(q) → Genie proposes SQL
              → execute_sql(sql, q)   → INTERRUPT: approve / edit / reject
                                        approve → run proposed · edit → run yours · reject → skip
              → on success → save {q → SQL}  ⇒ next time no HITL
```

**Protocol:** `/api/chat` streams tokens and, if the run pauses, ends with an
`interrupt` SSE event carrying the SQL. The UI shows
[SqlApprovalCard](frontend/components/SqlApprovalCard.tsx); the decision is sent
to **`/api/resume`** which resumes the graph with
`Command(resume={"decisions":[…]})` ([main.py](backend/app/main.py)). Approved SQL
runs via the Databricks SQL Statement Execution API on the space's warehouse
(auto-resolved, or set `GENIE_WAREHOUSE_ID`).

**Validate it** (live, no UI):

```powershell
cd backend
./.venv/Scripts/python.exe scripts/hitl_smoke.py approve
./.venv/Scripts/python.exe scripts/hitl_smoke.py edit "SELECT ROUND(SUM(fare_amount),2) AS total FROM samples.nyctaxi.trips"
./.venv/Scripts/python.exe scripts/hitl_smoke.py reject
./.venv/Scripts/python.exe scripts/hitl_smoke.py repeat   # saved query → no approval
```

Approved queries persist in `backend/data/saved_queries.json` (git-ignored).
Delete it to reset the "saved tools".

## Flow visualization ("Show flow")

Every answer carries a **Mermaid flow diagram** of how it was produced — which
specialist it routed to, the tools it called, the generated SQL, the human
approve/edit/reject decision, and the result. Each assistant message has a
**"Show flow"** button that renders it.

How it's captured ([backend/app/trace.py](backend/app/trace.py)): a LangChain
callback handler (`TraceCollector`) records each tool/agent step as the graph
runs (callbacks propagate into subagents, so inner steps are captured too).
Built-in housekeeping tools (`ls`, `write_todos`, …) are filtered out. The steps
are turned into a Mermaid `flowchart` and sent as a final **`trace`** SSE event;
[FlowDiagram.tsx](frontend/components/FlowDiagram.tsx) renders it with mermaid.js
(themed to the UHC/Optum palette, with a raw-code fallback).

## CMS Context Agent (real CMS data, FY2023–FY2026)

The **context‑agent** answers CMS/MS‑DRG reference questions from the **official
CMS IPPS Final Rule files** (public‑domain U.S. government data), ingested for
**FY2023–FY2026** (MS‑DRG v40–v43):

- **Full MS‑DRG catalog** (~770 DRGs/year) — code, title, MDC, MED/SURG, severity
  tier, relative weight, mean LOS (from **Table 5**).
- **Change log** — DRGs added / deleted / retitled each year (auto‑derived by
  diffing consecutive years).
- **IPPS rule highlights + provider payment factors** — CMS rule id, payment
  update %, effective date, wage index, DSH/uncompensated care, NTAP, quality
  programs (verified per‑year).
- **ICD‑10 update counts for all four years** (new/invalid diagnosis & procedure
  codes, revised titles, MCC/CC list sizes + additions/deletions — from **Tables
  6**), plus **per‑year MCC/CC change lists** and the complete current (FY2026)
  MCC (3,354) and CC (15,078) lists for the status lookup.

**Code:** ingestion `backend/scripts/ingest_cms.py`; loader
[app/cms_store.py](backend/app/cms_store.py); 8 tools in
[app/tools/cms_tools.py](backend/app/tools/cms_tools.py) (`cms_drg_lookup`,
`cms_drg_changes`, `cms_ipps_rule`, `cms_search_drgs`, `cms_compare_drg`,
`cms_cc_mcc`, `cms_icd10_updates`, `cms_cc_mcc_changes`); wired in
[subagents/context_agent.py](backend/app/subagents/context_agent.py).

**Rebuild the datasets** (downloads the official CMS Table 5 + Tables 6 ZIPs and
parses them into `backend/data/cms/*.json`):

```powershell
cd backend
./.venv/Scripts/python.exe scripts/ingest_cms.py
```

**Ask it:** *"Which MS‑DRGs did CMS add/delete in FY2026?"*, *"What is DRG 209?"*,
*"What's the FY2026 payment update and provider payment changes?"*, *"What changed
for DRG 871 since 2023?"*, *"Is ICD‑10 R65.20 a CC or MCC?"*, *"How many new ICD‑10
codes in FY2026?"* — answers cite the CMS rule id and effective date.

> Data files under `backend/data/cms/` are git‑ignored (regenerate with the
> ingestion script). All sourced from public‑domain CMS publications.

## Roadmap (next stages)

1. ~~**DRG agent → Databricks Genie**~~ ✅ Stage 2 (this) — multiple Genie spaces as
   tools, with mock fallback. Next: implement the full shift / ICD-driver / outlier
   *analytics* on top of the live data, and add more spaces.
2. **Clinical-evidence skill**: fill `SKILL.md` with validated criteria + data tools.
3. **Context agent**: back `cms_context_lookup` with the local CMS Excel
   (`pandas`/`openpyxl`).
4. **Appeals / Call-center**: add their Genie spaces to `GENIE_SPACES` with
   `"agent":"appeals"` / `"agent":"callcenter"` and wire `genie_tools_for(...)`
   into those subagents (same pattern as the DRG agent).
5. **HITL**: add `interrupt_on` for expensive queries (approve before running).
```
