"""Persistent store of human-approved (question -> SQL) "tools".

Once an ad-hoc SQL query is approved (or edited) and executed successfully, it is
saved here keyed by (space_id, normalized question). The next time the same
question is asked, ``run_saved_sql`` finds it and runs it directly — no human
approval needed. This is the "added automatically as a tool" behavior.

Stored as a simple JSON file (thread-safe via a lock). Swap for a DB later.
"""
from __future__ import annotations

import json
import re
import threading
from pathlib import Path

from ..config import get_settings

_lock = threading.Lock()


def _path() -> Path:
    return Path(get_settings().SAVED_QUERIES_PATH)


def normalize(question: str) -> str:
    """Normalize a question so trivial wording differences still match."""
    q = (question or "").strip().lower()
    q = re.sub(r"\s+", " ", q)
    q = q.rstrip("?. ")
    return q


def _key(space_id: str, question: str) -> str:
    return f"{space_id}::{normalize(question)}"


def _load() -> dict:
    p = _path()
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def get_saved(space_id: str, question: str) -> str | None:
    """Return the approved SQL for this question in this space, or None."""
    with _lock:
        entry = _load().get(_key(space_id, question))
    return entry.get("sql") if entry else None


def put_saved(space_id: str, question: str, sql: str) -> None:
    """Persist an approved (question -> SQL) mapping."""
    if not question or not sql:
        return
    with _lock:
        data = _load()
        data[_key(space_id, question)] = {
            "space_id": space_id,
            "question": question,
            "sql": sql,
        }
        p = _path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def list_saved() -> list[dict]:
    with _lock:
        return list(_load().values())
