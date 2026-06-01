"""Appeals subagent (Stage 1 stub with a MOCK tool)."""
from __future__ import annotations

from ..prompts import APPEALS_AGENT_PROMPT
from ..tools.mock_tools import appeals_lookup

APPEALS_SUBAGENT = {
    "name": "appeals-agent",
    "description": (
        "Answers appeals questions: status, volumes, overturn/upheld rates, "
        "reasons, and timelines."
    ),
    "system_prompt": APPEALS_AGENT_PROMPT,
    "tools": [appeals_lookup],
}
