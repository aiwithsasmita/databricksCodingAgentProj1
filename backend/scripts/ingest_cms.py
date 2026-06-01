"""Ingest the official CMS IPPS Table 5 files into a structured MS-DRG catalog.

Table 5 (public-domain CMS data) lists every MS-DRG with its MDC, type
(MED/SURG), title, relative weight, and mean length of stay. We parse FY2023-2026
into `data/cms/ms_drg_catalog.json` and derive `data/cms/drg_changes.json`
(added / deleted / retitled / weight-changed) by diffing consecutive years.

Run once to (re)build the datasets:
    cd backend
    ./.venv/Scripts/python.exe scripts/ingest_cms.py
"""
from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "cms" / "raw"
OUT = ROOT / "data" / "cms"

# fiscal year -> (zip filename, MS-DRG grouper version, CMS rule id)
YEARS = {
    "2023": ("fy2023-table5.zip", "v40", "CMS-1771-F"),
    "2024": ("fy2024-table5.zip", "v41", "CMS-1785-F"),
    "2025": ("fy2025-table5.zip", "v42", "CMS-1808-F"),
    "2026": ("fy2026-table5.zip", "v43", "CMS-1833-F"),
}


def _severity(title: str) -> str:
    t = title.upper()
    if "WITHOUT CC/MCC" in t or "W/O CC/MCC" in t:
        return "none"
    if "WITH MCC" in t or "W MCC" in t:
        return "mcc"
    if "WITH CC/MCC" in t or "W CC/MCC" in t:
        return "cc_or_mcc"
    if "WITH CC" in t or "W CC" in t:
        return "cc"
    if "WITHOUT MCC" in t or "W/O MCC" in t:
        return "not_mcc"
    return "n/a"


def _find_xlsx(zpath: Path) -> str:
    with zipfile.ZipFile(zpath) as z:
        names = [n for n in z.namelist() if n.lower().endswith(".xlsx")]
        # Prefer a "final rule" sheet over a "proposed"/"correction-only" one.
        names.sort(key=lambda n: ("correction" in n.lower(), "proposed" in n.lower()))
        return names[0]


def _colmap(header: list[str]) -> dict:
    idx = {}
    for i, h in enumerate(header):
        hs = str(h).strip().lower()
        if "ms-drg" in hs and "drg" not in idx:
            idx["drg"] = i
        elif hs == "mdc":
            idx["mdc"] = i
        elif hs == "type":
            idx["type"] = i
        elif "title" in hs:
            idx["title"] = i
        elif "geometric" in hs:
            idx["gmlos"] = i
        elif "arithmetic" in hs:
            idx["amlos"] = i
        elif "weight" in hs and "weight" not in idx:
            # prefer the "before cap" / base weight
            if "before" in hs or "cap" not in hs:
                idx["weight"] = i
    if "weight" not in idx:  # fallback: any column with "weight"
        for i, h in enumerate(header):
            if "weight" in str(h).lower():
                idx["weight"] = i
                break
    return idx


def parse_year(fy: str) -> list[dict]:
    zip_name, version, rule_id = YEARS[fy]
    zpath = RAW / zip_name
    sheet = _find_xlsx(zpath)
    with zipfile.ZipFile(zpath) as z:
        with z.open(sheet) as fh:
            raw = pd.read_excel(fh, header=None)
    # Find the header row (first column == "MS-DRG").
    header_row = None
    for i in range(min(8, len(raw))):
        if str(raw.iloc[i, 0]).strip().upper().startswith("MS-DRG"):
            header_row = i
            break
    if header_row is None:
        raise RuntimeError(f"FY{fy}: could not find header row in {sheet}")
    header = list(raw.iloc[header_row].values)
    idx = _colmap(header)
    records = []
    for _, row in raw.iloc[header_row + 1 :].iterrows():
        drg_raw = str(row[idx["drg"]]).strip()
        m = re.match(r"^0*(\d{1,3})$", drg_raw)
        if not m:
            continue
        drg = f"{int(m.group(1)):03d}"
        title = str(row[idx["title"]]).strip()
        if not title or title.lower() == "nan":
            continue

        def num(key):
            try:
                return round(float(row[idx[key]]), 4)
            except (ValueError, TypeError, KeyError):
                return None

        records.append(
            {
                "drg": drg,
                "title": title,
                "mdc": str(row[idx["mdc"]]).strip() if "mdc" in idx else "",
                "type": str(row[idx["type"]]).strip() if "type" in idx else "",
                "severity": _severity(title),
                "weight": num("weight"),
                "gmlos": num("gmlos"),
                "amlos": num("amlos"),
            }
        )
    print(f"FY{fy} ({version}, {rule_id}): {len(records)} MS-DRGs from '{sheet}'")
    return records


