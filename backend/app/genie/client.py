"""Thin, robust wrapper over the Databricks Genie Conversation API.

Call sequence (handled by the SDK's ``*_and_wait`` helpers, which poll to a
terminal status for us):

    start_conversation_and_wait(space_id, content) -> GenieMessage
    create_message_and_wait(space_id, conversation_id, content) -> GenieMessage  # follow-ups
    get_message_attachment_query_result(space_id, conversation_id,
        message_id, attachment_id) -> GenieGetMessageQueryResultResponse

Result extraction (verified against the Genie API docs / SDK):
    SQL          -> attachment.query.query
    description  -> attachment.query.description
    text answer  -> attachment.text.content
    columns      -> statement_response.manifest.schema.columns[].name
    rows         -> statement_response.result.data_array   (may be None -> guard)

Important SDK behaviors handled here:
    * ``GenieMessage.status`` is a ``MessageStatus`` *enum* (not a str), so we
      normalize via ``.value`` before comparing — otherwise ``str(status)`` is
      ``"MessageStatus.COMPLETED"`` and never matches.
    * The ``*_and_wait`` helpers RAISE on failure/timeout (``OperationFailed`` /
      ``TimeoutError``) rather than returning a FAILED status, so the except
      block classifies those. The terminal-status branch is kept as defense.
    * ``data_array`` is inline only for small results. Large results (>~25 MB)
      use the EXTERNAL_LINKS disposition; ``data_array`` is empty and we surface
      a clear note instead of silently returning zero rows.
    * Exception text is scrubbed of the host/token before being shown to the
      LLM/UI; full detail is logged server-side.
    * The SDK import is lazy so the backend still boots when databricks-sdk is
      absent or credentials are missing (Genie tools simply aren't offered).
"""
from __future__ import annotations

import json
import logging
import threading
from dataclasses import asdict, dataclass, field
from datetime import timedelta
from functools import lru_cache
from typing import Any, Optional

from ..config import get_settings

logger = logging.getLogger(__name__)

# Terminal statuses (compared against MessageStatus.value strings).
_TERMINAL_OK = {"COMPLETED"}
_TERMINAL_BAD = {"FAILED", "CANCELLED", "QUERY_RESULT_EXPIRED"}


def _status_str(status: Any) -> str:
    """Normalize a MessageStatus enum (or string/None) to its plain value.

    ``MessageStatus.COMPLETED`` -> ``"COMPLETED"``; ``"COMPLETED"`` -> itself.
    """
    return str(getattr(status, "value", None) or status or "")


@dataclass
class GenieResult:
    """Normalized, LLM-friendly result of one Genie question."""

    space: str
    space_id: str
    question: str
    status: str = ""
    sql: Optional[str] = None
    description: Optional[str] = None
    text: Optional[str] = None
    columns: list[str] = field(default_factory=list)
    rows: list[list[Any]] = field(default_factory=list)
    row_count: int = 0
    truncated: bool = False
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None
    error: Optional[str] = None
    note: Optional[str] = None

    def to_json(self) -> str:
        # Compact (no indent) to keep LLM context small; rows already capped.
        return json.dumps(asdict(self), default=str, ensure_ascii=False)


