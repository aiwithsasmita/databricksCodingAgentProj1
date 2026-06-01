"""Unit tests for the DuckDuckGo web_search tool — no network calls."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_web_search_formats_results(monkeypatch):
    from app.tools import search_tools

    fake = [
        {"title": "CMS FY2026 IPPS Final Rule", "url": "https://cms.gov/x", "snippet": "..."},
        {"title": "MS-DRG v43", "url": "https://cms.gov/y", "snippet": "..."},
    ]
    monkeypatch.setattr(search_tools, "_search_langchain", lambda q, n: fake)

    out = json.loads(search_tools.web_search.invoke({"query": "CMS FY2026 IPPS"}))
    assert out["query"] == "CMS FY2026 IPPS"
    assert len(out["results"]) == 2
    assert out["results"][0]["url"] == "https://cms.gov/x"


def test_web_search_falls_back_to_ddgs(monkeypatch):
    from app.tools import search_tools

    def boom(q, n):
        raise RuntimeError("rate limited")

    monkeypatch.setattr(search_tools, "_search_langchain", boom)
    monkeypatch.setattr(
        search_tools, "_search_ddgs", lambda q, n: [{"title": "t", "url": "https://u", "snippet": "s"}]
    )
    out = json.loads(search_tools.web_search.invoke({"query": "q"}))
    assert out["results"][0]["title"] == "t"


def test_web_search_handles_no_results(monkeypatch):
    from app.tools import search_tools

    monkeypatch.setattr(search_tools, "_search_langchain", lambda q, n: [])
    monkeypatch.setattr(search_tools, "_search_ddgs", lambda q, n: [])
    monkeypatch.setattr(search_tools.time, "sleep", lambda *_: None)  # no real backoff
    out = json.loads(search_tools.web_search.invoke({"query": "q"}))
    assert out["results"] == []
    assert "no results" in out["note"].lower()


def test_search_subagent_well_formed():
    from app.subagents import SEARCH_SUBAGENT

    assert SEARCH_SUBAGENT["name"] == "search-agent"
    assert SEARCH_SUBAGENT["tools"]
    assert SEARCH_SUBAGENT["tools"][0].name == "web_search"
