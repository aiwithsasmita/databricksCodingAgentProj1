"""Context-agent tools over the ingested CMS datasets (FY2023-FY2026).

All data is sourced from the official CMS IPPS Final Rule files (public-domain
U.S. government works) via scripts/ingest_cms.py. Each tool returns JSON.
"""
from __future__ import annotations

import json

from langchain_core.tools import tool

from .. import cms_store


@tool
def cms_drg_lookup(drg: str, fiscal_year: str = "2026") -> str:
    """Look up a single MS-DRG: its title, MDC, MED/SURG type, severity tier,
    relative weight and mean length of stay for a fiscal year, plus its change
    history (added/deleted/retitled). Use for 'what is DRG X' questions.

    Args:
        drg: MS-DRG code, e.g. "871" or "209".
        fiscal_year: 2023, 2024, 2025, or 2026 (default 2026).
    """
    return json.dumps(cms_store.get_drg(drg, fiscal_year), ensure_ascii=False)


@tool
def cms_drg_changes(fiscal_year: str = "2026", change_type: str = "all") -> str:
    """List MS-DRGs CMS added, deleted, or retitled in a fiscal year (vs the prior
    year). Use for 'which DRGs were added/deleted in 2026' questions.

    Args:
        fiscal_year: 2024, 2025, or 2026 (changes are vs the prior FY).
        change_type: "added", "deleted", "retitled", or "all" (default).
    """
    return json.dumps(cms_store.get_changes(fiscal_year, change_type), ensure_ascii=False)


@tool
def cms_ipps_rule(fiscal_year: str = "2026") -> str:
    """Get the IPPS Final Rule summary for a fiscal year: CMS rule id, effective
    date, operating payment update %, total impact, and provider payment factors
    (wage index, DSH/uncompensated care, NTAP, quality programs) plus key changes.
    Use for 'what are the FY2026 rule changes / payment update / provider impacts'.

    Args:
        fiscal_year: 2023, 2024, 2025, or 2026 (default 2026).
    """
    return json.dumps(cms_store.get_rule(fiscal_year), ensure_ascii=False)


@tool
def cms_search_drgs(query: str, fiscal_year: str = "2026") -> str:
    """Search MS-DRGs by keyword in the title (e.g. 'sepsis', 'transplant',
    'aortic'). Returns matching DRGs with code, title, severity and weight.

    Args:
        query: keyword(s) to find in the DRG title.
        fiscal_year: 2023, 2024, 2025, or 2026 (default 2026).
    """
    return json.dumps(cms_store.search_drgs(query, fiscal_year), ensure_ascii=False)


@tool
def cms_compare_drg(drg: str, fiscal_year_1: str, fiscal_year_2: str) -> str:
    """Compare one MS-DRG across two fiscal years to see what changed (title,
    severity, MDC, type, relative weight).

    Args:
        drg: MS-DRG code, e.g. "871".
        fiscal_year_1: earlier FY, e.g. "2023".
        fiscal_year_2: later FY, e.g. "2026".
    """
    return json.dumps(
        cms_store.compare_drg(drg, fiscal_year_1, fiscal_year_2), ensure_ascii=False
    )


@tool
def cms_cc_mcc(icd10_code: str) -> str:
    """Tell whether an ICD-10-CM diagnosis code is an MCC, a CC, or neither
    (NonCC) on the current (FY2026) CMS severity lists.

    Args:
        icd10_code: an ICD-10-CM code, e.g. "R65.20" or "N17.9".
    """
    return json.dumps(cms_store.cc_mcc_status(icd10_code), ensure_ascii=False)


@tool
def cms_icd10_updates(fiscal_year: str = "2026") -> str:
    """Get the count of ICD-10 code updates for a fiscal year (FY2023-FY2026):
    new diagnosis / procedure codes, invalidated codes, revised titles, and
    MCC/CC list size + additions/deletions counts.

    Args:
        fiscal_year: 2023, 2024, 2025, or 2026 (default 2026).
    """
    return json.dumps(cms_store.get_icd10_updates(fiscal_year), ensure_ascii=False)


@tool
def cms_cc_mcc_changes(fiscal_year: str = "2026") -> str:
    """List the specific ICD-10 codes ADDED to or DELETED from the MCC and CC
    severity lists in a fiscal year (counts plus a sample of codes). Use for
    'what was added to the MCC list in FY2024' style questions.

    Args:
        fiscal_year: 2023, 2024, 2025, or 2026 (default 2026).
    """
    return json.dumps(cms_store.get_cc_mcc_changes(fiscal_year), ensure_ascii=False)


CMS_TOOLS = [
    cms_drg_lookup,
    cms_drg_changes,
    cms_ipps_rule,
    cms_search_drgs,
    cms_compare_drg,
    cms_cc_mcc,
    cms_icd10_updates,
    cms_cc_mcc_changes,
]
