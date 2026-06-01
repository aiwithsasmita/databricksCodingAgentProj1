"""Validate the human-in-the-loop SQL flow end-to-end against the live taxi space.

Drives the real supervisor agent (same path as the API): asks a data question,
confirms the graph PAUSES at execute_sql, then resumes with a decision and prints
the final answer. Exercises approve / edit / reject.

Usage:
    python scripts/hitl_smoke.py approve
    python scripts/hitl_smoke.py edit "SELECT COUNT(*) AS n FROM samples.nyctaxi.trips WHERE trip_distance > 5"
    python scripts/hitl_smoke.py reject
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from langchain_core.messages import AIMessageChunk, HumanMessage  # noqa: E402
from langgraph.types import Command  # noqa: E402

from app.agent import get_agent  # noqa: E402
from app.main import _collect_interrupts, _first_action_request, _hitl_payload  # noqa: E402

# Distinct question per decision so the saved-query fast-path doesn't shadow the
# approval flow we're testing.
QUESTIONS = {
    "approve": "How many taxi trips are in the dataset?",
    "edit": "What is the total fare amount across all taxi trips?",
    "reject": "What is the maximum trip distance in the taxi data?",
    "repeat": "How many taxi trips are in the dataset?",  # reuses approve's saved SQL
}


async def _drain(agent, graph_input, config) -> str:
    out = []
    async for chunk, meta in agent.astream(graph_input, config=config, stream_mode="messages"):
        if isinstance(chunk, AIMessageChunk) and "|" not in (meta or {}).get("checkpoint_ns", ""):
            t = chunk.content
            if isinstance(t, str):
                out.append(t)
    return "".join(out)


async def run(decision: str, edited_sql: str | None) -> None:
    agent = get_agent()
    question = QUESTIONS.get(decision, QUESTIONS["approve"])
    config = {"configurable": {"thread_id": f"hitl-{decision}"}}

    print(f"\n===== DECISION: {decision} =====")
    print(f"Q: {question}")
    answer1 = await _drain(agent, {"messages": [HumanMessage(content=question)]}, config)

    state = await agent.aget_state(config, subgraphs=True)
    interrupts = _collect_interrupts(state)
    payload = _hitl_payload(interrupts)
    if not payload:
        # Expected for "repeat" (saved-query fast-path => no approval needed).
        if decision == "repeat":
            print("NO INTERRUPT (expected) — answered from saved query, no HITL:")
            print("  ", answer1.strip()[:300])
        else:
            print("!! NO INTERRUPT — execute_sql did not pause for approval.")
        return
    print("INTERRUPT (SQL awaiting approval):")
    print("   tool :", payload["tool"])
    print("   sql  :", payload["sql"])
    print("   allow:", payload["allowed_decisions"])

    ar = _first_action_request(interrupts)
    if decision == "approve":
        d = {"type": "approve"}
    elif decision == "reject":
        d = {"type": "reject"}
    else:
        args = dict(ar.get("args", {}) or {})
        if edited_sql:
            args["sql"] = edited_sql
        d = {"type": "edit", "edited_action": {"name": ar.get("name"), "args": args}}

    print(f"Resuming with: {json.dumps(d)[:160]}")
    answer = await _drain(agent, Command(resume={"decisions": [d]}), config)
    print("FINAL ANSWER:\n", answer.strip()[:800])

    state2 = await agent.aget_state(config, subgraphs=True)
    print("pending interrupt after resume:", bool(_collect_interrupts(state2)))


if __name__ == "__main__":
    dec = sys.argv[1] if len(sys.argv) > 1 else "approve"
    edited = sys.argv[2] if len(sys.argv) > 2 else None
    asyncio.run(run(dec, edited))