class GenieClient:
    """Wraps a Databricks ``WorkspaceClient`` for Genie calls."""

    def __init__(self) -> None:
        self._w = None  # lazy WorkspaceClient
        self._lock = threading.Lock()
        self._warehouse_cache: dict[str, str] = {}

    # -- availability ------------------------------------------------------
    def available(self) -> bool:
        """True when PAT credentials are configured (read fresh each call)."""
        return get_settings().databricks_configured

    # -- workspace client (lazy, thread-safe) ------------------------------
    def _client(self):
        if self._w is not None:
            return self._w
        with self._lock:
            if self._w is None:
                try:
                    from databricks.sdk import WorkspaceClient
                except ImportError as exc:  # pragma: no cover - env guard
                    raise RuntimeError(
                        "databricks-sdk is not installed. Run "
                        "`pip install databricks-sdk` to enable Genie."
                    ) from exc
                s = get_settings()
                if s.DATABRICKS_HOST and s.DATABRICKS_TOKEN:
                    self._w = WorkspaceClient(
                        host=s.DATABRICKS_HOST, token=s.DATABRICKS_TOKEN
                    )
                else:
                    # Ambient auth (CLI profile / env / OAuth).
                    self._w = WorkspaceClient()
        return self._w

    # -- error scrubbing ---------------------------------------------------
    def _scrub(self, text: str) -> str:
        """Remove the host and token from a string before it leaves the server."""
        s = get_settings()
        for secret in (s.DATABRICKS_TOKEN, s.DATABRICKS_HOST):
            if secret:
                text = text.replace(secret, "***")
        return text

    def _safe_error(self, prefix: str, exc: Exception) -> str:
        return f"{prefix} ({exc.__class__.__name__}): {self._scrub(str(exc))}"

    # -- public API --------------------------------------------------------
    def ask(
        self,
        space_id: str,
        question: str,
        space_name: str = "",
        conversation_id: Optional[str] = None,
    ) -> GenieResult:
        """Ask a Genie space a natural-language question and return a normalized
        result. Never raises for expected runtime failures — errors are captured
        in ``GenieResult.error`` so the agent can react gracefully."""
        result = GenieResult(
            space=space_name or space_id,
            space_id=space_id,
            question=question,
            conversation_id=conversation_id,
        )
        s = get_settings()
        timeout = timedelta(seconds=s.GENIE_TIMEOUT_SECONDS)
        try:
            w = self._client()
            if conversation_id:
                msg = w.genie.create_message_and_wait(
                    space_id, conversation_id, question, timeout=timeout
                )
            else:
                msg = w.genie.start_conversation_and_wait(
                    space_id, question, timeout=timeout
                )
        except TimeoutError as exc:
            logger.warning("Genie timeout: %s", self._scrub(str(exc)))
            result.status = "TIMEOUT"
            result.error = (
                f"Genie did not complete within {s.GENIE_TIMEOUT_SECONDS}s. "
                "Try a more specific or aggregated question."
            )
            return result
        except Exception as exc:  # noqa: BLE001 - report, don't crash the agent
            logger.warning("Genie request failed: %s", self._scrub(str(exc)))
            # The SDK's *_and_wait raises OperationFailed when a message reaches a
            # terminal-bad status; its message embeds the status string.
            if exc.__class__.__name__ == "OperationFailed":
                result.status = "FAILED"
            result.error = self._safe_error("Genie request failed", exc)
            return result

        result.conversation_id = getattr(msg, "conversation_id", None) or conversation_id
        # Prefer the canonical message_id; fall back to legacy id.
        result.message_id = getattr(msg, "message_id", None) or getattr(msg, "id", None)
        result.status = _status_str(getattr(msg, "status", None))

        # Collect text + query attachments.
        attachment_id = None
        for att in (getattr(msg, "attachments", None) or []):
            text_att = getattr(att, "text", None)
            if text_att and getattr(text_att, "content", None):
                result.text = (result.text or "") + text_att.content
            query_att = getattr(att, "query", None)
            if query_att:
                result.sql = getattr(query_att, "query", None) or result.sql
                result.description = (
                    getattr(query_att, "description", None) or result.description
                )
                attachment_id = getattr(att, "attachment_id", None) or attachment_id

        # Defensive: if a terminal-bad status is somehow returned (not raised),
        # surface it.
        if result.status in _TERMINAL_BAD:
            err = getattr(msg, "error", None)
            detail = getattr(err, "error", None) or err
            result.error = (
                f"Genie returned status {result.status}: "
                f"{self._scrub(str(detail)) if detail else 'no detail provided'}"
            )
            return result

        # Fetch tabular rows if there is a query attachment.
        if attachment_id and result.message_id and result.conversation_id:
            self._attach_rows(result, space_id, attachment_id)
        elif attachment_id:
            result.note = (
                "Genie returned a query attachment but rows could not be fetched: "
                "missing conversation_id or message_id in the response."
            )

        if not result.sql and not result.text and not result.rows and not result.error:
            result.note = result.note or (
                "Genie returned no SQL, text, or rows. The question may be out of "
                "scope for this space, or the space needs more curation/examples."
            )
        return result

    # -- helpers -----------------------------------------------------------
    def _attach_rows(self, result: GenieResult, space_id: str, attachment_id: str) -> None:
        try:
            w = self._client()
            resp = w.genie.get_message_attachment_query_result(
                space_id, result.conversation_id, result.message_id, attachment_id
            )
            sr = getattr(resp, "statement_response", None)
            if sr is None:
                result.note = "Query produced no statement_response (no result set)."
                return
            cols, rows, truncated, external = _extract_rows(
                sr, get_settings().GENIE_MAX_ROWS
            )
            result.columns = cols
            result.rows = rows
            result.row_count = len(rows)
            result.truncated = truncated
            if external:
                result.note = (
                    "Result is large and was returned via EXTERNAL_LINKS "
                    "(presigned URLs); inline rows are unavailable. Ask Genie to "
                    "aggregate/limit the result to see rows here."
                )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Genie row fetch failed: %s", self._scrub(str(exc)))
            result.note = self._safe_error("Could not fetch query rows", exc)


    # -- SQL execution (for HITL approve/edit of generated SQL) ------------
    def get_warehouse_id(self, space_id: str) -> Optional[str]:
        """Resolve the SQL warehouse to run statements on: explicit config wins,
        else the warehouse the Genie space is configured with (cached)."""
        s = get_settings()
        if s.GENIE_WAREHOUSE_ID:
            return s.GENIE_WAREHOUSE_ID
        if space_id in self._warehouse_cache:
            return self._warehouse_cache[space_id]
        try:
            space = self._client().genie.get_space(space_id)
            wh = getattr(space, "warehouse_id", None)
            if wh:
                self._warehouse_cache[space_id] = wh
            return wh
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not resolve warehouse for %s: %s", space_id, self._scrub(str(exc)))
            return None

    def run_sql(self, space_id: str, sql: str, max_rows: Optional[int] = None) -> dict:
        """Execute raw SQL on the space's warehouse and return columns/rows.

        Used to run human-approved or human-edited SQL. Returns a dict with
        ``columns``/``rows``/``row_count``/``truncated`` or ``error``.
        """
        s = get_settings()
        cap = max_rows or s.GENIE_MAX_ROWS
        warehouse_id = self.get_warehouse_id(space_id)
        if not warehouse_id:
            return {"error": "No SQL warehouse available (set GENIE_WAREHOUSE_ID)."}
        try:
            w = self._client()
            resp = w.statement_execution.execute_statement(
                warehouse_id=warehouse_id, statement=sql, wait_timeout="30s"
            )
            statement_id = getattr(resp, "statement_id", None)
            state = _statement_state(resp)
            # Poll if still running past the inline wait window.
            import time

            waited = 0
            while state in ("PENDING", "RUNNING") and waited < s.GENIE_TIMEOUT_SECONDS:
                time.sleep(2)
                waited += 2
                resp = w.statement_execution.get_statement(statement_id)
                state = _statement_state(resp)
            if state != "SUCCEEDED":
                err = getattr(getattr(resp, "status", None), "error", None)
                detail = getattr(err, "message", None) or err
                return {
                    "error": f"SQL execution {state or 'failed'}: "
                    f"{self._scrub(str(detail)) if detail else 'no detail'}"
                }
            cols, rows, truncated, _ = _extract_rows(resp, cap)
            return {
                "columns": cols,
                "rows": rows,
                "row_count": len(rows),
                "truncated": truncated,
            }
        except Exception as exc:  # noqa: BLE001
            logger.warning("run_sql failed: %s", self._scrub(str(exc)))
            return {"error": self._safe_error("SQL execution failed", exc)}


