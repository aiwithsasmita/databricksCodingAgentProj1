"""ICD-10-PCS codes new in MS-DRG / grouper V43.1 (CMS April 2026 web announcement)."""

from __future__ import annotations

import json
import os
from langchain_core.tools import tool

_DIR = os.path.dirname(__file__)
with open(os.path.join(_DIR, "v43_1_new_pcs_codes.json"), "r", encoding="utf-8") as f:
    V43_1_PCS: dict = json.load(f)

_BY_PCS: dict = {e["pcs"]: e for e in V43_1_PCS.get("procedures", [])}


def _norm_pcs(code: str) -> str:
    s = "".join(code.strip().upper().replace(".", ""))
    return s[:7] if len(s) >= 7 else s


@tool
def v43_1_pcs_check(pcs_code: str) -> str:
    """Check whether an ICD-10-PCS code is one of the **80 new procedure codes** in
    **ICD-10 MS-DRG / Grouper & MCE V43.1** effective **April 1, 2026** (CMS web announcement).

    Returns the official short description, O.R. flag when present, and * / ** footnote
    meaning from the publication (* non-O.R. with no MDC/DRG in table; ** non-O.R. that
    may still affect MS-DRG). Use for questions like whether a procedure code is new in FY 2026.

    Args:
        pcs_code: ICD-10-PCS code (7 characters, with or without dots).
    """
    code = _norm_pcs(pcs_code)
    if len(code) != 7 or not any(c.isdigit() for c in code):
        return json.dumps(
            {
                "error": "Provide a 7-character ICD-10-PCS code (e.g. 0F9480D).",
                "input": pcs_code,
            },
            indent=2,
        )
    e = _BY_PCS.get(code)
    if not e:
        return json.dumps(
            {
                "in_v43_1_new_80": False,
                "pcs": code,
                "effective": V43_1_PCS.get("effective_date"),
                "source": V43_1_PCS.get("source"),
            },
            indent=2,
        )
    out = {
        "in_v43_1_new_80": True,
        "pcs": code,
        "description": e.get("description"),
        "or_procedure": e.get("or_procedure"),
        "cms_table_footnote": e.get("cms_table_footnote"),
        "effective": V43_1_PCS.get("effective_date"),
    }
    if e.get("cms_table_footnote"):
        leg = V43_1_PCS.get("footnote_legend", {})
        k = e["cms_table_footnote"]
        if k in leg:
            out["footnote_explanation"] = leg[k]
    return json.dumps(out, indent=2)
