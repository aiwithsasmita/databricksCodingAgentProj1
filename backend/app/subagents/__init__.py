"""Subagent definitions for the supervisor deep agent.

DRG and data agents are built lazily (functions) because their tools depend on
runtime Genie configuration. Appeals/call-center/context have no live data
dependency yet, so they remain static dicts.
"""
from .appeals_agent import APPEALS_SUBAGENT
from .callcenter_agent import CALLCENTER_SUBAGENT
from .context_agent import CONTEXT_SUBAGENT
from .data_agent import build_data_subagent
from .drg_agent import build_drg_subagent
from .search_agent import SEARCH_SUBAGENT

__all__ = [
    "build_drg_subagent",
    "build_data_subagent",
    "APPEALS_SUBAGENT",
    "CALLCENTER_SUBAGENT",
    "CONTEXT_SUBAGENT",
    "SEARCH_SUBAGENT",
]
