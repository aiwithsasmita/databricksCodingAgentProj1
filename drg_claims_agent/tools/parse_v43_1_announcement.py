"""
Parse reference/v43_1_pcs_announcement.txt -> v43_1_new_pcs_codes.json

Run from repo root:  python drg_claims_agent/tools/parse_v43_1_announcement.py
or:                  python tools/parse_v43_1_announcement.py  (from drg_claims_agent/)
"""

from __future__ import annotations

import json
import os
import re

_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.normpath(os.path.join(_DIR, ".."))
_SRC = os.path.join(_ROOT, "reference", "v43_1_pcs_announcement.txt")
_OUT = os.path.join(_DIR, "v43_1_new_pcs_codes.json")

# Procedure begins with 7-char PCS, optional * or **, then description
RE_PCS = re.compile(r"^([0-9A-HJ-NP-Z]{7})(\*{0,2})\s*(.*)$")


def _is_pcs_code_line(line: str) -> re.Match | None:
    m = RE_PCS.match(line.strip())
    if not m:
        return None
    code = m.group(1)
    if not any(ch.isdigit() for ch in code):
        return None
    return m


def _is_or_following_line(s: str) -> bool:
    t = s.strip()
    if not t:
        return False
    if t in ("N", "Y"):
        return True
    if re.match(r"^N\s+Pre", t) or t.startswith("N Pre") or t == "N PreMDC":
        return True
    if t == "018":
        return True
    if re.match(r"^([YN])\s+\d", t) and "approach" not in t.lower() and "Drainage" not in t:
        return True
    if re.match(r"^N\s+23\s+945-946$", t):
        return True
    if re.match(r"^Y\s+\d{2}\s+\d{3}-\d{3}$", t):  # N 23 945-946 style for F codes
        return True
    # MDC/DRG columns only
    if re.match(r"^\d{1,2}$", t):
        return True
    if re.match(r"^\d{3}-\d{3}$", t):
        return True
    if re.match(r"^(\d{3}-\d{3},)*\d{3}-\d{3}$", t):
        return True
    return False


def parse() -> dict:
    with open(_SRC, "r", encoding="utf-8") as f:
        raw_lines = [ln.rstrip() for ln in f.readlines()]

    # Skip header until table body
    lines = raw_lines
    for idx, line in enumerate(raw_lines):
        if line.strip().startswith("02HM3"):
            lines = raw_lines[idx:]
            break

    # Split into blocks starting at each PCS line
    starts: list[int] = []
    for i, line in enumerate(lines):
        if i > 0 and line.startswith("*As the procedure"):
            break
        m = _is_pcs_code_line(line)
        if m and not line.lstrip().startswith("*As "):
            starts.append(i)

    procedures: list[dict] = []
    for j, st in enumerate(starts):
        end = starts[j + 1] if j + 1 < len(starts) else len(lines)
        block = lines[st:end]
        first = block[0]
        m0 = _is_pcs_code_line(first)
        assert m0
        code, stars, rest = m0.group(1), m0.group(2), m0.group(3).strip()
        # Description lines: first line may include " Y 06" style OR at end
        desc_lines = [rest] if rest else []
        for line in block[1:]:
            if _is_or_following_line(line):
                break
            desc_lines.append(line)
        desc = " ".join(x.strip() for x in desc_lines if x.strip())
        # Strip inline " Y 11" at end of same line as description start
        m_or = re.search(r"\s+([YN])\s+(\d{1,2}|11|12|14|16|18|20|22|25)\s*$", desc)
        or_flag = None
        if m_or:
            or_flag = m_or.group(1)
            desc = desc[: m_or.start()].rstrip()
        m_f = re.search(r"\s+([YN])\s+23\s+945-946\s*$", desc)
        if m_f:
            or_flag = m_f.group(1)
            desc = desc[: m_f.start()].rstrip()
        m_premdc = re.search(r"\s+([YN])\s+Pre-?MDC\s+018\s*$", desc, re.I)
        if m_premdc:
            or_flag = m_premdc.group(1)
            desc = desc[: m_premdc.start()].rstrip()
        if code == "0VT08ZE" and "18 19 23" in desc:
            desc = "Resection of prostate, via natural or artificial opening endoscopic, capsule intact"
            or_flag = "Y"
        foot = None
        if stars == "**":
            foot = "**"
        elif stars == "*":
            foot = "*"
        rec: dict = {
            "pcs": code,
            "description": re.sub(r"\s+", " ", desc).strip(),
        }
        if foot:
            rec["cms_table_footnote"] = foot
        if or_flag:
            rec["or_procedure"] = or_flag
        if foot == "*" and or_flag is None:
            rec["or_procedure"] = "N"
        if foot == "**" and "945-946" in first + "".join(block[:5]):
            rec["or_procedure"] = "N"
        procedures.append(rec)

    return {
        "source": "CMS web announcement: ICD-10 MS-DRGs V43.1 new ICD-10-PCS codes (April 2026)",
        "effective_date": "2026-04-01",
        "grouper_version": "ICD-10 MS-DRG V43.1",
        "mce_version_note": "MCE V43.1: edits validate ICD-10 codes on claims for discharges on or after 2026-04-01",
        "footnote_legend": {
            "*": (
                "Non-O.R. procedure: no assigned MDC/MS-DRG in the announcement table; "
                "grouper assignment depends on principal diagnosis, CC/MCC, procedures, age, sex, "
                "discharge status (CMS text)."
            ),
            "**": "Non-O.R. procedure that may still affect MS-DRG assignment (CMS text).",
        },
        "resource_urls": {
            "ms_drg_software": (
                "https://www.cms.gov/Medicare/Medicare-Fee-for-Service-Payment/"
                "AcuteInpatientPPS/MS-DRG-Classifications-and-Software.html"
            ),
            "icd_10_code_files": "https://www.cms.gov/medicare/coding-billing/icd-10-codes",
        },
        "count": len(procedures),
        "procedures": procedures,
    }


def main() -> None:
    data = parse()
    with open(_OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("Wrote", _OUT, "count =", data["count"], "(expected 80)")


if __name__ == "__main__":
    main()