def _statement_state(resp: Any) -> str:
    status = getattr(resp, "status", None)
    return _status_str(getattr(status, "state", None)) if status else ""


def _extract_rows(
    statement_response: Any, max_rows: int
) -> tuple[list[str], list[list[Any]], bool, bool]:
    """Return (columns, rows, truncated, used_external_links)."""
    # Columns from manifest.schema.columns[].name
    columns: list[str] = []
    manifest = getattr(statement_response, "manifest", None)
    schema = getattr(manifest, "schema", None) if manifest else None
    schema_cols = getattr(schema, "columns", None) if schema else None
    if schema_cols:
        columns = [getattr(c, "name", "") or "" for c in schema_cols]

    # Rows from result.data_array (guard None per docs).
    result_obj = getattr(statement_response, "result", None)
    data_array = getattr(result_obj, "data_array", None) if result_obj else None
    external = bool(getattr(result_obj, "external_links", None)) if result_obj else False

    rows_src = data_array or []
    truncated = len(rows_src) > max_rows
    rows = [list(r) for r in rows_src[:max_rows]]
    # If we have no inline rows but external links exist, flag it.
    used_external = external and not rows
    return columns, rows, truncated, used_external


@lru_cache
def get_genie_client() -> GenieClient:
    """Return the singleton GenieClient."""
    return GenieClient()
