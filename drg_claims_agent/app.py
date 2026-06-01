"""
DRG Claims Analysis Agent -- Streamlit Chat UI

Two modes:
  DEMO:      Keyword-matched responses -- no Databricks needed.
  CONNECTED: Calls the DeepAgents agent backed by Databricks Genie + LLM.

Run:  streamlit run app.py
"""

import os
import json
import streamlit as st

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

st.set_page_config(
    page_title="DRG Claims Agent",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _env(name: str, default: str = "") -> str:
    """Environment variable, then Streamlit Cloud ``st.secrets`` (production)."""
    try:
        if hasattr(st, "secrets") and name in st.secrets:
            return str(st.secrets[name]).strip()
    except (RuntimeError, TypeError, KeyError, FileNotFoundError):
        pass
    return (os.getenv(name) or default).strip()

# ── CSS ──────────────────────────────────────────────────────────
st.markdown("""
<style>
.main-header{text-align:center;padding:1rem 0;border-bottom:2px solid #0066cc;margin-bottom:1.5rem}
.main-header h1{color:#0066cc;font-size:2rem;margin-bottom:.2rem}
.main-header p{color:#666;font-size:.95rem}
.sidebar-card{background:#f0f4ff;padding:.8rem;border-radius:8px;margin:.4rem 0;border-left:3px solid #0066cc;font-size:.88rem}
.badge{display:inline-block;padding:2px 8px;border-radius:12px;font-size:.72rem;font-weight:600;margin:2px}
.badge-genie{background:#e8f5e9;color:#2e7d32}
.badge-audit{background:#fff3e0;color:#e65100}
.badge-deep{background:#e3f2fd;color:#1565c0}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Settings")
    mode = st.radio("Mode", ["Demo (no Databricks)", "Connected (Databricks)"], index=0)

    if mode.startswith("Connected"):
        st.markdown("---")
        st.markdown("### Databricks Connection")
        db_host = st.text_input("Workspace URL", _env("DATABRICKS_HOST", ""), placeholder="https://...")
        db_token = st.text_input("Token", _env("DATABRICKS_TOKEN", ""), type="password")
        llm_ep = st.text_input("LLM Endpoint", _env("LLM_ENDPOINT", "databricks-meta-llama-3-3-70b-instruct"))
        genie_id = st.text_input("Genie Space ID", _env("GENIE_SPACE_ID", ""))
        connected = all([db_host, db_token, llm_ep, genie_id])
        if connected:
            st.success("Ready to connect")
        else:
            st.warning("Fill all fields")
    else:
        connected = False

    st.markdown("---")
    st.markdown("### Agent Architecture")
    st.markdown("""
<div class="sidebar-card">
<span class="badge badge-genie">Genie</span>
<span class="badge badge-audit">Audit</span>
<span class="badge badge-deep">DeepAgents</span>
<br><br>
<b>Routing:</b>
<ul style="font-size:.82rem;margin:.3rem 0">
<li>Data/SQL → Genie (writes SQL)</li>
<li>Validation → Audit sub-agent</li>
<li>Reports → DeepAgents write_file</li>
<li>Complex → Plan + delegate</li>
</ul>
</div>
""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Sample Questions")
    samples = [
        "Show DRG shift patterns for heart failure",
        "Would MCE flag N40.0 (BPH) for a 5-year-old patient?",
        "What are the severity tiers for the pneumonia DRG family?",
        "What are the top 5 DRGs by total charges?",
        "Show readmission rates by provider",
        "Is DRG 470 correct for ICD M16.11?",
        "Audit all DRG 470 claims for coding errors",
        "Compare Q1 vs Q2 average LOS by DRG",
        "What is the CMS weight for DRG 871?",
        "Write a cost analysis report for DRG 291",
    ]
    for s in samples:
        if st.button(s, key=f"sample_{s[:20]}", use_container_width=True):
            st.session_state.pending_input = s

    st.markdown("---")
    if st.button("Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.reports = []
        st.rerun()

# ── Header ───────────────────────────────────────────────────────
col_main, col_report = st.columns([3, 2])

with col_main:
    st.markdown("""
<div class="main-header">
<h1>DRG Claims Analysis Agent</h1>
<p>DeepAgents + Databricks Genie + LangGraph &nbsp;|&nbsp; Healthcare Claims Intelligence</p>
</div>
""", unsafe_allow_html=True)

# ── Demo Responses ───────────────────────────────────────────────
DEMO = {
    "top": (
        "Here are the **top 5 DRGs by total charges** from the claims data:\n\n"
        "| Rank | DRG | Description | Total Charges | Claims |\n"
        "|------|-----|-------------|---------------|--------|\n"
        "| 1 | 871 | Septicemia/Severe Sepsis With MCC | $860,500 | 6 |\n"
        "| 2 | 470 | Major Hip/Knee Replacement | $621,400 | 8 |\n"
        "| 3 | 291 | Heart Failure With MCC | $449,600 | 5 |\n"
        "| 4 | 193 | Pneumonia With MCC | $429,700 | 5 |\n"
        "| 5 | 064 | Intracranial Hemorrhage With MCC | $345,000 | 3 |\n\n"
        "Sepsis (DRG 871) drives the highest total charges at $860K across 6 claims, "
        "with an average of $143K per case."
    ),
    "readmission": (
        "**Readmission rates by provider:**\n\n"
        "| Provider | Total Claims | Readmissions | Rate |\n"
        "|----------|-------------|--------------|------|\n"
        "| City General Hospital | 18 | 2 | 11.1% |\n"
        "| Regional Medical Center | 16 | 4 | 25.0% |\n"
        "| University Hospital | 13 | 2 | 15.4% |\n"
        "| Behavioral Health Center | 3 | 1 | 33.3% |\n\n"
        "Regional Medical Center has the highest readmission rate at 25%. "
        "This warrants further investigation, particularly for DRGs 871 and 291."
    ),
    "validate": (
        "**Validation Result:**\n\n"
        "```json\n"
        '{\n'
        '  "valid": true,\n'
        '  "icd_code": "M16.11",\n'
        '  "drg_code": "470",\n'
        '  "drg_description": "Major Hip and Knee Joint Replacement Without MCC",\n'
        '  "matched_prefix": "M16",\n'
        '  "reasoning": "ICD-10 code M16.11 (Primary osteoarthritis, right hip) starts with M16, '\
        'which is a valid principal diagnosis for MS-DRG 470. Coding appears appropriate."\n'
        '}\n'
        "```\n\n"
        "The coding is **correct**. M16.11 (primary osteoarthritis of the right hip) "
        "is a valid principal diagnosis for DRG 470 (Major Hip/Knee Replacement)."
    ),
    "audit": (
        "**DRG 470 Coding Audit Results:**\n\n"
        "Analyzed **8 claims** with DRG 470.\n\n"
        "### Findings\n\n"
        "| Claim ID | ICD-10 | Valid? | Issue |\n"
        "|----------|--------|--------|-------|\n"
        "| CLM001 | M16.11 | PASS | Correct |\n"
        "| CLM002 | M17.11 | PASS | Correct |\n"
        "| CLM003 | M16.12 | PASS | Correct |\n"
        "| CLM004 | M17.12 | PASS | Correct |\n"
        "| CLM005 | M16.11 | PASS | Correct |\n"
        "| CLM006 | M17.11 | PASS | Correct |\n"
        "| CLM007 | M16.9  | PASS | Correct |\n"
        "| **CLM043** | **J18.9** | **FAIL** | Pneumonia code assigned to joint replacement DRG |\n\n"
        "### Summary\n"
        "- **7 of 8** claims have correct coding\n"
        "- **1 critical error**: CLM043 has principal diagnosis J18.9 (Pneumonia) "
        "but is coded as DRG 470 (Joint Replacement). Suggested DRG: 193 or 194.\n"
        "- **Estimated financial impact**: ~$33,000 overpayment on CLM043\n\n"
        "A detailed report has been saved."
    ),
    "compare": (
        "**Q1 vs Q2 Average Length of Stay by DRG:**\n\n"
        "| DRG | Q1 Avg LOS | Q2 Avg LOS | Change |\n"
        "|-----|-----------|-----------|--------|\n"
        "| 470 | 3.4 days | 3.0 days | -0.4 |\n"
        "| 871 | 8.5 days | 7.0 days | -1.5 |\n"
        "| 392 | 2.2 days | 2.0 days | -0.2 |\n"
        "| 291 | 6.4 days | 6.0 days | -0.4 |\n"
        "| 690 | 2.6 days | 3.0 days | +0.4 |\n\n"
        "Most DRGs show improved (shorter) LOS in Q2, particularly "
        "DRG 871 (Sepsis) which decreased by 1.5 days. "
        "DRG 690 (UTI) increased slightly, which may warrant review."
    ),
    "weight": (
        "**MS-DRG 871 Reference Data:**\n\n"
        "| Attribute | Value |\n"
        "|-----------|-------|\n"
        "| Description | Septicemia or Severe Sepsis Without MV >96 Hours With MCC |\n"
        "| MDC | 18 - Infectious and Parasitic Diseases |\n"
        "| Type | Medical |\n"
        "| **Relative Weight** | **1.8244** |\n"
        "| Geometric Mean LOS | 5.2 days |\n"
        "| Arithmetic Mean LOS | 6.5 days |\n\n"
        "At a weight of 1.8244, DRG 871 reimburses about 82% more than the "
        "base DRG rate. Valid principal diagnoses include A40.x and A41.x (septicemia codes)."
    ),
    "report": (
        "I'll create a cost analysis report for DRG 291 (Heart Failure With MCC).\n\n"
        "**Planning steps:**\n"
        "1. Query all DRG 291 claims from the database\n"
        "2. Calculate aggregate statistics\n"
        "3. Break down by provider and payer\n"
        "4. Identify outliers\n"
        "5. Write the report\n\n"
        "---\n\n"
        "# DRG 291 Cost Analysis Report\n\n"
        "## Summary\n"
        "- **Total claims**: 5\n"
        "- **Date range**: Jan 2025 - Mar 2025\n"
        "- **Average charges**: $89,920\n"
        "- **Average payments**: $42,440\n"
        "- **Average LOS**: 6.4 days (CMS GMLOS: 4.5)\n"
        "- **Readmission rate**: 40% (2 of 5)\n\n"
        "## By Provider\n"
        "| Provider | Claims | Avg Charges | Avg LOS |\n"
        "|----------|--------|-------------|--------|\n"
        "| City General | 2 | $95,250 | 6.5 |\n"
        "| Regional Medical | 2 | $86,000 | 6.5 |\n"
        "| University Hospital | 1 | $82,100 | 6.0 |\n\n"
        "## Outliers\n"
        "- **CLM022**: LOS=8 days (77% above GMLOS), charges=$112K\n"
        "- **CLM020 & CLM023**: Readmitted within period\n\n"
        "Report saved to `drg_291_cost_analysis.md`."
    ),
    "shift": (
        "**Heart Failure DRG Shift Analysis:**\n\n"
        "Comparing DRG severity assignment (291=MCC / 292=CC / 293=Base) across providers:\n\n"
        "| Provider | Claims | DRG 291 (MCC) | DRG 292 (CC) | DRG 293 (Base) | MCC Rate | vs Peer |\n"
        "|----------|--------|---------------|--------------|----------------|----------|--------|\n"
        "| City General Hospital | 8 | 6 (75.0%) | 1 (12.5%) | 1 (12.5%) | 75.0% | +35.0% |\n"
        "| Regional Medical Ctr | 7 | 2 (28.6%) | 3 (42.9%) | 2 (28.6%) | 28.6% | -11.4% |\n"
        "| University Hospital | 5 | 2 (40.0%) | 2 (40.0%) | 1 (20.0%) | 40.0% | baseline |\n\n"
        "### Flags\n\n"
        "**HIGH RISK - City General Hospital:** MCC capture rate 75% is 1.9x the peer "
        "average of 40%. This suggests either superior clinical documentation or potential "
        "DRG upcoding. Recommended: chart review for CC/MCC documentation practices.\n\n"
        "### Financial Impact\n\n"
        "The weight spread between DRG 293 (0.70) and DRG 291 (1.35) is **93%**. "
        "At a base rate of ~$6,000, this translates to approximately **$3,900 more per case** "
        "when coded as MCC vs base. City General's higher MCC rate represents an estimated "
        "**$15,600 additional revenue** across their heart failure cases compared to peers."
    ),
    "mce": (
        "**Medicare Code Editor (MCE) v43.1 — sample check:**\n\n"
        "For **N40.0** (Benign prostatic hyperplasia) on a **5-year-old**, MCE applies "
        "**Edit 4 (Age conflict)**: the code is on the *adult* list (ages 15–124), "
        "so age 5 is inconsistent with the diagnosis.\n\n"
        "*(Hypertension I10 is a different example: it is more often caught under "
        "**Edit 8 — Questionable admission** as principal, not the age list.)*\n\n"
        "```json\n"
        "{\n"
        '  "icd_code": "N400",\n'
        '  "flags": [\n'
        '    {\n'
        '      "edit": "4 Age conflict (adult list)",\n'
        '      "detail": "ICD N400 is for ages 15-124. Patient age 5. ..."\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "```\n\n"
        "MCE is separate from MS-DRG grouping: it flags **claim data consistency** "
        "(PDX rules, age, etc.). Use the `mce_code_check` tool in Connected mode for live results."
    ),
    "family": (
        "**DRG Family: Heart Failure and Shock**\n\n"
        "| Tier | DRG | Description | Weight | GMLOS |\n"
        "|------|-----|-------------|--------|-------|\n"
        "| MCC | 291 | Heart Failure and Shock With MCC | 1.3520 | 4.5 days |\n"
        "| CC | 292 | Heart Failure and Shock With CC | 0.9691 | 3.3 days |\n"
        "| Base | 293 | Heart Failure and Shock Without CC/MCC | 0.6983 | 2.5 days |\n\n"
        "**Weight Spread:** 93.6% between base and MCC\n"
        "**Shift Risk:** HIGH -- significant payment variation based on severity coding\n\n"
        "This means the same heart failure patient could generate payments ranging from "
        "~$4,200 (base) to ~$8,100 (MCC) depending on documented comorbidities."
    ),
    "default": (
        "I'm your DRG Claims Analysis Agent. I can help with:\n\n"
        "- **Data queries**: Ask anything about claims, costs, providers, payers\n"
        "- **DRG lookups**: CMS weights, mean LOS, valid diagnoses\n"
        "- **Coding validation**: Check if ICD-10 codes match DRG assignments\n"
        "- **DRG shift analysis**: Compare how hospitals assign severity levels\n"
        "- **Audits**: Systematic review of coding accuracy\n"
        "- **Reports**: Detailed cost analysis and compliance reports\n\n"
        "Try one of the sample questions in the sidebar, or ask your own!"
    ),
}


def get_demo_response(msg: str) -> str:
    m = msg.lower()
    if any(
        w in m
        for w in [
            "mce",
            "medicare code edit",
            "medicare code editor",
            "age conflict",
            "unacceptable principal",
            "manifestation as principal",
            "questionable admission",
        ]
    ):
        return DEMO["mce"]
    if any(w in m for w in ["shift", "upcod", "variation", "mcc rate", "capture rate"]):
        return DEMO["shift"]
    if any(w in m for w in ["family", "severity tier", "tiers", "spread"]):
        return DEMO["family"]
    if any(w in m for w in ["top", "highest", "most"]):
        return DEMO["top"]
    if any(w in m for w in ["readmission", "readmit"]):
        return DEMO["readmission"]
    if any(w in m for w in ["valid", "correct", "icd", "m16", "m17"]):
        return DEMO["validate"]
    if "audit" in m:
        return DEMO["audit"]
    if any(w in m for w in ["compare", "q1", "q2", "trend", "quarter"]):
        return DEMO["compare"]
    if any(w in m for w in ["weight", "cms", "reference", "lookup"]):
        return DEMO["weight"]
    if any(w in m for w in ["report", "analysis", "write"]):
        return DEMO["report"]
    return DEMO["default"]


def call_agent(user_msg: str, history: list) -> str:
    """Call the DeepAgents agent via the agent module."""
    try:
        os.environ["DATABRICKS_HOST"] = db_host
        os.environ["DATABRICKS_TOKEN"] = db_token
        os.environ["LLM_ENDPOINT"] = llm_ep
        os.environ["GENIE_SPACE_ID"] = genie_id
        os.environ["DRG_AGENT_STRICT"] = _env("DRG_AGENT_STRICT", "0")

        from agent import create_drg_agent

        if "agent_instance" not in st.session_state:
            st.session_state.agent_instance = create_drg_agent()

        agent = st.session_state.agent_instance
        msgs = [{"role": m["role"], "content": m["content"]} for m in history]
        msgs.append({"role": "user", "content": user_msg})

        result = agent.invoke({"messages": msgs})

        for msg in reversed(result["messages"]):
            if hasattr(msg, "content") and msg.content and getattr(msg, "type", "") == "ai":
                return msg.content
        return str(result)
    except Exception as e:
        return f"Error: {e}\n\nMake sure Databricks credentials are correct and `deepagents` is installed."


# ── Chat State ───────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "reports" not in st.session_state:
    st.session_state.reports = []

# ── Main Layout ──────────────────────────────────────────────────
with col_main:
    for message in st.session_state.messages:
        avatar = "🏥" if message["role"] == "assistant" else "👤"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

    if not st.session_state.messages:
        with st.chat_message("assistant", avatar="🏥"):
            st.markdown(
                "Welcome to the **DRG Claims Analysis Agent**.\n\n"
                "I can query your claims data, validate DRG coding, run audits, "
                "and write reports. Try a sample question from the sidebar or ask your own."
            )

    pending = st.session_state.pop("pending_input", None)
    prompt = st.chat_input("Ask about DRG claims, coding, costs, audits...") or pending

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar="🏥"):
            with st.spinner("Analyzing..."):
                if connected:
                    response = call_agent(prompt, st.session_state.messages[:-1])
                else:
                    response = get_demo_response(prompt)
            st.markdown(response)

        st.session_state.messages.append({"role": "assistant", "content": response})

        if any(kw in prompt.lower() for kw in ["report", "audit", "write"]):
            st.session_state.reports.append({
                "title": prompt[:60],
                "content": response,
            })

with col_report:
    st.markdown("### Reports & Files")
    if st.session_state.reports:
        for i, rpt in enumerate(st.session_state.reports):
            with st.expander(f"📄 {rpt['title']}", expanded=(i == len(st.session_state.reports) - 1)):
                st.markdown(rpt["content"])
                st.download_button(
                    "Download as Markdown",
                    rpt["content"],
                    file_name=f"report_{i+1}.md",
                    mime="text/markdown",
                    key=f"dl_{i}",
                )
    else:
        st.info("Reports will appear here when you ask for audits or analyses.")

    st.markdown("---")
    st.markdown("### DRG Quick Reference")
    ref_data = {
        "DRG": ["470", "871", "291", "392", "690", "193", "064", "322", "885"],
        "Description": [
            "Hip/Knee Replacement",
            "Sepsis With MCC",
            "Heart Failure With MCC",
            "GI Disorders",
            "UTI Without MCC",
            "Pneumonia With MCC",
            "Stroke With MCC",
            "PCI w/ Intraluminal Device w/o MCC (FY26)",
            "Psychoses",
        ],
        "Weight": [1.9289, 1.9425, 1.2838, 0.7796, 0.8095, 1.3144, 2.0110, 1.763, 1.3968],
        "GMLOS": [1.9, 4.8, 3.8, 2.5, 2.8, 3.9, 4.4, 2.0, 6.5],
    }
    st.dataframe(ref_data, width="stretch", hide_index=True)
