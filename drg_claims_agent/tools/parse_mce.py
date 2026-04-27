"""
One-time (or re-run) parser: CMS "Definitions of Medicare Code Edits" text file
-> mce_reference.json

Usage:
  python tools/parse_mce.py [path-to-Definitions-of-Medicare-Code-Edits.txt]

Default input path (Windows) can be overridden; output is always tools/mce_reference.json
"""

from __future__ import annotations

import json
import os
import re
import sys

# Output next to this script
_OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mce_reference.json")

# Typical Windows download path from user; override via argv[1]
_DEFAULT_INPUT = r"C:\Users\SSD\Downloads\definitions-of-medicare-code-edits_v_43_1 (2)\Definitions of Medicare Code Edits_v_43_1.txt"

def _split_code_desc(line: str) -> tuple[str, str] | None:
    line = line.rstrip()
    if "\t" in line:
        left, right = line.split("\t", 1)
        code, desc = left.strip(), right.strip()
        if re.match(r"^[A-Z][0-9A-Z.]*$", code) and desc:
            return code.upper().replace(".", ""), desc
    m = re.match(r"^([A-Z][0-9A-Z.]{2,7})\s{2,}(.+)$", line)
    if m:
        return m.group(1).upper().replace(".", ""), m.group(2).strip()
    m = re.match(r"^([A-Z][0-9A-Z.]{2,7})\s+(.+)$", line)
    if m:
        return m.group(1).upper().replace(".", ""), m.group(2).strip()
    return None


def parse_mce(path: str, encoding: str = "cp1252") -> dict:
    with open(path, "r", encoding=encoding, errors="replace") as f:
        lines = f.readlines()

    sections = {
        "perinatal": {},
        "pediatric": {},
        "maternity": {},
        "adult": {},
        "manifestation_not_pdx": {},
        "questionable_admission_pdx": {},
        "unacceptable_pdx": {},
    }
    # Z51.89 exception from narrative (asterisk)
    special: dict = {
        "Z5189": {
            "note": "Acceptable as principal only when a secondary diagnosis is also coded; otherwise MCE may flag REQUIRES SECONDARY DX per CMS v43.1 MCE doc.",
        }
    }

    state: str | None = None
    in_unacceptable = False
    in_questionable = False

    for i, raw in enumerate(lines):
        line = raw.rstrip("\n\r")

        if line.startswith("A. Perinatal") or line.startswith("A.\tPerinatal"):
            state = "perinatal"
            continue
        if line.startswith("B. Pediatric"):
            state = "pediatric"
            continue
        if line.startswith("C. Maternity"):
            state = "maternity"
            continue
        if line.startswith("D. Adult"):
            state = "adult"
            continue
        if line.strip() == "5. Sex conflict (deactivated as of 10/01/2024)":
            state = None
            continue
        if line.strip() == "Manifestation codes not allowed as principal diagnosis":
            state = "manifestation"
            continue
        if state == "manifestation" and line.startswith("7. Non-specific principal diagnosis"):
            state = None
            continue
        if line.strip() == "Questionable admission codes":
            in_questionable = True
            continue
        if in_questionable and (
            line.startswith("Questionable obstetric")
            or line.strip().startswith("B. The following ICD-10-PCS")
        ):
            in_questionable = False
            state = None
            continue
        if line.strip() == "9. Unacceptable principal diagnosis" or line.strip().startswith(
            "9. Unacceptable principal diagnosis\t"
        ):
            # narrative until list
            in_unacceptable = True
            state = None
            continue
        if line.strip() == "Unacceptable principal diagnosis codes":
            state = "unacceptable"
            in_unacceptable = True
            continue
        if state == "unacceptable" and line.strip().startswith("10. Non-specific O.R."):
            state = None
            in_unacceptable = False
            continue

        key = state
        if in_questionable:
            key = "questionable"
        if key is None:
            continue
        if key in ("perinatal", "pediatric", "maternity", "adult"):
            row = _split_code_desc(line)
            if not row:
                continue
            code, desc = row
            sections[key][code] = desc
        elif key == "manifestation":
            row = _split_code_desc(line)
            if not row:
                continue
            code, desc = row
            sections["manifestation_not_pdx"][code] = desc
        elif key == "questionable":
            row = _split_code_desc(line)
            if not row:
                continue
            code, desc = row
            sections["questionable_admission_pdx"][code] = desc
        elif key == "unacceptable" or in_unacceptable and state == "unacceptable":
            row = _split_code_desc(line)
            if not row:
                continue
            code, desc = row
            # Skip procedure-like codes (ICD-10-PCS starts with 0-9) if any slipped in
            if code[0].isdigit():
                continue
            sections["unacceptable_pdx"][code] = desc

    return {
        "source": "CMS Definitions of Medicare Code Edits (MCE) ICD-10 v43.1 April 2026",
        "mce_version": "43.1",
        "age_ranges": {
            "perinatal": "age 0 years only (newborn/perinatal)",
            "pediatric": "age 0 through 17 (inclusive)",
            "maternity": "age 9 through 64 (inclusive)",
            "adult": "age 15 through 124 (inclusive)",
        },
        "age_conflict_lists": {
            "perinatal": sections["perinatal"],
            "pediatric": sections["pediatric"],
            "maternity": sections["maternity"],
            "adult": sections["adult"],
        },
        "manifestation_not_pdx": sections["manifestation_not_pdx"],
        "questionable_admission_pdx": sections["questionable_admission_pdx"],
        "unacceptable_pdx": sections["unacceptable_pdx"],
        "principal_dx_special_rules": special,
    }


def main() -> None:
    src = sys.argv[1] if len(sys.argv) > 1 else _DEFAULT_INPUT
    if not os.path.isfile(src):
        print(f"Input not found: {src}", file=sys.stderr)
        print("Pass path as first argument.", file=sys.stderr)
        sys.exit(1)
    data = parse_mce(src)
    with open(_OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=0)
    print("Wrote", _OUT)
    for k, v in data["age_conflict_lists"].items():
        print(f"  age_conflict {k}: {len(v)} codes")
    print(f"  manifestation_not_pdx: {len(data['manifestation_not_pdx'])}")
    print(f"  questionable_admission: {len(data['questionable_admission_pdx'])}")
    print(f"  unacceptable_pdx: {len(data['unacceptable_pdx'])}")


if __name__ == "__main__":
    main()
