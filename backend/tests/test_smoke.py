"""Stage-1 smoke tests — verify the agent graph wires up without a live LLM.

These do NOT call OpenAI. They confirm the structure compiles so a missing/fake
API key doesn't hide import or wiring errors. Run with:

    cd backend
    python -m pytest -q          # or: python tests/test_smoke.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Make `app` importable when run directly (python tests/test_smoke.py).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Ensure construction never depends on a real key.
os.environ.setdefault("OPENAI_API_KEY", "sk-REPLACE_ME")


def test_subagents_are_well_formed():
    from app.subagents import (
        APPEALS_SUBAGENT,
        CALLCENTER_SUBAGENT,
        CONTEXT_SUBAGENT,
        build_drg_subagent,
    )

    subs = [build_drg_subagent(), APPEALS_SUBAGENT, CALLCENTER_SUBAGENT, CONTEXT_SUBAGENT]
    names = {s["name"] for s in subs}
    assert names == {"drg-agent", "appeals-agent", "callcenter-agent", "context-agent"}
    for s in subs:
        assert s["description"] and s["system_prompt"]
        assert s.get("tools"), f"{s['name']} should expose at least one tool"


def test_drg_skill_path_exists():
    from app.subagents import build_drg_subagent

    skill_dir = Path(build_drg_subagent()["skills"][0])
    assert (skill_dir / "SKILL.md").is_file(), "clinical-evidence SKILL.md missing"


def test_supervisor_agent_compiles():
    from app.agent import get_agent

    agent = get_agent()
    # A compiled LangGraph exposes astream/ainvoke.
    assert hasattr(agent, "astream")
    assert hasattr(agent, "ainvoke")


if __name__ == "__main__":
    test_subagents_are_well_formed()
    test_drg_skill_path_exists()
    test_supervisor_agent_compiles()
    print("OK: all Stage-1 smoke tests passed.")
