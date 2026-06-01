# DRG Claims Analysis Agent

A **healthcare data analyst agent** for MS-DRG claims: query Databricks claims data with **Genie (NL→SQL)**, run **CMS-aligned** coding checks (ICD-10, CC/MCC, MCE, new PCS codes), and produce audit-style reports. Built with **DeepAgents** (planning, skills, sub-agents) and a **Streamlit** chat UI.

> **Disclaimer:** The bundled sample data and tools support **coding/billing review and education**, not clinical decisions. Use of real PHI must follow your organization’s policies and applicable law.

## Features

- **Natural-language SQL** via Databricks **Genie** on `healthcare.claims.drg_claims`
- **All 770 MS-DRG** reference weights/LOS (CMS Table 5, FY 2026)
- **ICD-10–to–DRG** validation (Appendix B–style mapping, ~65K codes)
- **CC / MCC** lookup (Appendix C–style list)
- **Medicare Code Editor (MCE)** v43.1 checks (age, unacceptable PDX, etc.)
- **ICD-10-PCS V43.1** “80 new codes” lookup (April 2026 announcement)
- **DRG shift** analysis (sample provider data for demo; replace with your SQL)
- **Agent skills** (YAML `SKILL.md` per domain) loaded through DeepAgents
- **Demo mode** in Streamlit without Databricks; **Connected mode** with workspace credentials

## Requirements

- Python 3.10+
- Databricks workspace with:
  - **Genie** space pointed at your claims table (or equivalent SQL)
  - **Model serving** or foundation model access for the chosen `LLM_ENDPOINT`
  - Personal access token or service principal for API auth

## Quick start

```bash
cd drg_claims_agent
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate       # macOS / Linux
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your DATABRICKS_HOST, DATABRICKS_TOKEN, GENIE_SPACE_ID, LLM_ENDPOINT
```

### Verify bundled CMS data (optional)

```bash
python config.py
# Expect: Bundled reference data: OK
```

### Run the Streamlit app

```bash
streamlit run app.py
```

- **Demo (no Databricks):** use sidebar default; answers are keyword-matched samples.
- **Connected:** enter workspace URL, token, LLM endpoint, and Genie space ID (or set via `.env` / Streamlit secrets).

## Configuration

| Variable | Purpose |
|----------|---------|
| `DATABRICKS_HOST` | Workspace URL, e.g. `https://xxx.cloud.databricks.com` |
| `DATABRICKS_TOKEN` | `dapi...` personal access token or SP secret |
| `GENIE_SPACE_ID` | Genie space that can query the claims table |
| `LLM_ENDPOINT` | Databricks model endpoint name, e.g. `databricks-claude-sonnet-4` |
| `DRG_AGENT_STRICT` | Set to `1` in **production** to reject placeholder creds and validate JSON bundles at startup |

See `.env.example` for copy-paste templates.

**Streamlit Cloud:** add the same keys under **App settings → Secrets**; the app reads `st.secrets` when environment variables are unset.

## Project layout

| Path | Description |
|------|-------------|
| `app.py` | Streamlit UI (demo + connected) |
| `agent.py` | `create_drg_agent()` — DeepAgents + Genie + tools + skills mount |
| `config.py` | Environment loading, production validation, `verify_bundled_reference_data()` |
| `tools/` | LangChain tools + JSON reference files (Table 5, MCE, Appendix B/C, V43.1 PCS) |
| `skills/` | DeepAgents skills (`SKILL.md` in subfolders) |
| `reference/` | Source text for one-off parsers (e.g. PCS announcement) |
| `notebooks/` | Databricks SQL to create sample `healthcare.claims.drg_claims` |
| `README.md` | This file |
| `ARCHITECTURE.md` | System design and data flow |

## Regenerating reference JSON (advanced)

- **MCE** from CMS *Definitions of Medicare Code Edits* text: `python tools/parse_mce.py <path-to-txt>` → `tools/mce_reference.json`
- **V43.1 new PCS** list: edit `reference/v43_1_pcs_announcement.txt`, then `python tools/parse_v43_1_announcement.py` → `tools/v43_1_new_pcs_codes.json`

## Production notes

- Set `DRG_AGENT_STRICT=1` and real secrets; do not commit `.env` (see `.gitignore`).
- Configure `logging` in your process so `agent` module logs are visible.
- Point Genie and SQL grants at the real Unity Catalog table; update the system prompt in `agent.py` if the table name or schema differs.
- Replace **demo** `drg_shift_analysis` data with Genie-driven queries for production.

## License / data

Reference JSON derives from **CMS** public materials (e.g. IPPS Table 5, MS-DRG definitions, MCE, PCS announcements). Retain CMS attribution in derivative works as required by CMS terms of use. Sample claims in notebooks are **synthetic** for training.

## Further reading

- [ARCHITECTURE.md](ARCHITECTURE.md) — components, request flow, and tool routing
- Databricks: [MS-DRG Classifications and Software](https://www.cms.gov/Medicare/Medicare-Fee-for-Service-Payment/AcuteInpatientPPS/MS-DRG-Classifications-and-Software.html)
