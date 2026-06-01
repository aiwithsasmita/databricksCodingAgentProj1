"""Free web search via DuckDuckGo — no API key required.

Uses LangChain's community DuckDuckGo wrapper as the primary engine and the
``ddgs`` / ``duckduckgo_search`` package as a fallback (the package was renamed
from ``duckduckgo-search`` to ``ddgs``). DuckDuckGo aggressively rate-limits
automated/rapid queries, so we retry with exponential backoff and degrade
gracefully to a clear note instead of failing the agent.
"""
from __future__ import annotations

import json
import logging
import time

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

_MAX_RESULTS = 5
_RETRIES = 3
_BACKOFF_BASE = 1.5  # seconds; grows per attempt to ride out rate limits


def _normalize_lc(raw: list[dict]) -> list[dict]:
    return [
        {"title": r.get("title"), "url": r.get("link"), "snippet": r.get("snippet")}
        for r in raw
    ]


def _search_langchain(query: str, n: int) -> list[dict]:
    """Primary engine (LangChain community wrapper). Raises on failure."""
    from langchain_community.utilities import DuckDuckGoSearchAPIWrapper

    wrapper = DuckDuckGoSearchAPIWrapper(max_results=n)
    return _normalize_lc(wrapper.results(query, n))


def _search_ddgs(query: str, n: int) -> list[dict]:
    """Fallback engine using the ddgs / duckduckgo_search package directly."""
    last_exc: Exception | None = None
    for module in ("ddgs", "duckduckgo_search"):
        try:
            DDGS = __import__(module, fromlist=["DDGS"]).DDGS
        except Exception:  # noqa: BLE001 - module not present, try the other
            continue
        try:
            with DDGS() as ddgs:
                raw = list(ddgs.text(query, max_results=n))
            return [
                {"title": r.get("title"), "url": r.get("href"), "snippet": r.get("body")}
                for r in raw
            ]
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
    if last_exc:
        raise last_exc
    raise RuntimeError("No DuckDuckGo backend available.")


@tool
def web_search(query: str) -> str:
    """Search the public web with DuckDuckGo (free, no API key) and return the
    top results as JSON (title, url, snippet). Use for current events, external
    facts, definitions, regulations, or anything not in the internal data
    sources.

    Args:
        query: The search query.
    """
    last_err: str | None = None
    for attempt in range(_RETRIES):
        for engine in (_search_langchain, _search_ddgs):
            try:
                results = engine(query, _MAX_RESULTS)
                if results:
                    return json.dumps(
                        {"query": query, "results": results}, ensure_ascii=False
                    )
                last_err = "no results"
            except Exception as exc:  # noqa: BLE001
                last_err = f"{type(exc).__name__}: {exc}"
                logger.debug("web_search engine %s failed: %s", engine.__name__, last_err)
        # Rate-limited or empty: wait and retry (skip the wait after the last try).
        if attempt < _RETRIES - 1:
            time.sleep(_BACKOFF_BASE * (attempt + 1))

    logger.warning("web_search exhausted retries for %r: %s", query, last_err)
    return json.dumps(
        {
            "query": query,
            "results": [],
            "note": (
                "Web search returned no results (DuckDuckGo may be rate-limiting; "
                "try again shortly or rephrase the query)."
            ),
        }
    )