def diff_changes(catalog: dict) -> list[dict]:
    changes: list[dict] = []
    fys = sorted(catalog.keys())
    for prev, cur in zip(fys, fys[1:]):
        prev_map = {r["drg"]: r for r in catalog[prev]}
        cur_map = {r["drg"]: r for r in catalog[cur]}
        for drg in sorted(cur_map.keys() - prev_map.keys()):
            changes.append(
                {"fy": cur, "change_type": "added", "drg": drg, "title": cur_map[drg]["title"]}
            )
        for drg in sorted(prev_map.keys() - cur_map.keys()):
            changes.append(
                {"fy": cur, "change_type": "deleted", "drg": drg, "title": prev_map[drg]["title"]}
            )
        for drg in sorted(cur_map.keys() & prev_map.keys()):
            old_t, new_t = prev_map[drg]["title"], cur_map[drg]["title"]
            if old_t != new_t:
                changes.append(
                    {
                        "fy": cur,
                        "change_type": "retitled",
                        "drg": drg,
                        "old_title": old_t,
                        "new_title": new_t,
                    }
                )
    return changes


# fiscal year -> Tables 6 zip filename (downloaded under data/cms/raw)
TABLES6 = {
    "2023": "fy2023-tables6.zip",
    "2024": "fy2024-tables6.zip",
    "2025": "fy2025-tables6.zip",
    "2026": "fy2026-tables6.zip",
}

_HEADER_FIRST = {"diagnosis code", "procedure code", "code"}


def _collect_txts(zpath: Path) -> dict[str, bytes]:
    """Recursively collect every .txt (by basename) from a zip and nested zips.

    Handles both flat layouts (FY2024) and nested sub-zips (FY2023/2025/2026).
    """
    import io

    out: dict[str, bytes] = {}

    def walk(zf: zipfile.ZipFile) -> None:
        for name in zf.namelist():
            low = name.lower()
            if low.endswith(".txt"):
                out[name.split("/")[-1]] = zf.read(name)
            elif low.endswith(".zip"):
                walk(zipfile.ZipFile(io.BytesIO(zf.read(name))))

    walk(zipfile.ZipFile(zpath))
    return out


def _rows(text_bytes: bytes) -> list[tuple[str, str]]:
    """Parse a tab-separated Table 6 text file into (code, description) rows,
    skipping the title and column-header lines regardless of how many there are."""
    rows = []
    for line in text_bytes.decode("latin-1", "replace").splitlines():
        if not line.strip() or line.lstrip().upper().startswith("TABLE"):
            continue
        parts = line.split("\t")
        code = parts[0].strip()
        if not code or code.lower() in _HEADER_FIRST:
            continue
        rows.append((code, parts[1].strip() if len(parts) > 1 else ""))
    return rows


def _table(txts: dict, phrase: str) -> list[tuple[str, str]]:
    """Find a table file by its descriptive phrase (consistent across years)."""
    for name, data in txts.items():
        if phrase.lower() in name.lower():
            return _rows(data)
    return []


