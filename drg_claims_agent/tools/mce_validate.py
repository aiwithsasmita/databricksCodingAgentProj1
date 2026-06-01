"""
Medicare Code Editor (MCE) v43.1 checks from CMS *Definitions of Medicare Code Edits*.

MCE is the claim-by-claim editor that flags logic errors (age vs diagnosis, unacceptable
PDX, etc.). It complements MS-DRG grouping (Appendix B/C) but is a separate system.
"""

from __future__ import annotations

import json
import os
from langchain_core.tools import tool

_DIR = os.path.dirname(__file__)
with open(os.path.join(_DIR, "mce_reference.json"), "r", encoding="utf-8") as f:
    MCE_DATA: dict = json.load(f)

_AGE = MCE_DATA["age_conflict_lists"]
_MAN = MCE_DATA["manifestation_not_pdx"]
_QADM = MCE_DATA["questionable_admission_pdx"]
_BAD_PDX = MCE_DATA["unacceptable_pdx"]
_SPECIAL = MCE_DATA.get("principal_dx_special_rules", {})


def _norm_icd(code: str) -> str:
    return code.strip().upper().replace(".", "")


def _age_conflict(age: int, icd: str) -> dict | None:
    for bucket, d in _AGE.items():
        if icd not in d:
            continue
        desc = d[icd]
        if bucket == "perinatal" and age != 0:
            return {
                "edit": "4 Age conflict (perinatal list)",
                "detail": f"ICD {icd} is restricted to newborns (age 0). Patient age {age}. {desc}",
            }
        if bucket == "pediatric" and not (0 <= age <= 17):
            return {
                "edit": "4 Age conflict (pediatric list)",
                "detail": f"ICD {icd} is for ages 0-17. Patient age {age}. {desc}",
            }
        if bucket == "maternity" and not (9 <= age <= 64):
            return {
                "edit": "4 Age conflict (maternity list)",
                "detail": f"ICD {icd} is for ages 9-64. Patient age {age}. {desc}",
            }
        if bucket == "adult" and not (15 <= age <= 124):
            return {
                "edit": "4 Age conflict (adult list)",
                "detail": f"ICD {icd} is for ages 15-124. Patient age {age}. {desc}",
            }
    return None


@tool
def mce_code_check(
    icd_code: str,
    is_principal: bool = True,
    patient_age: int | None = None,
    has_secondary_diagnosis: bool | None = None,
) -> str:
    """Screen one ICD-10-CM code against **Medicare Code Editor (MCE) v43.1** rules
    (Definitions of Medicare Code Edits, not MS-DRG grouping).

    Detects, when data is available:
    - **Edit 4 — Age conflict**: ICD is on a perinatal / pediatric / maternity / adult
      list and patient age is outside the expected range
    - **Edit 6 — Manifestation as principal**: code must not be principal diagnosis
    - **Edit 8 — Questionable admission**: diagnosis may be insufficient to justify
      inpatient stay when used as principal
    - **Edit 9 — Unacceptable principal diagnosis**: code is not valid as principal
      (e.g. symptom-only, status, organism-only codes). Exception: **Z51.89** is allowed
      as principal *if* a secondary diagnosis is also present (pass has_secondary_diagnosis).

    Args:
        icd_code: ICD-10-CM code (with or without dot).
        is_principal: If True, apply PDX-only edits (6, 8, 9). If False, only age rules apply.
        patient_age: Patient age in full years, if known (triggers age conflict checks).
        has_secondary_diagnosis: For Z51.89 principal: True if at least one secondary DX exists.
    """
    icd = _norm_icd(icd_code)
    out: dict = {
        "icd_code": icd,
        "mce_version": MCE_DATA.get("mce_version"),
        "source": MCE_DATA.get("source"),
        "flags": [],
    }

    if patient_age is not None:
        ac = _age_conflict(patient_age, icd)
        if ac:
            out["flags"].append(ac)

    if not is_principal:
        return json.dumps(
            {**out, "summary": f"MCE: {len(out['flags'])} issue(s) (principal-only edits skipped)."},
            indent=2,
        )

    if icd in _MAN:
        out["flags"].append(
            {
                "edit": "6 Manifestation not allowed as principal diagnosis",
                "detail": _MAN[icd],
            }
        )

    if icd in _QADM:
        out["flags"].append(
            {
                "edit": "8 Questionable admission (when used as principal)",
                "detail": _QADM[icd],
            }
        )

    if icd == "Z5189":
        if has_secondary_diagnosis is True:
            out.setdefault("notes", []).append(
                "Z51.89 acceptable as principal when a secondary diagnosis is also coded (v43.1)."
            )
        elif has_secondary_diagnosis is False:
            out["flags"].append(
                {
                    "edit": "9 Unacceptable principal — Z51.89 (no secondary diagnosis)",
                    "detail": _SPECIAL.get("Z5189", {}).get(
                        "note",
                        "MCE may return REQUIRES SECONDARY DX.",
                    ),
                }
            )
        else:
            out["flags"].append(
                {
                    "edit": "9 Unacceptable principal — Z51.89 (incomplete check)",
                    "detail": "Pass has_secondary_diagnosis (True/False) to evaluate this edit.",
                }
            )
    elif icd in _BAD_PDX:
        out["flags"].append(
            {
                "edit": "9 Unacceptable principal diagnosis",
                "detail": _BAD_PDX[icd],
            }
        )

    n = len(out["flags"])
    if n == 0:
        out["summary"] = "MCE: no applicable edits triggered for this code as principal (given inputs)."
    else:
        out["summary"] = f"MCE: {n} potential edit(s) — review for billing/coding workflow."

    return json.dumps(out, indent=2)
