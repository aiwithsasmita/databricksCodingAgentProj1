"""Databricks Genie integration (Stage 2).

Turns natural-language questions into governed SQL + result rows by calling the
Genie Conversation API, and exposes each configured Genie space to the agents as
a LangChain tool.
"""
from .client import GenieClient, GenieResult, get_genie_client
from .hitl_tools import build_data_query_tools
from .registry import GenieSpace, load_genie_spaces
from .tools import genie_tools_for

__all__ = [
    "GenieClient",
    "GenieResult",
    "get_genie_client",
    "load_genie_spaces",
    "GenieSpace",
    "genie_tools_for",
    "build_data_query_tools",
]
