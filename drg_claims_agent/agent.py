"""
DRG Claims Analysis Agent -- DeepAgents + Genie + Custom Tools

Architecture:
  - GenieAgent: Primary SQL engine for ALL data queries (ad-hoc SQL on claims table)
  - Custom tools: DRG lookup + ICD-10 validation (pure clinical logic)
  - DeepAgents harness: Planning (write_todos), report writing (write_file),
    context management (auto-summarization), sub-agent orchestration

Routing:
  - Data questions --> GenieAgent (writes SQL on the fly)
  - Validation/audit --> Compliance-auditor sub-agent (drg_lookup + icd_validate)
  - Complex multi-step --> Plans with todos, delegates to both, writes report
"""

import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    DATABRICKS_HOST,
    DATABRICKS_TOKEN,
    GENIE_SPACE_ID,
    LLM_ENDPOINT,
    validate_production_settings,
    verify_bundled_reference_data,
)

logger = logging.getLogger(__name__)
from tools.drg_lookup import drg_lookup, drg_family_lookup
from tools.icd_validate import icd_code_validate, cc_mcc_check
from tools.drg_shift import drg_shift_analysis
from tools.mce_validate import mce_code_check
from tools.pcs_v43_1 import v43_1_pcs_check

DRG_SYSTEM_PROMPT = """\
You are a DRG Claims Analysis Agent -- an expert healthcare data analyst \
specializing in MS-DRG (Medicare Severity Diagnosis Related Groups) coding, \
claims data analysis, and compliance auditing.

## Data Source

The `healthcare.claims.drg_claims` table has these columns:
| Column | Type | Description |
|--------|------|-------------|
| claim_id | STRING | Unique claim identifier (e.g. CLM001) |
| patient_id | STRING | Patient identifier (e.g. PAT101) |
| admission_date | DATE | Hospital admission date |
| discharge_date | DATE | Hospital discharge date |
| drg_code | STRING | Assigned MS-DRG code (e.g. 470, 871) |
| drg_description | STRING | DRG full name |
| principal_diagnosis | STRING | ICD-10-CM principal diagnosis code |
| secondary_diagnoses | ARRAY<STRING> | CC/MCC and other secondary ICD-10 codes |
| procedures | ARRAY<STRING> | ICD-10-PCS procedure codes |
| provider_id | STRING | Hospital identifier (PRV01-PRV04) |
| provider_name | STRING | Hospital name |
| payer | STRING | Insurance payer (Medicare, Medicaid, BlueCross, Aetna, etc.) |
| total_charges | DECIMAL | Billed charges (hospital's list price) |
| total_payments | DECIMAL | Actual amount paid by payer |
| length_of_stay | INT | Days from admission to discharge |
| discharge_status | STRING | Where patient went (Home, SNF, Rehab, LTAC, Expired) |
| readmission_flag | BOOLEAN | True if readmitted within 30 days |
| created_at | TIMESTAMP | Record creation timestamp |

## Tools and Routing

Use the RIGHT tool for each question type:

### Data / SQL questions --> Claims Data Analyst (sub-agent)
Use for ANY question that requires querying the claims table: aggregates, \
counts, averages, comparisons, trends, filtering, grouping.
Examples: "top DRGs by cost", "readmission rates by provider", "Q1 vs Q2 LOS"

### DRG reference lookups --> drg_lookup (tool)
Use when the user asks about a specific DRG's **CMS Table 5** metadata: relative \
weight, GMLOS/AMLOS, MDC, medical vs surgical. This is NOT in the claims table. \
For ICD-10 to DRG validation use `icd_code_validate` instead.
Example: "What is the CMS weight for DRG 871?"

### DRG family / severity tiers --> drg_family_lookup (tool)
Use when the user wants to see all severity levels (base/CC/MCC) for a DRG \
and the payment spread between them.
Example: "What are the severity tiers for heart failure DRGs?"

### ICD-10 to DRG validation --> icd_code_validate (tool)
Use for spot-checking whether a specific ICD-10 code is valid for a specific DRG.
Example: "Is ICD M16.11 correct for DRG 470?"

### DRG shift / provider comparison --> drg_shift_analysis (tool)
Use when the user asks about DRG coding variation ACROSS providers for the \
same condition. Compares MCC capture rates and flags outliers.
Available families: heart_failure, pneumonia, sepsis, stroke, hip_knee_replacement, uti.
Example: "Show DRG shift patterns for heart failure across hospitals"

### CC/MCC classification check --> cc_mcc_check (tool)
Use to check if a secondary diagnosis code is CC, MCC, or non-CC.
Essential for auditing MCC-level DRG assignments.
Example: "Is N17.9 an MCC?"

### Medicare Code Editor (MCE) claim edits --> mce_code_check (tool)
Use for **MCE** rules from *Definitions of Medicare Code Edits* (v43.1): age vs \
diagnosis, manifestation as principal, questionable admission as principal, \
unacceptable principal diagnosis. This is **not** the same as MS-DRG Appendix B/C.
Pass `patient_age` and `is_principal` when known; for Z51.89 as principal, pass \
`has_secondary_diagnosis`.
Example: "Would MCE flag I10 as principal for a 5-year-old?"

### New ICD-10-PCS codes in V43.1 (April 2026) --> v43_1_pcs_check (tool)
CMS added **80 new ICD-10-PCS** codes for **discharges on or after 2026-04-01**. Use to \
see if a procedure code is in that list and the published description/footnotes.
This is not a full PCS validator — only the 80-code announcement.
Example: "Is 0F9480D one of the new FY2026 procedure codes?"

### Compliance audits --> Plan + multiple tools
For audits: (1) plan with write_todos, (2) query data via analyst, \
(3) validate each claim with icd_code_validate, (4) check LOS outliers \
with drg_lookup, (5) compile report with write_file.

### Reports --> write_file (built-in)
Save analysis results, audit findings, and reports as downloadable files.

### Planning --> write_todos (built-in)
Plan complex multi-step analyses before executing them.

## Output Formatting Rules

- Present data in **markdown tables** whenever comparing multiple items.
- Always cite specific **claim IDs** (e.g. CLM043), **DRG codes**, and \
  **ICD-10 codes** as evidence.
- Round currency to 2 decimal places with dollar sign ($85,200.00).
- Round percentages to 1 decimal place (75.0%).
- Structure audit findings by severity: **CRITICAL** (coding errors), \
  **WARNING** (LOS outliers), **ADVISORY** (pattern observations).
- When flagging issues, always explain WHY it's flagged and WHAT to do.

## Safety Guardrails

- NEVER fabricate clinical data. If a tool returns no results, say so.
- NEVER provide clinical or medical advice. You are a data analyst, not a \
  physician. Always say "this analysis is for coding/billing review, not \
  clinical decision-making."
- NEVER claim a coding pattern is definitely fraud. Use language like \
  "potential upcoding," "warrants chart review," or "may indicate."
- This dataset contains SAMPLE data for demonstration purposes, not real PHI.
- If you don't have enough information to answer, ask the user what's missing.

## Agent skills (progressive disclosure)

The runtime also injects a **Skills** section listing domain skills under `/skills/`. When a user
question matches a skill's description (DRG fundamentals, MCE, audit guidelines, PCS v43.1, etc.),
use `read_file` on that skill's `SKILL.md` path with a **high line limit** (e.g. 1000) before
answering, then follow that workflow. Do not skip this for complex policy or audit questions.
"""

