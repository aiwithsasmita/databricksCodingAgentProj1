"""STAGE-1 MOCK TOOLS.

Every function here returns deterministic, illustrative data so the agent
architecture (routing, subagents, skills, streaming) can be exercised end-to-end
*without* a live Databricks/Genie connection or a real Excel file.

In Stage 2+ each of these is replaced by a real tool:
  - drg_shift_lookup / icd_driver_lookup / provider_utilization_lookup
        -> Databricks Genie queries (one per Genie space)
  - cms_context_lookup
        -> pandas/openpyxl read of the local CMS reference Excel
  - appeals_lookup / callcenter_lookup
        -> their respective Genie spaces / warehouses

Keep the *signatures* stable so the swap is a drop-in.
"""
from __future__ import annotations

import json

from langchain_core.tools import tool

# A clear banner the model can echo so users know data is not yet live.
_MOCK = "STAGE-1 ILLUSTRATIVE MOCK DATA — not yet wired to live Databricks."


# ---------------------------------------------------------------------------
# DRG agent tools
# ---------------------------------------------------------------------------
@tool
def drg_shift_lookup(drg_code: str, drg_family: str = "") -> str:
    """Return the severity-tier coding mix by fiscal year (2023-2026) for a DRG,
    nationally and by state, to reveal shift from no-CC/MCC -> CC -> MCC.

    Args:
        drg_code: The MS-DRG code, e.g. "871".
        drg_family: Optional DRG family / base name, e.g. "Septicemia".
    """
    data = {
        "_note": _MOCK,
        "drg_code": drg_code,
        "drg_family": drg_family or "Septicemia or Severe Sepsis",
        "tier_definition": "Tier 1 = no CC/MCC, Tier 2 = with CC, Tier 3 = with MCC",
        "national_tier_mix_pct": {
            "2023": {"tier1_no_cc_mcc": 14.0, "tier2_cc": 31.0, "tier3_mcc": 55.0},
            "2024": {"tier1_no_cc_mcc": 12.5, "tier2_cc": 29.5, "tier3_mcc": 58.0},
            "2025": {"tier1_no_cc_mcc": 10.5, "tier2_cc": 27.5, "tier3_mcc": 62.0},
            "2026": {"tier1_no_cc_mcc": 9.0, "tier2_cc": 25.0, "tier3_mcc": 66.0},
        },
        "national_shift_summary": (
            "Clear upward severity migration: MCC tier rose from 55% (2023) to "
            "66% (2026), +11 pts, while the no-CC/MCC tier fell from 14% to 9%."
        ),
        "statewise_mcc_share_pct": {
            "TX": {"2023": 57, "2024": 61, "2025": 67, "2026": 73},
            "FL": {"2023": 56, "2024": 60, "2025": 65, "2026": 70},
            "CA": {"2023": 54, "2024": 56, "2025": 59, "2026": 61},
            "NY": {"2023": 53, "2024": 55, "2025": 57, "2026": 59},
        },
        "statewise_shift_summary": (
            "TX and FL show the steepest MCC migration (+16 and +14 pts), well "
            "above CA and NY (+7 and +6 pts)."
        ),
    }
    return json.dumps(data, indent=2)


@tool
def icd_driver_lookup(drg_code: str) -> str:
    """Return the ICD-10 diagnosis codes most responsible for the upward
    severity (MCC) migration in a DRG.

    Args:
        drg_code: The MS-DRG code, e.g. "871".
    """
    data = {
        "_note": _MOCK,
        "drg_code": drg_code,
        "top_mcc_drivers": [
            {
                "icd10": "R65.20",
                "label": "Severe sepsis without septic shock",
                "share_of_mcc_growth_pct": 38,
                "yoy_volume_change_pct": {"2024": 9, "2025": 14, "2026": 19},
            },
            {
                "icd10": "R65.21",
                "label": "Severe sepsis with septic shock",
                "share_of_mcc_growth_pct": 27,
                "yoy_volume_change_pct": {"2024": 7, "2025": 11, "2026": 16},
            },
            {
                "icd10": "N17.9",
                "label": "Acute kidney failure, unspecified",
                "share_of_mcc_growth_pct": 18,
                "yoy_volume_change_pct": {"2024": 6, "2025": 8, "2026": 10},
            },
            {
                "icd10": "J96.00",
                "label": "Acute respiratory failure, unspecified",
                "share_of_mcc_growth_pct": 17,
                "yoy_volume_change_pct": {"2024": 5, "2025": 7, "2026": 9},
            },
        ],
        "driver_summary": (
            "R65.20 / R65.21 (severe sepsis) account for ~65% of MCC growth. "
            "Their rapid rise without a matching rise in dialysis or ventilator "
            "procedures is a flag worth a clinical-evidence check."
        ),
    }
    return json.dumps(data, indent=2)


