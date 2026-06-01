"""FastAPI entrypoint for the DRG Deep-Agent backend.

Endpoints:
  GET  /api/health  -> readiness probe
  POST /api/chat    -> SSE stream of the agent's reply (may end in an `interrupt`)
  POST /api/resume  -> resume a paused (human-in-the-loop) run with a decision

Human-in-the-loop: when the data-agent calls `execute_sql`, deepagents'
`interrupt_on` middleware pauses the graph. After streaming, we inspect the graph
state for a pending interrupt and emit an `interrupt` SSE event carrying the SQL.
The frontend shows an approve/edit/reject card and POSTs to /api/resume, which
resumes the graph with `Command(resume={"decisions":[...]})`.
"""
from __future__ import annotations

import json
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import AIMessageChunk, HumanMessage
from langgraph.types import Command
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from .agent import get_agent
from .config import get_settings
from .trace import (
    TraceCollector,
    add_step,
    get_trace,
    reset_trace,
    steps_to_mermaid,
)

settings = get_settings()

# Remember each thread's current question so the flow diagram can label it across
# the chat turn and its human-in-the-loop resume.
_QUESTIONS: dict[str, str] = {}

app = FastAPI(title="DRG Deep-Agent API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN, "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"


class ResumeRequest(BaseModel):
    thread_id: str
    decision: str  # "approve" | "edit" | "reject"
    edited_sql: Optional[str] = None


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok", "model": settings.MODEL}


# --------------------------------------------------------------------------
# Streaming helpers
# --------------------------------------------------------------------------
def _chunk_text(chunk: AIMessageChunk) -> str:
    text = chunk.content
    if isinstance(text, list):  # some providers return content as parts
        text = "".join(
            part.get("text", "") if isinstance(part, dict) else str(part) for part in text
        )
    return text or ""


async def _stream_messages(agent, graph_input, config):
    """Yield `token` SSE events for the top-level supervisor's reply."""
    async for chunk, metadata in agent.astream(
        graph_input, config=config, stream_mode="messages"
    ):
        # Skip nested subagent/tool chatter (namespace joined with "|").
        if not isinstance(chunk, AIMessageChunk):
            continue
        if "|" in (metadata or {}).get("checkpoint_ns", ""):
            continue
        text = _chunk_text(chunk)
        if text:
            yield {"event": "token", "data": json.dumps({"text": text})}


def _collect_interrupts(state) -> list:
    """Recursively collect interrupts from a (sub)graph state snapshot."""
    found: list = []

    def walk(snap):
        if snap is None:
            return
        for it in (getattr(snap, "interrupts", None) or []):
            found.append(it)
        for task in (getattr(snap, "tasks", None) or []):
            for it in (getattr(task, "interrupts", None) or []):
                found.append(it)
            walk(getattr(task, "state", None))

    walk(state)
    return found


def _first_action_request(interrupts) -> Optional[dict]:
    for it in interrupts:
        value = getattr(it, "value", None)
        if isinstance(value, dict) and value.get("action_requests"):
            return value["action_requests"][0]
    return None


def _hitl_payload(interrupts) -> Optional[dict]:
    for it in interrupts:
        value = getattr(it, "value", None)
        if isinstance(value, dict) and value.get("action_requests"):
            ar = value["action_requests"][0]
            args = ar.get("args", {}) or {}
            review = (value.get("review_configs") or [{}])[0]
            return {
                "type": "sql_approval",
                "tool": ar.get("name"),
                "sql": args.get("sql"),
                "question": args.get("question"),
                "allowed_decisions": review.get(
                    "allowed_decisions", ["approve", "edit", "reject"]
                ),
            }
    return None


async def _drive(agent, graph_input, config, thread_id: str, question: str):
    """Stream tokens, then emit `interrupt` (if paused), else `trace` + `done`."""
    answer_parts: list[str] = []
    try:
        async for ev in _stream_messages(agent, graph_input, config):
            try:
                answer_parts.append(json.loads(ev["data"])["text"])
            except (KeyError, ValueError):
                pass
            yield ev
        state = await agent.aget_state(config, subgraphs=True)
        payload = _hitl_payload(_collect_interrupts(state))
        if payload:
            # Record a pending approval node for the flow diagram.
            add_step(
                thread_id,
                {"kind": "approval", "name": "approval", "decision": "pending", "sql": payload.get("sql")},
            )
            yield {"event": "interrupt", "data": json.dumps(payload)}
            return
        mermaid = steps_to_mermaid(thread_id, question, "".join(answer_parts))
        yield {
            "event": "trace",
            "data": json.dumps({"mermaid": mermaid, "steps": get_trace(thread_id)}),
        }
    except Exception as exc:  # noqa: BLE001 - surface to the UI
        yield {"event": "error", "data": json.dumps({"error": str(exc)})}
    yield {"event": "done", "data": "{}"}


# --------------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------------
async def _chat_stream(message: str, thread_id: str):
    agent = get_agent()
    reset_trace(thread_id)  # new turn -> fresh flow
    _QUESTIONS[thread_id] = message
    config = {
        "configurable": {"thread_id": thread_id},
        "callbacks": [TraceCollector(thread_id)],
    }
    async for ev in _drive(
        agent, {"messages": [HumanMessage(content=message)]}, config, thread_id, message
    ):
        yield ev


@app.post("/api/chat")
async def chat(req: ChatRequest):
    return EventSourceResponse(_chat_stream(req.message, req.thread_id))


async def _resume_stream(req: ResumeRequest):
    agent = get_agent()
    config = {
        "configurable": {"thread_id": req.thread_id},
        "callbacks": [TraceCollector(req.thread_id)],
    }
    state = await agent.aget_state(config, subgraphs=True)
    interrupts = _collect_interrupts(state)
    action_request = _first_action_request(interrupts)
    if action_request is None:
        yield {
            "event": "error",
            "data": json.dumps({"error": "No pending approval for this conversation."}),
        }
        yield {"event": "done", "data": "{}"}
        return

    decision = (req.decision or "").lower()
    if decision == "approve":
        decision_obj: dict = {"type": "approve"}
    elif decision == "reject":
        decision_obj = {"type": "reject"}
    else:  # edit
        args = dict(action_request.get("args", {}) or {})
        if req.edited_sql is not None:
            args["sql"] = req.edited_sql
        decision_obj = {
            "type": "edit",
            "edited_action": {"name": action_request.get("name"), "args": args},
        }

    # Record the human's decision on the pending approval node.
    for step in reversed(get_trace(req.thread_id)):
        if step.get("kind") == "approval":
            step["decision"] = {"approve": "approved", "edit": "edited & run", "reject": "rejected"}.get(
                decision, decision
            )
            if decision == "edit" and req.edited_sql:
                step["sql"] = req.edited_sql
            break

    command = Command(resume={"decisions": [decision_obj]})
    async for ev in _drive(agent, command, config, req.thread_id, _QUESTIONS.get(req.thread_id, "")):
        yield ev


@app.post("/api/resume")
async def resume(req: ResumeRequest):
    return EventSourceResponse(_resume_stream(req))
