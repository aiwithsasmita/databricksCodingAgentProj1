---
name: medicare-mce
description: Medicare Code Editor (MCE) v43.1 claim edits vs MS-DRG grouping — when to use mce_code_check and how MCE differs from Appendix B/C.
tags:
  - healthcare
  - mce
  - medicare-code-edits
  - compliance
---

# Medicare Code Editor (MCE) v43.1

## What this is (vs MS-DRG)

- **MCE** (*Definitions of Medicare Code Edits*): claim-level **edits** — invalid/implausible combinations (e.g. age vs diagnosis, unacceptable principal diagnosis, manifestation as PDX, questionable admission).
- **MS-DRG** (*Definitions Manual* Appendix B/C): **grouping** — which DRG a stay maps to, CC/MCC severity.

Load this skill when the user asks about MCE, age/sex conflicts, “unacceptable principal,” “questionable admission,” or **whether Medicare would flag a code on the claim** before grouping.

## On-demand tool

- `mce_code_check(icd_code, is_principal, patient_age?, has_secondary_diagnosis?)` — uses embedded CMS v43.1 MCE code lists in `tools/mce_reference.json` (regenerate with `python tools/parse_mce.py <path-to-CMS-txt>`).

## Data accuracy

Lists are **parsed from the official CMS text file** the user provided (April 2026 v43.1). Always cite MCE v43.1 and offer chart review; never assert fraud.