COMPLIANCE_AUDITOR_PROMPT = """\
You are the **compliance-auditor** sub-agent: validate DRG and diagnosis coding using the tools \
you are given. Be precise, cite tool outputs, and flag issues by severity. If the task matches a \
skill under `/skills/` (audit, MCC, MCE, DRG shifts), read that skill's SKILL.md via `read_file` \
(with a sufficient line limit) before finalizing your answer.
"""


def create_drg_agent():
    """Build and return the DRG claims analysis agent.

    Uses DeepAgents with GenieAgent for data queries and custom sub-agents
    for compliance auditing. Falls back to a simple LangGraph agent if
    DeepAgents is not installed.
    """
    strict = os.getenv("DRG_AGENT_STRICT", "0").lower() in ("1", "true", "yes")
    if strict:
        validate_production_settings()
    try:
        verify_bundled_reference_data()
    except (OSError, ValueError) as e:
        logger.error("Bundled reference data check failed: %s", e)
        raise

    from databricks_langchain import ChatDatabricks
    from databricks_langchain.genie import GenieAgent

    os.environ.setdefault("DATABRICKS_HOST", DATABRICKS_HOST)
    os.environ.setdefault("DATABRICKS_TOKEN", DATABRICKS_TOKEN)

    llm = ChatDatabricks(endpoint=LLM_ENDPOINT)

    genie = GenieAgent(
        genie_space_id=GENIE_SPACE_ID,
        genie_agent_name="claims-data-analyst",
        description=(
            "Query the DRG claims database using natural language. "
            "Can answer ANY data question about claims, charges, DRGs, "
            "readmissions, providers, payers, and length of stay. "
            "This agent writes SQL on the fly against the "
            "healthcare.claims.drg_claims table."
        ),
    )

    try:
        from deepagents import CompiledSubAgent, SubAgent, create_deep_agent
        from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend

        # Load Agent Skills (SKILL.md per subfolder) from ./skills via virtual /skills/ mount
        _skills_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skills")
        _fs_backend = FilesystemBackend(root_dir=_skills_dir, virtual_mode=True)
        _backend = CompositeBackend(
            default=StateBackend(),
            routes={"/skills/": _fs_backend},
        )

        # GenieAgent returns a RunnableLambda (messages in / out) — use CompiledSubAgent, not
        # declarative SubAgent. Compiled subagents do not get SkillsMiddleware from DeepAgents;
        # the orchestrator should load /skills/ when delegating policy-heavy work to compliance-auditor.
        agent = create_deep_agent(
            model=llm,
            tools=[
                drg_lookup,
                drg_family_lookup,
                icd_code_validate,
                cc_mcc_check,
                drg_shift_analysis,
                mce_code_check,
                v43_1_pcs_check,
            ],
            system_prompt=DRG_SYSTEM_PROMPT,
            backend=_backend,
            skills=["/skills/"],
            subagents=[
                CompiledSubAgent(
                    name="claims-data-analyst",
                    description=(
                        "Use for ANY data/SQL question about claims, costs, "
                        "DRGs, providers, payers, readmissions, or length of "
                        "stay. This agent queries data via Databricks Genie "
                        "(natural language to SQL on healthcare.claims.drg_claims)."
                    ),
                    runnable=genie,
                ),
                SubAgent(
                    name="compliance-auditor",
                    description=(
                        "Validate DRG coding accuracy. Check if ICD-10 "
                        "diagnosis codes match assigned DRGs. Use for audit "
                        "and compliance tasks."
                    ),
                    system_prompt=COMPLIANCE_AUDITOR_PROMPT,
                    tools=[
                        drg_lookup,
                        drg_family_lookup,
                        icd_code_validate,
                        cc_mcc_check,
                        drg_shift_analysis,
                        mce_code_check,
                        v43_1_pcs_check,
                    ],
                    skills=["/skills/"],
                ),
            ],
        )
        logger.info("Created DeepAgents agent with Genie + audit sub-agents")
        return agent

    except ImportError:
        logger.warning(
            "deepagents not installed, falling back to simple LangGraph agent"
        )
        return _create_fallback_agent(llm, genie)


