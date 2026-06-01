"""
ICD-10 to DRG Validation Tool -- Clinical coding compliance checker.

Uses the full CMS Appendix B (65,925 ICD-10 to DRG mappings) and
Appendix C (18,432 CC/MCC classifications) from the MS-DRG V43.1
Definitions Manual for validation.
"""

import json
from langchain_core.tools import tool
from tools.drg_lookup import ICD_TO_DRG, CC_MCC_LIST, MS_DRG_REFERENCE


@tool
def icd_code_validate(icd_code: str, drg_code: str) -> str:
    """Validate whether a principal ICD-10 diagnosis code is clinically
    appropriate for the assigned MS-DRG code.

    Uses the official CMS Appendix B (65,925 ICD-10 to DRG mappings)
    to check if the ICD code maps to the given DRG. This works for
    ALL 770 MS-DRGs, not just a subset.

    Returns a validation result with:
    - valid: whether the pairing is appropriate per CMS grouper logic
    - reasoning: explanation of why it matches or doesn't
    - suggested_drgs: if invalid, which DRGs the ICD code actually maps to

    Use this tool for DRG coding audits and compliance checks.

    Args:
        icd_code: The ICD-10-CM principal diagnosis code (e.g. 'M16.11', 'A41.9').
        drg_code: The MS-DRG code assigned to the claim (e.g. '470', '871').
    """
    code = drg_code.strip().replace("MS-DRG ", "").replace("DRG ", "")
    icd = icd_code.strip().upper().replace(".", "")

    drg_info = MS_DRG_REFERENCE.get(code)
    drg_desc = drg_info["description"] if drg_info else f"Unknown DRG {code}"

    icd_entry = ICD_TO_DRG.get(icd)
    if not icd_entry:
        return json.dumps({
            "valid": None,
            "icd_code": icd,
            "drg_code": code,
            "drg_description": drg_desc,
            "error": (
                f"ICD-10 code '{icd}' not found in CMS Appendix B "
                f"({len(ICD_TO_DRG)} codes loaded). Check the code format -- "
                f"CMS uses codes without dots (e.g., M1611 not M16.11)."
            ),
        }, indent=2)

    all_drgs = set()
    for mapping in icd_entry["mappings"]:
        all_drgs.update(mapping["drgs"])

    is_valid = code in all_drgs

    if is_valid:
        return json.dumps({
            "valid": True,
            "icd_code": icd,
            "icd_description": icd_entry["description"],
            "drg_code": code,
            "drg_description": drg_desc,
            "reasoning": (
                f"ICD-10 code {icd} ({icd_entry['description']}) is a valid "
                f"principal diagnosis for MS-DRG {code} ({drg_desc}) per "
                f"CMS Appendix B. Coding appears appropriate."
            ),
            "all_possible_drgs": sorted(all_drgs),
        }, indent=2)

    suggested = []
    for drg in sorted(all_drgs):
        ref = MS_DRG_REFERENCE.get(drg)
        if ref:
            suggested.append({
                "drg_code": drg,
                "description": ref["description"],
                "relative_weight": ref["relative_weight"],
            })

    return json.dumps({
        "valid": False,
        "icd_code": icd,
        "icd_description": icd_entry["description"],
        "drg_code": code,
        "drg_description": drg_desc,
        "reasoning": (
            f"ICD-10 code {icd} ({icd_entry['description']}) does NOT map "
            f"to MS-DRG {code} ({drg_desc}) per CMS Appendix B. "
            f"This ICD code maps to DRGs: {sorted(all_drgs)}. "
            f"This is a DRG coding error."
        ),
        "suggested_drgs": suggested,
    }, indent=2)


@tool
def cc_mcc_check(icd_code: str) -> str:
    """Check whether an ICD-10 diagnosis code is classified as CC
    (Complication/Comorbidity), MCC (Major CC), or non-CC by CMS.

    Uses the official CMS Appendix C (18,432 CC/MCC classifications).
    This is important for auditing MCC-level DRG assignments -- a claim
    coded with an MCC-level DRG should have at least one qualifying MCC
    on the secondary diagnosis list.

    Args:
        icd_code: The ICD-10-CM diagnosis code to check (e.g. 'N17.9', 'J96.01').
    """
    icd = icd_code.strip().upper().replace(".", "")

    entry = CC_MCC_LIST.get(icd)
    if entry:
        return json.dumps({
            "icd_code": icd,
            "classification": entry["level"],
            "description": entry["description"],
            "severity_impact": (
                "Bumps DRG to highest severity tier (MCC level)"
                if entry["level"] == "MCC"
                else "Bumps DRG to middle severity tier (CC level)"
            ),
        }, indent=2)

    return json.dumps({
        "icd_code": icd,
        "classification": "Non-CC",
        "description": "Not found in CMS CC/MCC list",
        "severity_impact": "No severity bump -- does not affect DRG assignment",
    }, indent=2)