def parse_tables6_all() -> None:
    """Parse Tables 6A-6J for all configured years into icd10_updates.json,
    cc_mcc_changes.json (per-year additions/deletions), and cc_mcc_list.json
    (the latest year's complete MCC/CC lists, used by the status lookup)."""
    icd: dict = {}
    cc_mcc_changes: dict = {}
    latest_complete = None
    latest_fy = max(YEARS)
    for fy in YEARS:
        zpath = RAW / TABLES6.get(fy, "")
        if not zpath.exists():
            print(f"FY{fy} Tables 6 not downloaded; skipping.")
            continue
        t = _collect_txts(zpath)
        new_dx = _table(t, "New Diagnosis Codes")
        new_px = _table(t, "New Procedure Codes")
        inv_dx = _table(t, "Invalid Diagnosis Codes")
        inv_px = _table(t, "Invalid Procedure Codes")
        rev_dx = _table(t, "Revised Diagnosis Code Titles")
        rev_px = _table(t, "Revised Procedure Code Titles")
        mcc_all = _table(t, "Complete MCC List")
        mcc_add = _table(t, "Additions to the MCC List")
        mcc_del = _table(t, "Deletions to the MCC List")
        cc_all = _table(t, "Complete CC List")
        cc_add = _table(t, "Additions to the CC List")
        cc_del = _table(t, "Deletions to the CC List")

        icd[fy] = {
            "ms_drg_version": YEARS[fy][1],
            "cms_id": YEARS[fy][2],
            "new_diagnosis_codes": len(new_dx),
            "new_procedure_codes": len(new_px),
            "invalid_diagnosis_codes": len(inv_dx),
            "invalid_procedure_codes": len(inv_px),
            "revised_diagnosis_titles": len(rev_dx),
            "revised_procedure_titles": len(rev_px),
            "mcc_list_size": len(mcc_all),
            "cc_list_size": len(cc_all),
            "mcc_additions": len(mcc_add),
            "mcc_deletions": len(mcc_del),
            "cc_additions": len(cc_add),
            "cc_deletions": len(cc_del),
            "notable_new_diagnosis": [{"code": c, "description": d} for c, d in new_dx[:10]],
            "source": f"{YEARS[fy][2]} Tables 6A-6J (FY{fy} IPPS Final Rule)",
        }
        cc_mcc_changes[fy] = {
            "mcc_additions": [{"code": c, "description": d} for c, d in mcc_add],
            "mcc_deletions": [{"code": c, "description": d} for c, d in mcc_del],
            "cc_additions": [{"code": c, "description": d} for c, d in cc_add],
            "cc_deletions": [{"code": c, "description": d} for c, d in cc_del],
        }
        if fy == latest_fy:
            latest_complete = {
                "fy": fy,
                "mcc": {c: d for c, d in mcc_all},
                "cc": {c: d for c, d in cc_all},
                "mcc_additions": cc_mcc_changes[fy]["mcc_additions"],
                "cc_additions": cc_mcc_changes[fy]["cc_additions"],
                "cc_deletions": cc_mcc_changes[fy]["cc_deletions"],
            }
        print(
            f"FY{fy} ICD-10: {len(new_dx)} new dx, {len(new_px)} new px, "
            f"{len(inv_dx)} invalid dx; MCC {len(mcc_all)} (+{len(mcc_add)}/-{len(mcc_del)}), "
            f"CC {len(cc_all)} (+{len(cc_add)}/-{len(cc_del)})"
        )

    (OUT / "icd10_updates.json").write_text(
        json.dumps(icd, indent=1, ensure_ascii=False), encoding="utf-8"
    )
    (OUT / "cc_mcc_changes.json").write_text(
        json.dumps(cc_mcc_changes, ensure_ascii=False), encoding="utf-8"
    )
    if latest_complete:
        (OUT / "cc_mcc_list.json").write_text(
            json.dumps(latest_complete, ensure_ascii=False), encoding="utf-8"
        )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    catalog = {fy: parse_year(fy) for fy in YEARS}
    (OUT / "ms_drg_catalog.json").write_text(
        json.dumps(catalog, indent=1, ensure_ascii=False), encoding="utf-8"
    )
    changes = diff_changes(catalog)
    (OUT / "drg_changes.json").write_text(
        json.dumps(changes, indent=1, ensure_ascii=False), encoding="utf-8"
    )
    # Summary
    by = {}
    for c in changes:
        by.setdefault((c["fy"], c["change_type"]), 0)
        by[(c["fy"], c["change_type"])] += 1
    print("\nChange summary (added/deleted/retitled per FY):")
    for (fy, ct), n in sorted(by.items()):
        print(f"  FY{fy} {ct}: {n}")
    print(f"\nWrote {OUT/'ms_drg_catalog.json'} and {OUT/'drg_changes.json'}")
    print("\nICD-10 / CC-MCC (Tables 6):")
    parse_tables6_all()


if __name__ == "__main__":
    main()
