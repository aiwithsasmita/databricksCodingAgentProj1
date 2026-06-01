"""Parses the configured Genie space registry from settings.

``GENIE_SPACES`` is a JSON array string, e.g.:

    [
      {"name": "drg_shift", "space_id": "01ef...", "agent": "drg",
       "description": "DRG severity tier mix and coding shift by FY, US + statewise."},
      {"name": "taxi", "space_id": "01ef...", "agent": "data",
       "description": "NYC taxi trips dataset."}
    ]

Each entry becomes a tool ``genie_<name>`` routed to the named subagent (default
``drg``). Uniqueness is enforced per ``(agent, name)`` so the same short name can
be reused across different agents. Malformed config logs a warning and is skipped
(the agents then fall back to the Stage-1 mock tools).
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

from ..config import get_settings

logger = logging.getLogger(__name__)

_NAME_RE = re.compile(r"^[a-z0-9_]+$")
_MAX_DESC = 300  # cap config-provided descriptions before they reach the LLM


def _clean_desc(text: str) -> str:
    """Collapse whitespace / strip control chars and cap length.

    Descriptions come from config and are interpolated into LLM-facing tool
    descriptions, so treat them as untrusted data: single-line, length-capped.
    """
    text = re.sub(r"[\x00-\x1f\x7f]", " ", text)  # control chars -> space
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > _MAX_DESC:
        text = text[:_MAX_DESC].rstrip() + "…"
    return text


@dataclass(frozen=True)
class GenieSpace:
    name: str
    space_id: str
    description: str
    agent: str = "drg"

    @property
    def tool_name(self) -> str:
        return f"genie_{self.name}"


def load_genie_spaces() -> list[GenieSpace]:
    """Return the validated list of configured Genie spaces (possibly empty)."""
    raw = (get_settings().GENIE_SPACES or "").strip()
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.warning("GENIE_SPACES is not valid JSON (%s); ignoring.", exc)
        return []
    if not isinstance(parsed, list):
        logger.warning("GENIE_SPACES must be a JSON array; ignoring.")
        return []

    spaces: list[GenieSpace] = []
    seen: set[tuple[str, str]] = set()  # (agent, name)
    for i, item in enumerate(parsed):
        if not isinstance(item, dict):
            logger.warning("GENIE_SPACES[%d] is not an object; skipping.", i)
            continue
        name = str(item.get("name", "")).strip().lower()
        space_id = str(item.get("space_id", "")).strip()
        description = _clean_desc(str(item.get("description", "")))
        agent = str(item.get("agent", "drg")).strip().lower() or "drg"

        if not name or not space_id:
            logger.warning("GENIE_SPACES[%d] missing name/space_id; skipping.", i)
            continue
        if " " in space_id:
            logger.warning(
                "GENIE_SPACES[%d] space_id contains whitespace; skipping.", i
            )
            continue
        if not _NAME_RE.match(name):
            logger.warning(
                "GENIE_SPACES[%d] name %r must be lowercase a-z0-9_; skipping.",
                i,
                name,
            )
            continue
        if not _NAME_RE.match(agent):
            logger.warning(
                "GENIE_SPACES[%d] agent %r must be lowercase a-z0-9_; skipping.",
                i,
                agent,
            )
            continue
        if (agent, name) in seen:
            logger.warning(
                "GENIE_SPACES duplicate (agent=%s, name=%s); skipping.", agent, name
            )
            continue
        seen.add((agent, name))
        spaces.append(
            GenieSpace(
                name=name,
                space_id=space_id,
                description=description or f"Genie space '{name}'.",
                agent=agent,
            )
        )
    return spaces
