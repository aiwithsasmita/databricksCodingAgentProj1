"""Call-center subagent (Stage 1 stub with a MOCK tool)."""
from __future__ import annotations

from ..prompts import CALLCENTER_AGENT_PROMPT
from ..tools.mock_tools import callcenter_lookup

CALLCENTER_SUBAGENT = {
    "name": "callcenter-agent",
    "description": (
        "Answers call-center questions: call volumes, top call reasons, average "
        "handle time, service level, and member complaints."
    ),
    "system_prompt": CALLCENTER_AGENT_PROMPT,
    "tools": [callcenter_lookup],
}
