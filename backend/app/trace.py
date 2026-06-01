"""Execution-trace capture for the "Show flow" feature.

A lightweight LangChain callback handler records each tool/agent step as the
graph runs (callbacks propagate into subagents, so we capture the inner steps:
route -> generate SQL -> approval -> execute). Steps accumulate per thread across
a chat turn AND its human-in-the-loop resume, then we render them as a Mermaid
flowchart the frontend can draw.
"""
from __future__ import annotations

import json
from typing import Any, Optional

from langchain_core.callbacks import BaseCallbackHandler

# thread_id -> ordered list of step dicts for the current turn.
_TRACES: dict[str, list[dict]] = {}

# deepagents built-in housekeeping tools — not meaningful in the user-facing flow.
_SKIP = {"ls", "read_file", "write_file", "edit_file", "glob", "grep", "write_todos"}

_FRIENDLY = {
    "task": "Route to specialist",
    "run_saved_sql": "Check saved queries",
    "genie_generate_sql": "Genie generates SQL",
    "execute_sql": "Execute SQL",
    "web_search": "Web search",
    "drg_shift_lookup": "DRG shift lookup",
    "icd_driver_lookup": "ICD driver lookup",
    "provider_utilization_lookup": "Provider utilization",
    "cms_context_lookup": "CMS context lookup",
    "appeals_lookup": "Appeals lookup",
    "callcenter_lookup": "Call-center lookup",
}


# --------------------------------------------------------------------------
# Per-thread trace store
# --------------------------------------------------------------------------
def reset_trace(thread_id: str) -> None:
    _TRACES[thread_id] = []


def get_trace(thread_id: str) -> list[dict]:
    return _TRACES.get(thread_id, [])


def add_step(thread_id: str, step: dict) -> None:
    _TRACES.setdefault(thread_id, []).append(step)


def last_step_of(thread_id: str, name: str) -> Optional[dict]:
    for step in reversed(_TRACES.get(thread_id, [])):
        if step.get("name") == name:
            return step
    return None


# --------------------------------------------------------------------------
# Callback handler
# --------------------------------------------------------------------------
def _parse_json(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, ValueError):
            return value
    return value


def _tool_content(output: Any) -> Any:
    # on_tool_end output may be a ToolMessage, a string, or a dict.
    content = getattr(output, "content", output)
    return _parse_json(content)


def _summarize(name: str, output: Any) -> str:
    data = _tool_content(output)
    if not isinstance(data, dict):
        text = str(data)
        return text[:80]
    if name == "run_saved_sql":
        return "saved query found → ran directly" if data.get("saved") else "no saved query"
    if name == "genie_generate_sql":
        sql = data.get("sql")
        return f"SQL: {sql[:70]}" if sql else (data.get("note") or "no SQL produced")
    if name == "execute_sql":
        if data.get("error"):
            return f"error: {str(data['error'])[:60]}"
        rc = data.get("row_count")
        saved = " · saved as tool" if data.get("saved_as_tool") else ""
        return f"{rc} row(s) returned{saved}"
    if name == "web_search":
        n = len(data.get("results", []) or [])
        return f"{n} web result(s)"
    # generic
    keys = ", ".join(list(data.keys())[:4])
    return f"returned: {keys}" if keys else "ok"


def _route_target(args: Any) -> str:
    if isinstance(args, dict):
        for key in ("subagent_type", "subagent", "name", "agent"):
            if args.get(key):
                return str(args[key])
    return "specialist"


class TraceCollector(BaseCallbackHandler):
    """Records tool/agent steps into the per-thread trace store."""

    def __init__(self, thread_id: str) -> None:
        self.thread_id = thread_id
        self._runs: dict[str, dict] = {}

    def on_tool_start(
        self,
        serialized: Optional[dict],
        input_str: str,
        *,
        run_id: Any = None,
        parent_run_id: Any = None,
        metadata: Optional[dict] = None,
        inputs: Optional[dict] = None,
        **kwargs: Any,
    ) -> None:
        name = (serialized or {}).get("name") or kwargs.get("name") or "tool"
        if name in _SKIP:
            return
        args = inputs if inputs is not None else _parse_json(input_str)
        if name == "task":
            step = {
                "kind": "route",
                "name": "task",
                "label": f"Route → {_route_target(args)}",
                "summary": None,
            }
        else:
            step = {
                "kind": "tool",
                "name": name,
                "label": _FRIENDLY.get(name, name),
                "summary": None,
            }
            # Surface the generated SQL immediately so it shows even before end.
            if isinstance(args, dict) and args.get("sql"):
                step["sql"] = str(args["sql"])
        self._runs[str(run_id)] = step
        add_step(self.thread_id, step)

    def on_tool_end(self, output: Any, *, run_id: Any = None, **kwargs: Any) -> None:
        step = self._runs.get(str(run_id))
        if step is not None:
            step["summary"] = _summarize(step.get("name", ""), output)


# --------------------------------------------------------------------------
# Mermaid rendering
# --------------------------------------------------------------------------
def _esc(text: str) -> str:
    """Escape text for a Mermaid node label."""
    text = (text or "").replace('"', "'").replace("\n", " ")
    return text[:90]


def steps_to_mermaid(thread_id: str, question: str, answer: str = "") -> str:
    steps = get_trace(thread_id)
    lines = ["flowchart TD"]
    lines.append(f'  U["🧑 User<br/>{_esc(question)}"]')
    lines.append('  S["🧭 Supervisor<br/>routes the question"]')
    lines.append("  U --> S")
    prev = "S"
    for i, step in enumerate(steps):
        nid = f"N{i}"
        kind = step.get("kind")
        label = _esc(step.get("label", step.get("name", "step")))
        summary = _esc(step.get("summary") or "")
        sql = step.get("sql")
        if kind == "route":
            lines.append(f'  {nid}{{"{label}"}}')
        elif kind == "approval":
            decision = step.get("decision", "pending")
            sql_txt = _esc(sql or "")
            lines.append(
                f'  {nid}{{"🙋 Human approval<br/>{decision}<br/>{sql_txt}"}}'
            )
        else:
            body = label
            if sql and step.get("name") != "execute_sql":
                body += f"<br/>{_esc(sql)}"
            if summary:
                body += f"<br/>{summary}"
            lines.append(f'  {nid}["{body}"]')
        lines.append(f"  {prev} --> {nid}")
        prev = nid
    ans = _esc(answer) if answer else "final answer"
    lines.append(f'  F["✅ Answer<br/>{ans}"]')
    lines.append(f"  {prev} --> F")
    return "\n".join(lines)