@tool
def provider_utilization_lookup(drg_code: str, icd10: str = "", state: str = "") -> str:
    """Return provider/TIN utilization of a high-severity code so national and
    state averages can be computed and super-outliers identified.

    Args:
        drg_code: The MS-DRG code, e.g. "871".
        icd10: Optional driving ICD-10 code to focus on, e.g. "R65.20".
        state: Optional 2-letter state filter, e.g. "TX".
    """
    data = {
        "_note": _MOCK,
        "drg_code": drg_code,
        "icd10": icd10 or "R65.20",
        "state": state or "TX",
        "benchmarks_mcc_rate_pct": {
            "national_avg_2026": 66.0,
            "state_avg_2026": 73.0,
        },
        "providers": [
            {
                "tin": "75-1234567",
                "name": "Lone Star Medical Center",
                "state": "TX",
                "mcc_rate_by_year_pct": {"2023": 58, "2024": 64, "2025": 78, "2026": 92},
                "own_history_delta_pts": 34,
                "vs_state_avg_pts": 19,
                "flag": "SUPER-OUTLIER",
            },
            {
                "tin": "75-7654321",
                "name": "Gulf Coast Regional",
                "state": "TX",
                "mcc_rate_by_year_pct": {"2023": 60, "2024": 63, "2025": 71, "2026": 88},
                "own_history_delta_pts": 28,
                "vs_state_avg_pts": 15,
                "flag": "SUPER-OUTLIER",
            },
            {
                "tin": "75-2468013",
                "name": "Hill Country Health",
                "state": "TX",
                "mcc_rate_by_year_pct": {"2023": 57, "2024": 60, "2025": 64, "2026": 69},
                "own_history_delta_pts": 12,
                "vs_state_avg_pts": -4,
                "flag": "within norms",
            },
        ],
        "outlier_method": (
            "A provider is a SUPER-OUTLIER when its 2026 MCC rate is >15 pts above "
            "the state average AND has climbed >25 pts versus its own 2023 baseline."
        ),
    }
    return json.dumps(data, indent=2)


# ---------------------------------------------------------------------------
# Appeals agent tool
# ---------------------------------------------------------------------------
@tool
def appeals_lookup(query: str) -> str:
    """Return appeals metrics (status, volumes, overturn rates, reasons).

    Args:
        query: A natural-language description of the appeals question.
    """
    data = {
        "_note": _MOCK,
        "query": query,
        "open_appeals": 1287,
        "overturn_rate_pct_2026": 34.5,
        "upheld_rate_pct_2026": 65.5,
        "avg_days_to_decision": 21,
        "top_reasons": [
            {"reason": "DRG validation / severity downgrade", "share_pct": 41},
            {"reason": "Medical necessity", "share_pct": 26},
            {"reason": "Coding/documentation mismatch", "share_pct": 19},
            {"reason": "Timely filing", "share_pct": 14},
        ],
    }
    return json.dumps(data, indent=2)


# ---------------------------------------------------------------------------
# Call-center agent tool
# ---------------------------------------------------------------------------
@tool
def callcenter_lookup(query: str) -> str:
    """Return call-center metrics (volumes, reasons, handle time, complaints).

    Args:
        query: A natural-language description of the call-center question.
    """
    data = {
        "_note": _MOCK,
        "query": query,
        "calls_last_30d": 48213,
        "avg_handle_time_sec": 372,
        "service_level_pct": 81,
        "top_call_reasons": [
            {"reason": "Claim status", "share_pct": 33},
            {"reason": "Benefit/eligibility", "share_pct": 24},
            {"reason": "Appeal / denial question", "share_pct": 18},
            {"reason": "Billing / cost", "share_pct": 15},
            {"reason": "Other", "share_pct": 10},
        ],
        "complaint_rate_per_1k_calls": 7.4,
    }
    return json.dumps(data, indent=2)


# ---------------------------------------------------------------------------
# Context (CMS reference) agent tool
# ---------------------------------------------------------------------------
@tool
def cms_context_lookup(fiscal_year: str = "2026", change_type: str = "all") -> str:
    """Return CMS MS-DRG reference changes for a fiscal year.

    Args:
        fiscal_year: e.g. "2026".
        change_type: one of "added", "deleted", "recoded", or "all".
    """
    data = {
        "_note": _MOCK + " Later: read from local CMS Excel via pandas/openpyxl.",
        "fiscal_year": fiscal_year,
        "ms_drg_version": "MS-DRG v43 (FY2026)",
        "added": [
            {"drg": "329", "title": "Major Small & Large Bowel Procedures w MCC (revised split)"},
            {"drg": "521", "title": "Hip Replacement w Principal Dx of Hip Fracture w MCC"},
            {"drg": "656", "title": "Kidney & Ureter Procedures for Neoplasm w MCC"},
        ],
        "deleted": [
            {"drg": "984", "title": "Prostatic O.R. Procedure Unrelated to Principal Dx w MCC"},
            {"drg": "985", "title": "Prostatic O.R. Procedure Unrelated to Principal Dx w CC"},
        ],
        "recoded": [
            {"from_drg": "522", "to_drg": "521", "note": "Hip fracture split refined for MCC capture"},
            {"from_drg": "330", "to_drg": "329", "note": "Bowel procedure severity logic updated"},
        ],
    }
    return json.dumps(data, indent=2)
