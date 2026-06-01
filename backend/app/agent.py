"""Builds the supervisor deep agent (LangChain `deepagents`).

The supervisor is a compiled LangGraph graph. It plans with todos, keeps working
memory in a virtual filesystem, and routes work to the subagents via the
built-in `task` tool. A MemorySaver checkpointer gives per-thread conversation
memory so the chat UI can keep context across turns.

Subagents are assembled at agent-construction time (not import time) so that
runtime Genie configuration determines the DRG agent's live-vs-mock tools and
whether a general data-agent is offered.
"""
from __future__ import annotations

from functools import lru_cache

from deepagents import create_deep_agent
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver

from .config import get_settings
from .prompts import SUPERVISOR_PROMPT
from .subagents import (
    APPEALS_SUBAGENT,
    CALLCENTER_SUBAGENT,
    CONTEXT_SUBAGENT,
    SEARCH_SUBAGENT,
    build_data_subagent,
    build_drg_subagent,
)

_DATA_AGENT_ROUTE = (
    "\n\nADDITIONAL ROUTE — **data-agent**: for ad-hoc data/analytics questions "
    "that don't fit the DRG, appeals, call-center, or CMS-context specialists "
    "(e.g. exploratory questions over connected Databricks datasets). Route any "
    "general data question there and summarize what it returns."
)


def _build_model() -> ChatOpenAI:
    """Construct the GPT-5.5 chat model from settings.

    Only the model id and credentials are set; GPT-5-family sampling params are
    left at their defaults to avoid 400s on parameters the model may not accept.
    """
    settings = get_settings()
    kwargs: dict = {
        "model": settings.MODEL,
        "api_key": settings.OPENAI_API_KEY,
    }
    if settings.OPENAI_BASE_URL:
        kwargs["base_url"] = settings.OPENAI_BASE_URL
    return ChatOpenAI(**kwargs)


def _build_subagents() -> list[dict]:
    """Assemble the subagent list, including data-agent only when it has tools."""
    subs = [
        build_drg_subagent(),
        APPEALS_SUBAGENT,
        CALLCENTER_SUBAGENT,
        CONTEXT_SUBAGENT,
        SEARCH_SUBAGENT,
    ]
    data_agent = build_data_subagent()
    if data_agent is not None:
        subs.append(data_agent)
    return subs


@lru_cache
def get_agent():
    """Return the singleton compiled supervisor deep agent."""
    subagents = _build_subagents()
    has_data_agent = any(s["name"] == "data-agent" for s in subagents)
    system_prompt = SUPERVISOR_PROMPT + (_DATA_AGENT_ROUTE if has_data_agent else "")

    common = dict(
        model=_build_model(),
        system_prompt=system_prompt,
        subagents=subagents,
    )
    # `checkpointer` gives per-thread memory. Older deepagents builds don't
    # accept it in create_deep_agent; fall back gracefully if so.
    try:
        return create_deep_agent(checkpointer=MemorySaver(), **common)
    except TypeError:
        return create_deep_agent(**common)
