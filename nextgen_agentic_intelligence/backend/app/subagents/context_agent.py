"""CMS Context subagent — answers from the ingested official CMS datasets.

Backed by FY2023-FY2026 MS-DRG catalogs (Table 5), DRG change logs, IPPS rule
highlights + provider payment factors, the CC/MCC lists, and ICD-10 update
counts (Tables 6) — all from the official CMS IPPS Final Rule files.
"""
from __future__ import annotations

from ..prompts import CONTEXT_AGENT_PROMPT
from ..tools.cms_tools import CMS_TOOLS

CONTEXT_SUBAGENT = {
    "name": "context-agent",
    "description": (
        "Answers CMS / MS-DRG reference questions from official IPPS Final Rule "
        "data (FY2023-FY2026): which DRGs were added/deleted/retitled in a year, "
        "what a DRG is (title, MDC, severity, weight), IPPS rule changes and "
        "provider payment factors (wage index, DSH, NTAP, quality programs), "
        "CC/MCC status of an ICD-10 code, and ICD-10 code-update counts."
    ),
    "system_prompt": CONTEXT_AGENT_PROMPT,
    "tools": CMS_TOOLS,
}
