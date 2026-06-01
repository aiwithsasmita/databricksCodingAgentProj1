"""Loader + query layer over the ingested CMS datasets (public-domain CMS data).

Datasets live in ``data/cms/`` and are produced by ``scripts/ingest_cms.py`` from
the official CMS IPPS Final Rule files (Table 5 = MS-DRG catalog; Tables 6 =
ICD-10 / CC / MCC changes) plus a verified per-year rule-highlights file.

Covers FY2023-FY2026 (MS-DRG v40-v43).
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

_DIR = Path(__file__).resolve().parent.parent / "data" / "cms"
LATEST_FY = "2026"
FYS = ["2023", "2024", "2025", "2026"]


def _load(name: str) -> dict | list:
    path = _DIR / name
    if not path.exists():
        return {} if name.endswith(".json") else []
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _catalog() -> dict:
    return _load("ms_drg_catalog.json")  # {fy: [records]}


@lru_cache(maxsize=1)
def _catalog_index() -> dict:
    return {fy: {r["drg"]: r for r in recs} for fy, recs in _catalog().items()}


@lru_cache(maxsize=1)
def _changes() -> list:
    return _load("drg_changes.json")


@lru_cache(maxsize=1)
def _rules() -> dict:
    return _load("ipps_rules.json")


@lru_cache(maxsize=1)
def _cc_mcc() -> dict:
    return _load("cc_mcc_list.json")


@lru_cache(maxsize=1)
def _icd10() -> dict:
    return _load("icd10_updates.json")


@lru_cache(maxsize=1)
def _cc_mcc_changes() -> dict:
    return _load("cc_mcc_changes.json")


def available() -> bool:
    return bool(_catalog())


def _norm_fy(fy) -> str:
    fy = str(fy or LATEST_FY).strip()
    if fy.startswith("FY"):
        fy = fy[2:]
    return fy if fy in FYS else LATEST_FY


def _norm_drg(drg) -> str:
    s = "".join(ch for ch in str(drg) if ch.isdigit())
    return f"{int(s):03d}" if s else str(drg).strip()


# --- queries ---------------------------------------------------------------
def drg_change_history(drg: str) -> list[dict]:
    return [c for c in _changes() if c.get("drg") == drg]


def get_drg(drg: str, fy=LATEST_FY) -> dict:
    fy = _norm_fy(fy)
    drg = _norm_drg(drg)
    rec = _catalog_index().get(fy, {}).get(drg)
    out = {"fy": fy, "drg": drg}
    if rec:
        out["record"] = rec
        out["history"] = drg_change_history(drg)
    else:
        # Was it deleted? Find the last FY it existed.
        existed = [y for y in FYS if drg in _catalog_index().get(y, {})]
        out["found"] = False
        out["note"] = (
            f"MS-DRG {drg} is not in the FY{fy} catalog."
            + (f" It existed in FY{existed[-1]} and was later deleted." if existed else "")
        )
        out["history"] = drg_change_history(drg)
        return out
    out["found"] = True
    return out


def get_changes(fy=LATEST_FY, change_type: str = "all") -> dict:
    fy = _norm_fy(fy)
    items = [c for c in _changes() if c.get("fy") == fy]
    if change_type and change_type != "all":
        items = [c for c in items if c.get("change_type") == change_type]
    summary: dict[str, int] = {}
    for c in items:
        summary[c["change_type"]] = summary.get(c["change_type"], 0) + 1
    return {"fy": fy, "change_type": change_type, "summary": summary, "changes": items}


def get_rule(fy=LATEST_FY) -> dict:
    fy = _norm_fy(fy)
    rule = _rules().get(fy)
    return rule or {"fy": fy, "note": "No rule summary available for that fiscal year."}


def search_drgs(query: str, fy=LATEST_FY, limit: int = 25) -> dict:
    fy = _norm_fy(fy)
    q = (query or "").strip().lower()
    recs = _catalog().get(fy, [])
    hits = [r for r in recs if q in r["title"].lower()] if q else []
    return {"fy": fy, "query": query, "count": len(hits), "results": hits[:limit]}


def compare_drg(drg: str, fy1: str, fy2: str) -> dict:
    drg = _norm_drg(drg)
    fy1, fy2 = _norm_fy(fy1), _norm_fy(fy2)
    a = _catalog_index().get(fy1, {}).get(drg)
    b = _catalog_index().get(fy2, {}).get(drg)
    diffs = {}
    if a and b:
        for k in ("title", "severity", "mdc", "type", "weight"):
            if a.get(k) != b.get(k):
                diffs[k] = {f"fy{fy1}": a.get(k), f"fy{fy2}": b.get(k)}
    return {
        "drg": drg,
        f"fy{fy1}": a or "not present",
        f"fy{fy2}": b or "not present",
        "differences": diffs or "no field-level differences",
    }


def cc_mcc_status(icd10: str) -> dict:
    code = (icd10 or "").strip().upper()
    data = _cc_mcc()
    mcc, cc = data.get("mcc", {}), data.get("cc", {})
    if code in mcc:
        return {"icd10": code, "tier": "MCC", "description": mcc[code], "fy": data.get("fy")}
    if code in cc:
        return {"icd10": code, "tier": "CC", "description": cc[code], "fy": data.get("fy")}
    return {"icd10": code, "tier": "neither (NonCC)", "fy": data.get("fy")}


def get_icd10_updates(fy=LATEST_FY) -> dict:
    fy = _norm_fy(fy)
    upd = _icd10().get(fy)
    if upd:
        return {"fy": fy, **upd}
    return {"fy": fy, "note": f"No ICD-10 update data for FY{fy} (loaded: {', '.join(FYS)})."}


def get_cc_mcc_changes(fy=LATEST_FY, limit: int = 25) -> dict:
    """Per-year additions/deletions to the MCC and CC lists (counts + a sample)."""
    fy = _norm_fy(fy)
    ch = _cc_mcc_changes().get(fy)
    if not ch:
        return {"fy": fy, "note": f"No CC/MCC change data for FY{fy}."}

    def cap(items: list) -> dict:
        return {"count": len(items), "sample": items[:limit]}

    return {
        "fy": fy,
        "mcc_additions": cap(ch.get("mcc_additions", [])),
        "mcc_deletions": cap(ch.get("mcc_deletions", [])),
        "cc_additions": cap(ch.get("cc_additions", [])),
        "cc_deletions": cap(ch.get("cc_deletions", [])),
    }
