---
name: audit-guidelines
description: DRG coding audit workflow, red flags for upcoding and coding errors, report templates, and readmission penalty rules. Load this skill when the user asks you to audit claims, check coding accuracy, or write a compliance report.
tags:
  - healthcare
  - audit
  - compliance
  - coding
  - upcoding
---

# DRG Audit & Compliance Guidelines

## Audit Workflow

When asked to audit claims, follow this process:

1. **Plan** the audit scope using `write_todos`:
   - Which DRGs? Which providers? What date range?
2. **Query claims data** via the Claims Data Analyst sub-agent (Genie).
3. **For each claim**, validate the principal diagnosis against the
   assigned DRG using the `icd_code_validate` tool.
4. **Check LOS outliers** by comparing actual LOS to GMLOS/AMLOS
   from the `drg_lookup` tool.
5. **Check CC/MCC validity** -- does the claim have a qualifying MCC
   on the secondary diagnoses list for MCC-level DRGs?
6. **Compile findings** into a structured report via `write_file`.

## Red Flags to Check

### 1. Diagnosis-DRG Mismatch (CRITICAL)
The principal ICD-10 code doesn't correspond to the assigned DRG.
- Example: DRG 470 (joint replacement) + principal dx J18.9 (pneumonia)
- Action: Use `icd_code_validate` to confirm mismatch
- Impact: Entire DRG payment may need to be refunded/adjusted

### 2. DRG Upcoding (CRITICAL)
MCC-level DRG assigned without qualifying MCC documentation:
- DRG 291 (HF with MCC) but no MCC on secondary diagnoses
- Same provider always codes MCC regardless of patient complexity
- CC/MCC codes that are on the exclusion list for that DRG
- Action: Use `drg_shift_analysis` to compare provider MCC rates

### 3. Length of Stay Outliers (WARNING)
- **Short stay**: LOS < 0.5 * GMLOS --> possible wrong DRG or
  premature discharge
- **Long stay**: LOS > 2.0 * AMLOS --> possible complications,
  wrong DRG, or discharge delays
- Action: Use `drg_lookup` to get GMLOS/AMLOS, compare to actual LOS

### 4. Readmission Patterns (WARNING)
- Same-DRG readmission within 30 days --> quality concern
- Different-DRG readmission --> original DRG may have been wrong
- CMS penalizes excess readmissions under HRRP (see below)

### 5. Charge-to-Payment Ratio Anomalies (ADVISORY)
Expected CPR ranges by payer:

| Payer Type | Normal CPR Range | Flag if |
|------------|-----------------|---------|
| Medicare | 3.0 - 4.0 | < 2.0 or > 5.0 |
| Medicaid | 4.0 - 6.0 | < 3.0 or > 8.0 |
| Commercial (BCBS, Aetna, UHC, Cigna) | 1.5 - 2.5 | < 1.0 or > 4.0 |

CPR < 1.0 means the hospital is losing money on the case.

## Hospital Readmissions Reduction Program (HRRP)

CMS penalizes hospitals with excess readmissions for these conditions:

| Condition | DRGs | Penalty |
|-----------|------|---------|
| Acute Myocardial Infarction (AMI) | 280-282 | Up to 3% of total Medicare payments |
| Heart Failure (HF) | 291-293 | Up to 3% |
| Pneumonia (PN) | 193-195 | Up to 3% |
| COPD | 190-192 | Up to 3% |
| Hip/Knee Replacement (THA/TKA) | 469-470 | Up to 3% |
| Coronary Artery Bypass Graft (CABG) | 231-236 | Up to 3% |

The penalty applies to ALL Medicare payments, not just the readmitted
DRGs. A 3% penalty on a hospital with $100M in Medicare revenue = $3M.

## Report Templates

### Compliance Audit Report

```
# DRG Coding Compliance Audit

## Scope
- Claims reviewed: N
- Date range: [start] to [end]
- DRG codes: [list]
- Provider(s): [list]

## Executive Summary
[2-3 sentence overview of findings]

## Findings

### CRITICAL: Coding Errors
| Claim ID | Assigned DRG | Principal Dx | Issue | Suggested DRG |
|----------|-------------|--------------|-------|---------------|
[rows]

### WARNING: LOS Outliers
| Claim ID | DRG | Actual LOS | Expected GMLOS | Variance |
|----------|-----|-----------|----------------|----------|
[rows]

### ADVISORY: Pattern Observations
[upcoding trends, readmission clusters, payer anomalies]

## Financial Impact
- Estimated overpayment from coding errors: $X
- Estimated underpayment from undercoding: $Y
- Net adjustment: $Z

## Recommendations
1. [specific action items]
2. [chart review targets]
3. [CDI program suggestions]
```

### Cost Analysis Report

```
# DRG Cost Analysis: [DRG Code] - [Description]

## Summary
- Total claims analyzed: N
- Date range: [start] to [end]
- Average charges: $X
- Average payments: $Y
- Average LOS: Z days
- Readmission rate: P%

## By Provider
| Provider | Claims | Avg Charges | Avg Payment | Avg LOS | Readmit% |
|----------|--------|-------------|-------------|---------|----------|
[rows]

## By Payer
| Payer | Claims | Avg Payment | CPR |
|-------|--------|-------------|-----|
[rows]

## Quarterly Trend
| Quarter | Claims | Avg LOS | Avg Payment |
|---------|--------|---------|-------------|
[rows]

## Outliers
[flagged cases with reasoning]
```

## Known Test Data Anomalies

The sample dataset includes these intentional errors for testing:

| Claim | Assigned DRG | Principal Dx | Expected Finding |
|-------|-------------|--------------|-----------------|
| CLM043 | 470 (Joint Replacement) | J18.9 (Pneumonia) | CRITICAL mismatch |
| CLM044 | 291 (Heart Failure) | M17.11 (Knee OA) | CRITICAL mismatch |
| CLM045 | 690 (UTI) | I50.23 (Heart Failure) | CRITICAL mismatch |

Any audit should detect all three. If it doesn't, the audit logic has gaps.
