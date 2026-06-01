"""Unit tests for execution-trace capture and Mermaid generation."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_collector_records_and_skips_builtins():
    from app import trace

    tid = "t-rec"
    trace.reset_trace(tid)
    c = trace.TraceCollector(tid)
    # task (route) + a domain tool + a skipped builtin
    c.on_tool_start({"name": "task"}, "", run_id="r1", inputs={"subagent_type": "data-agent"})
    c.on_tool_start({"name": "genie_generate_sql"}, "", run_id="r2", inputs={"question": "q"})
    c.on_tool_end(
        SimpleNamespace(content='{"sql": "SELECT 1"}'), run_id="r2"
    )
    c.on_tool_start({"name": "ls"}, "", run_id="r3", inputs={})  # builtin -> skipped

    steps = trace.get_trace(tid)
    names = [s["name"] for s in steps]
    assert names == ["task", "genie_generate_sql"]  # ls skipped
    assert steps[0]["kind"] == "route" and "data-agent" in steps[0]["label"]
    assert "SELECT 1" in steps[1]["summary"]


def test_steps_to_mermaid_is_wellformed():
    from app import trace

    tid = "t-mer"
    trace.reset_trace(tid)
    trace.add_step(tid, {"kind": "route", "name": "task", "label": "Route → data-agent"})
    trace.add_step(
        tid,
        {"kind": "tool", "name": "genie_generate_sql", "label": "Genie generates SQL", "sql": "SELECT 1"},
    )
    trace.add_step(
        tid,
        {"kind": "approval", "name": "approval", "decision": "approved", "sql": "SELECT 1"},
    )
    mer = trace.steps_to_mermaid(tid, "how many?", "answer text")
    assert mer.startswith("flowchart TD")
    assert "Human approval" in mer
    assert "approved" in mer
    assert mer.count("-->") >= 4  # U->S->route->tool->approval->answer


def test_execute_sql_summary():
    from app.trace import _summarize

    out = SimpleNamespace(content='{"row_count": 3, "saved_as_tool": true}')
    s = _summarize("execute_sql", out)
    assert "3 row" in s and "saved" in s
