"""DRG shift-analysis subagent (built lazily at agent-construction time).

When Databricks Genie is configured (credentials + at least one ``drg`` space in
GENIE_SPACES), the DRG agent gets one live ``genie_<name>`` tool per space and a
data-source note that lists those tools and tells the model to treat figures as
REAL. Otherwise it falls back to the Stage-1 mock tools and labels figures as
illustrative. Building lazily (not at import) means env/settings are read when
the agent is constructed, not when the module is first imported.
"""
from __future__ import annotations

from pathlib import Path

from ..genie import genie_tools_for
from ..prompts import DRG_AGENT_PROMPT
from ..tools.mock_tools import (
    drg_shift_lookup,
    icd_driver_lookup,
    provider_utilization_lookup,
)

# Absolute path to the clinical-evidence skill directory (contains SKILL.md).
_SKILL_DIR = Path(__file__).resolve().parents[2] / "skills" / "drg_clinical_evidence"

_MOCK_TOOLS = [drg_shift_lookup, icd_driver_lookup, provider_utilization_lookup]

_DESCRIPTION = (
    "Analyzes DRG coding shift over fiscal years 2023-2026 (no CC/MCC -> CC "
    "-> MCC) nationally and by state, finds the ICD-10 codes driving the "
    "shift, applies clinical-evidence logic, and when evidence is absent "
    "identifies high-utilizing TINs/providers and super-outliers. Use for "
    "any DRG family / DRG code trend, driver, or outlier question."
)


def _live_note(tools) -> str:
    listing = "\n".join(f"- {t.name}: {t.description}" for t in tools)
    return (
        "\n\nDATA SOURCE: **LIVE Databricks Genie**. Use these tools to query real "
        "data — ask each one focused natural-language questions:\n"
        f"{listing}\n"
        "Call as many of these as the question requires (e.g. tier mix by fiscal "
        "year, ICD drivers, provider/TIN utilization) and synthesize them into one "
        "answer. These are REAL figures from Databricks — present them as real and "
        "cite Genie. Do NOT label them as mock or illustrative."
    )


_MOCK_NOTE = (
    "\n\nDATA SOURCE: Stage-1 illustrative MOCK tools (`drg_shift_lookup`, "
    "`icd_driver_lookup`, `provider_utilization_lookup`); no live Databricks "
    "connection is configured. Use them for the workflow above and clearly label "
    "every figure as illustrative mock data."
)


def build_drg_subagent() -> dict:
    """Construct the DRG subagent dict, resolving live-vs-mock tools now."""
    genie_tools = genie_tools_for("drg")
    if genie_tools:
        tools = genie_tools
        note = _live_note(genie_tools)
    else:
        tools = _MOCK_TOOLS
        note = _MOCK_NOTE
    return {
        "name": "drg-agent",
        "description": _DESCRIPTION,
        "system_prompt": DRG_AGENT_PROMPT + note,
        "tools": tools,
        "skills": [str(_SKILL_DIR)],
    }
