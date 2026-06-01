"""Tests for the CMS context store/tools (over ingested official CMS data).

These run against the real ingested datasets in data/cms/ (built by
scripts/ingest_cms.py). They assert known FY2026 facts so a bad re-ingest is
caught.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

from app import cms_store  # noqa: E402

pytestmark = pytest.mark.skipif(
    not cms_store.available(), reason="CMS datasets not ingested (run scripts/ingest_cms.py)"
)


def test_fy2026_added_drgs():
    ch = cms_store.get_changes("2026", "added")
    added = {c["drg"] for c in ch["changes"]}
    assert {"209", "213", "318", "359", "360"} <= added


def test_fy2026_deleted_includes_hypertensive_encephalopathy():
    ch = cms_store.get_changes("2026", "deleted")
    deleted = {c["drg"] for c in ch["changes"]}
    assert {"077", "078", "079"} <= deleted


def test_rule_fy2026_facts():
    r = cms_store.get_rule("2026")
    assert r["cms_id"] == "CMS-1833-F"
    assert r["operating_update_pct"] == 2.6
    assert r["effective_date"] == "2025-10-01"
    assert "wage_index" in r["provider_payment_factors"]


def test_drg_lookup_and_severity():
    d = cms_store.get_drg("871", "2026")
    assert d["found"] and "SEPTICEMIA" in d["record"]["title"].upper()
    assert d["record"]["severity"] == "mcc"


def test_deleted_drg_reports_history():
    d = cms_store.get_drg("077", "2026")
    assert d["found"] is False
    assert any(c["change_type"] == "deleted" for c in d["history"])


def test_cc_mcc_status():
    assert cms_store.cc_mcc_status("R65.20")["tier"] == "MCC"
    assert cms_store.cc_mcc_status("N17.9")["tier"] == "CC"
    assert "neither" in cms_store.cc_mcc_status("Z00.00")["tier"].lower()


def test_tool_returns_json():
    from app.tools.cms_tools import cms_drg_changes

    out = json.loads(cms_drg_changes.invoke({"fiscal_year": "2026", "change_type": "added"}))
    assert out["summary"].get("added", 0) >= 5


def test_icd10_updates_all_years():
    # Multi-year ICD-10 update counts are loaded for every FY2023-2026.
    for fy in ("2023", "2024", "2025", "2026"):
        upd = cms_store.get_icd10_updates(fy)
        assert upd.get("new_diagnosis_codes", 0) > 0, f"FY{fy} missing ICD-10 counts"
        assert upd.get("cc_list_size", 0) > 10000


def test_cc_mcc_changes_per_year():
    ch = cms_store.get_cc_mcc_changes("2026")
    assert ch["mcc_additions"]["count"] >= 1
    assert isinstance(ch["cc_additions"]["sample"], list)
    # FY2024 had MCC deletions in the source tables.
    ch24 = cms_store.get_cc_mcc_changes("2024")
    assert ch24["mcc_deletions"]["count"] >= 1
