"""Human-in-the-loop data tools for the generic (Genie-backed) data-agent.

Workflow the data-agent follows for an ad-hoc data question:

  1. run_saved_sql(question)   -> if a previously approved SQL exists for this
                                  question, run it directly (NO human approval).
  2. genie_generate_sql(question) -> ask Genie to produce candidate SQL.
  3. execute_sql(sql, question)   -> run it. This tool is configured with
                                     `interrupt_on` so the graph PAUSES for human
                                     approve / edit / reject before it runs. On
                                     success the (question -> SQL) pair is saved
                                     so step 1 will hit it next time.

Only `execute_sql` is interrupted; the other two run without approval.
"""
from __future__ import annotations

import json

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from .client import get_genie_client
from .registry import GenieSpace
from .saved_queries import get_saved, put_saved

# interrupt_on config for the data-agent: only execute_sql needs approval.
EXECUTE_INTERRUPT = {"execute_sql": {"allowed_decisions": ["approve", "edit", "reject"]}}


class _QuestionInput(BaseModel):
    question: str = Field(description="The user's natural-language data question.")


class _ExecuteInput(BaseModel):
    sql: str = Field(description="The exact SQL to execute (from genie_generate_sql).")
    question: str = Field(
        default="", description="The originating question, so the query can be saved for reuse."
    )


def build_data_query_tools(space: GenieSpace) -> tuple[list[StructuredTool], dict]:
    """Return (tools, interrupt_on) for a generic data-agent over ``space``."""
    client = get_genie_client()

    def _run_saved(question: str) -> str:
        sql = get_saved(space.space_id, question)
        if not sql:
            return json.dumps(
                {"saved": False, "note": "No saved query — use genie_generate_sql then execute_sql."}
            )
        res = client.run_sql(space.space_id, sql)
        res.update({"saved": True, "sql": sql, "question": question})
        return json.dumps(res, default=str, ensure_ascii=False)

    def _generate(question: str) -> str:
        r = client.ask(space.space_id, question, space_name=space.name)
        return json.dumps(
            {
                "sql": r.sql,
                "description": r.description,
                "question": question,
                "error": r.error,
                "note": r.note,
            },
            default=str,
            ensure_ascii=False,
        )

    def _execute(sql: str, question: str = "") -> str:
        res = client.run_sql(space.space_id, sql)
        if not res.get("error"):
            put_saved(space.space_id, question, sql)
            res["saved_as_tool"] = True
        res.update({"sql": sql, "question": question})
        return json.dumps(res, default=str, ensure_ascii=False)

    tools = [
        StructuredTool.from_function(
            func=_run_saved,
            name="run_saved_sql",
            description=(
                f"Check for and run a previously APPROVED SQL query for the "
                f"'{space.name}' data, matching the question. Returns rows if a "
                f"saved query exists (no approval needed), else a note to generate. "
                f"ALWAYS call this FIRST for a data question."
            ),
            args_schema=_QuestionInput,
        ),
        StructuredTool.from_function(
            func=_generate,
            name="genie_generate_sql",
            description=(
                f"Ask Databricks Genie to generate candidate SQL for the "
                f"'{space.name}' data from a natural-language question. Returns the "
                f"SQL and a description. Does NOT require approval. Call this when "
                f"run_saved_sql reports no saved query."
            ),
            args_schema=_QuestionInput,
        ),
        StructuredTool.from_function(
            func=_execute,
            name="execute_sql",
            description=(
                f"Execute SQL against the '{space.name}' data warehouse and return "
                f"rows. A human will APPROVE, EDIT, or REJECT this SQL before it "
                f"runs. Pass the SQL from genie_generate_sql and the original "
                f"question. On success the query is saved for instant reuse."
            ),
            args_schema=_ExecuteInput,
        ),
    ]
    return tools, dict(EXECUTE_INTERRUPT)
