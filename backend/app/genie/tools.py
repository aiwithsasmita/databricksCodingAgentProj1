"""Builds one LangChain tool per configured Genie space.

Each space ``foo`` becomes a tool ``genie_foo(question: str)`` whose description
includes the space's purpose so the supervisor/DRG agent knows when to call it.
The tool calls Genie, then returns a compact JSON payload (SQL + columns + rows)
that the LLM can reason over.
"""
from __future__ import annotations

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from .client import get_genie_client
from .registry import GenieSpace, load_genie_spaces


class GenieQueryInput(BaseModel):
    question: str = Field(
        description=(
            "A clear, self-contained natural-language data question for this "
            "Genie space. Include any DRG code, fiscal years, state, or "
            "provider/TIN the analysis needs."
        )
    )


def _make_tool(space: GenieSpace) -> StructuredTool:
    client = get_genie_client()

    def _run(question: str) -> str:
        result = client.ask(space.space_id, question, space_name=space.name)
        # GenieResult.to_json already caps rows to GENIE_MAX_ROWS.
        return result.to_json()

    # space.description is config-provided; render it as clearly-labeled data
    # rather than free-floating guidance (already whitespace-collapsed + capped
    # in the registry).
    description = (
        f"Query the Databricks Genie space '{space.name}' with a natural-language "
        f"question and get back the generated SQL plus result rows (as JSON). "
        f'Use this for LIVE data. Scope (config-provided): "{space.description}"'
    )
    return StructuredTool.from_function(
        func=_run,
        name=space.tool_name,
        description=description,
        args_schema=GenieQueryInput,
    )


def genie_tools_for(agent: str = "drg") -> list[StructuredTool]:
    """Return the Genie tools assigned to ``agent``.

    Returns an empty list when no spaces are configured or credentials are
    missing — callers then fall back to the Stage-1 mock tools.
    """
    client = get_genie_client()
    if not client.available():
        return []
    spaces = [s for s in load_genie_spaces() if s.agent == agent]
    return [_make_tool(s) for s in spaces]
