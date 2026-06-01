"""General-purpose Databricks Genie data-agent with human-in-the-loop SQL.

Backed by the Genie space(s) tagged ``agent="data"`` (currently the NYC-taxi
space). The supervisor routes ad-hoc data/analytics questions here. The agent
generates SQL via Genie, then a human approves/edits/rejects it before it runs
(deepagents ``interrupt_on`` middleware); approved queries are saved so repeats
skip approval. Returns ``None`` when no ``data`` space is configured.
"""
from __future__ import annotations

from typing import Optional

from ..genie import build_data_query_tools, get_genie_client, load_genie_spaces
from ..prompts import DATA_AGENT_PROMPT

_DESCRIPTION = (
    "Answers ad-hoc data/analytics and generic claims questions by generating SQL "
    "over connected Databricks data (with human approval of the SQL). Use for any "
    "general data question NOT covered by the DRG, appeals, call-center, or "
    "CMS-context specialists."
)


def build_data_subagent() -> Optional[dict]:
    """Return the HITL data-agent dict, or None if no ``data`` space exists."""
    if not get_genie_client().available():
        return None
    data_spaces = [s for s in load_genie_spaces() if s.agent == "data"]
    if not data_spaces:
        return None
    # Generic agent is backed by the first data space (the NYC-taxi space).
    space = data_spaces[0]
    tools, interrupt_on = build_data_query_tools(space)
    prompt = DATA_AGENT_PROMPT + f"\n\nConnected dataset: '{space.name}' — {space.description}"
    return {
        "name": "data-agent",
        "description": _DESCRIPTION,
        "system_prompt": prompt,
        "tools": tools,
        "interrupt_on": interrupt_on,
    }