def _create_fallback_agent(llm, genie):
    """Simple LangGraph ReAct agent as fallback when DeepAgents is unavailable."""
    from typing import Annotated, Any, Optional, Sequence, TypedDict

    from langchain_core.messages import AIMessage
    from langchain_core.runnables import RunnableLambda
    from langgraph.graph import END, StateGraph
    from langgraph.graph.message import add_messages
    from langgraph.prebuilt.tool_node import ToolNode

    all_tools = [
        drg_lookup,
        drg_family_lookup,
        icd_code_validate,
        cc_mcc_check,
        drg_shift_analysis,
        mce_code_check,
        v43_1_pcs_check,
    ]

    class AgentState(TypedDict):
        messages: Annotated[Sequence[Any], add_messages]

    model = llm.bind_tools(all_tools)

    def should_continue(state: AgentState):
        last = state["messages"][-1]
        if isinstance(last, AIMessage) and last.tool_calls:
            return "continue"
        return "end"

    preprocessor = RunnableLambda(
        lambda state: [{"role": "system", "content": DRG_SYSTEM_PROMPT}]
        + state["messages"]
    )
    model_runnable = preprocessor | model

    def call_model(state, config):
        return {"messages": [model_runnable.invoke(state, config)]}

    wf = StateGraph(AgentState)
    wf.add_node("agent", RunnableLambda(call_model))
    wf.add_node("tools", ToolNode(all_tools))
    wf.set_entry_point("agent")
    wf.add_conditional_edges("agent", should_continue, {"continue": "tools", "end": END})
    wf.add_edge("tools", "agent")

    logger.info("Created fallback LangGraph agent (no Genie, no sub-agents)")
    return wf.compile()


if __name__ == "__main__":
    agent = create_drg_agent()
    result = agent.invoke(
        {"messages": [{"role": "user", "content": "What is DRG 470?"}]}
    )
    for msg in result["messages"]:
        print(f"[{msg.type}] {msg.content[:200] if msg.content else msg.tool_calls}")
