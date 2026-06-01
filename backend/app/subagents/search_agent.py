"""Web-search subagent (free DuckDuckGo, no API key).

Static subagent — no runtime data dependency, so it's a plain dict. The
supervisor routes outside-world / current-info questions here.
"""
from __future__ import annotations

from ..prompts import SEARCH_AGENT_PROMPT
from ..tools.search_tools import web_search

SEARCH_SUBAGENT = {
    "name": "search-agent",
    "description": (
        "Searches the public web (DuckDuckGo, no API key) for current events, "
        "news, recent CMS rule changes, definitions, regulations, or any fact "
        "not in the internal data sources. Use for outside-world or up-to-date "
        "information."
    ),
    "system_prompt": SEARCH_AGENT_PROMPT,
    "tools": [web_search],
}
