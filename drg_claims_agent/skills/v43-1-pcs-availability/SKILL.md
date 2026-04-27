---
name: v43-1-pcs-availability
description: CMS April 2026 announcement of 80 new ICD-10-PCS codes in MS-DRG V43.1 — effective dates, footnotes, and v43_1_pcs_check tool usage.
tags:
  - healthcare
  - icd-10-pcs
  - ms-drg
  - fy2026
---

# MS-DRG / ICD-10-PCS V43.1 — 80 new procedure codes (April 2026)

## Summary

- **Effective:** discharges on or after **2026-04-01** (CMS web announcement).
- **Grouper:** ICD-10 **MS-DRG V43.1** includes these new ICD-10-PCS codes in assignment logic.
- **MCE:** **Medicare Code Editor V43.1** applies to ICD-10 codes on claims for the same discharge date rule.
- **Count:** **80** new **ICD-10-PCS** procedure codes (not new ICD-10-CM diagnosis codes in this document).

## Agent tool

- `v43_1_pcs_check(pcs_code)` — looks up a 7-character PCS in the published list (`tools/v43_1_new_pcs_codes.json`).

## Footnotes in the announcement table

- **\*** — Non-O.R. procedure; **no MDC/MS-DRG shown in the table**; final DRG depends on principal diagnosis, CC/MCC, other procedures, demographics (CMS text).
- **\*\*** — **Non-O.R.** but may **still affect** MS-DRG assignment (CMS text).

## Regenerate data

- Source text: `reference/v43_1_pcs_announcement.txt`
- Parser: `python tools/parse_v43_1_announcement.py` → rewrites `tools/v43_1_new_pcs_codes.json`

## URLs (from announcement)

- MS-DRG software & definitions: see `v43_1_new_pcs_codes.json` → `resource_urls`
- ICD code files / addenda: `https://www.cms.gov/medicare/coding-billing/icd-10-codes`
