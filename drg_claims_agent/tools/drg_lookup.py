"""
DRG Lookup Tool -- Reference data for ALL 770 MS-DRG codes + 65,925
ICD-10 to DRG mappings + 18,432 CC/MCC classifications.

Data sources (all from CMS FY 2026 IPPS Final Rule):
  - drg_reference_data.json: Table 5 weights/LOS for all 770 DRGs
  - icd_to_drg.json: Appendix B ICD-10 to DRG mappings (65,925 codes)
  - cc_mcc_list.json: Appendix C CC/MCC classification (18,432 codes)
"""

import json
import os
from langchain_core.tools import tool

_DIR = os.path.dirname(__file__)

with open(os.path.join(_DIR, "drg_reference_data.json"), "r", encoding="utf-8") as _f:
    MS_DRG_REFERENCE: dict = json.load(_f)

with open(os.path.join(_DIR, "icd_to_drg.json"), "r", encoding="utf-8") as _f:
    ICD_TO_DRG: dict = json.load(_f)

with open(os.path.join(_DIR, "cc_mcc_list.json"), "r", encoding="utf-8") as _f:
    CC_MCC_LIST: dict = json.load(_f)

# Stroke family corrected: 064 (MCC) / 065 (CC+TPA) / 066 (base)
# DRG 067 is Precerebral Occlusion -- a DIFFERENT condition
DRG_FAMILIES = {
    "hip_knee_replacement": {
        "label": "Major Hip and Knee Joint Replacement",
        "mcc": "469",
        "cc": None,
        "base": "470",
        "icd_prefixes": ["M16", "M17"],
    },
    "heart_failure": {
        "label": "Heart Failure and Shock",
        "mcc": "291",
        "cc": "292",
        "base": "293",
        "icd_prefixes": ["I50"],
    },
    "pneumonia": {
        "label": "Simple Pneumonia and Pleurisy",
        "mcc": "193",
        "cc": "194",
        "base": "195",
        "icd_prefixes": ["J13", "J14", "J15", "J16", "J18"],
    },
    "sepsis": {
        "label": "Septicemia or Severe Sepsis Without MV >96 Hours",
        "mcc": "871",
        "cc": "872",
        "base": None,
        "icd_prefixes": ["A40", "A41"],
    },
    "stroke": {
        "label": "Intracranial Hemorrhage or Cerebral Infarction",
        "mcc": "064",
        "cc": "065",
        "base": "066",
        "icd_prefixes": ["I60", "I61", "I62", "I63"],
    },
    "uti": {
        "label": "Kidney and Urinary Tract Infections",
        "mcc": "689",
        "cc": None,
        "base": "690",
        "icd_prefixes": ["N10", "N39.0"],
    },
}

_DRG_TO_FAMILY = {}
for fam_name, fam in DRG_FAMILIES.items():
    for tier in ("mcc", "cc", "base"):
        code = fam[tier]
        if code:
            _DRG_TO_FAMILY[code] = (fam_name, tier)


@tool
def drg_family_lookup(drg_code: str) -> str:
    """Look up the DRG family for a given MS-DRG code and return all
    severity tiers (MCC / CC / base) with their relative weights.

    Use this to understand DRG shift -- which severity levels exist
    for the same clinical condition and the payment spread between them.

    Args:
        drg_code: Any MS-DRG code in a family (e.g. '291', '292', '293').
    """
    code = drg_code.strip().replace("MS-DRG ", "").replace("DRG ", "")
    entry = _DRG_TO_FAMILY.get(code)
    if not entry:
        available = ", ".join(sorted(_DRG_TO_FAMILY.keys()))
        return (
            f"DRG '{code}' is not part of a known DRG family. "
            f"Known family members: {available}. "
            f"Available families: {', '.join(DRG_FAMILIES.keys())}"
        )
    fam_name, _ = entry
    fam = DRG_FAMILIES[fam_name]
    tiers = {}
    for tier in ("mcc", "cc", "base"):
        tier_code = fam[tier]
        if tier_code and tier_code in MS_DRG_REFERENCE:
            ref = MS_DRG_REFERENCE[tier_code]
            tiers[tier] = {
                "drg_code": tier_code,
                "description": ref["description"],
                "relative_weight": ref["relative_weight"],
                "geometric_mean_los": ref["geometric_mean_los"],
            }

    weights = [t["relative_weight"] for t in tiers.values()]
    spread = ((max(weights) - min(weights)) / min(weights) * 100) if len(weights) > 1 else 0

    return json.dumps({
        "family": fam_name,
        "label": fam["label"],
        "icd_prefixes": fam["icd_prefixes"],
        "tiers": tiers,
        "weight_spread_pct": round(spread, 1),
        "shift_risk": "HIGH" if spread > 80 else "MODERATE" if spread > 40 else "LOW",
    }, indent=2)


@tool
def drg_lookup(drg_code: str) -> str:
    """Look up CMS Table 5 reference data for a given MS-DRG code.

    Returns: description, relative weight, geometric and arithmetic mean LOS,
    MDC, and type (medical/surgical) from `drg_reference_data.json` (all 770 DRGs).
    For ICD-10 principal diagnosis vs DRG pairing use `icd_code_validate` (Appendix B).
    For CC/MCC on a secondary code use `cc_mcc_check` (Appendix C).

    Args:
        drg_code: The MS-DRG code to look up (e.g. '470', '871').
    """
    code = drg_code.strip().replace("MS-DRG ", "").replace("DRG ", "")
    info = MS_DRG_REFERENCE.get(code)
    if not info:
        available = ", ".join(sorted(MS_DRG_REFERENCE.keys()))
        return (
            f"DRG code '{code}' not found in reference data. "
            f"Available codes: {available}"
        )
    return json.dumps(
        {"drg_code": code, **info},
        indent=2,
    )
