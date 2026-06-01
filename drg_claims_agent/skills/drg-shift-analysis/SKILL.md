---
name: drg-shift-analysis
description: DRG shift detection methodology -- how to compare provider coding patterns, calculate MCC capture rates, and identify potential upcoding or undercoding. Load this skill when the user asks about DRG variation, coding differences between hospitals, or MCC capture rate analysis.
tags:
  - healthcare
  - drg-shift
  - upcoding
  - provider-comparison
  - mcc-rate
---

# DRG Shift Analysis

## What Is DRG Shift?

DRG shift occurs when different hospitals assign different severity-
level DRGs (base / CC / MCC) for patients with the same principal
diagnosis. This happens due to differences in:
- Clinical documentation quality
- CDI (Clinical Documentation Improvement) program effectiveness
- Coding practices and coder interpretation
- Potentially: intentional upcoding

## DRG Families (Severity Tiers)

Each clinical condition has a family of DRGs at different severity.
Use `drg_family_lookup` to see tiers for any DRG code.

> Source: CMS FY 2026 IPPS Final Rule, Table 5 (CMS-1833-F).
> All weights are exact FY 2026 Final Rule values.

| Family | Base (no CC/MCC) | CC | MCC | Weight Spread |
|--------|-----------------|-----|------|---------------|
| Heart Failure | 293 (0.5660) | 292 (0.8490) | 291 (1.2838) | 127% |
| Pneumonia | 195 (0.6285) | 194 (0.8059) | 193 (1.3144) | 109% |
| Sepsis | -- | 872 (1.0233) | 871 (1.9425) | 90% |
| Stroke | 066 (0.6844) | 065 (1.0103) | 064 (2.0110) | 194% |
| Hip/Knee | 470 (1.9289) | -- | 469 (3.0332) | 57% |
| UTI | 690 (0.8095) | -- | 689 (1.1603) | 43% |

**Weight Spread** = (MCC weight - Base weight) / Base weight * 100.
Higher spread = bigger financial incentive to code at MCC level.

## Detection Workflow

Use `drg_shift_analysis` tool for automated analysis, or manually:

1. **Pick a DRG family** (e.g., `heart_failure`)
2. **Query claims** via Genie:
   `SELECT provider_name, drg_code, COUNT(*) as cnt
    FROM drg_claims
    WHERE drg_code IN ('291','292','293')
    GROUP BY provider_name, drg_code
    ORDER BY provider_name, drg_code`
3. **Calculate MCC capture rate** per provider:
   MCC Rate = count(MCC DRG) / total family claims * 100
4. **Calculate peer average** MCC rate across all providers
5. **Flag outliers**:
   - MCC rate >= 1.8x peer average --> HIGH risk
   - MCC rate <= 0.5x peer average --> MODERATE risk (undercoding)
6. **Estimate financial impact per case**:
   Impact = (MCC weight - base weight) * base rate (~$6,300)
   Total = per-case impact * excess MCC cases vs peer average

## Interpretation: Upcoding vs Documentation

A high MCC capture rate does NOT automatically mean fraud.

### Legitimate reasons for high MCC rate:
- **Teaching hospital** (sicker patients, higher case mix index)
- **Strong CDI program** (queries physicians to document severity)
- **Better EHR templates** that prompt detailed documentation
- **Patient population** (elderly, more comorbidities)

### Red flags that suggest upcoding:
- Same physician, same principal dx, ALWAYS gets MCC -- regardless
  of patient age or comorbidity count
- MCC capture rate jumped suddenly (e.g., 30% to 70% in one quarter)
  without a CDI program launch or new physician
- Secondary diagnoses appear in identical "copy-paste" patterns
  across multiple claims
- MCC codes don't match the clinical narrative or treatment plan
- Provider's MCC rate is >2x national benchmark for that DRG family

### Recommended follow-up actions:
- **HIGH flag**: Request chart-level review for 10-20 cases
- **MODERATE flag (undercoding)**: Assess CDI program, coder education
- Compare against national benchmarks (MedPAR data) if available

## DRG Shift Data in Sample Dataset

Claims CLM060-087 were designed with intentional shift patterns:
- **City General Hospital (PRV01)**: High MCC capture rate
  (~75% for heart failure, ~80% for pneumonia, 100% for sepsis)
- **Regional Medical Center (PRV02)**: Conservative coding
  (~29% MCC for heart failure, ~40% for pneumonia, ~75% for sepsis)
- **University Hospital (PRV03)**: Balanced/moderate coding

## Shift Analysis Report Template

```
# DRG Shift Analysis: [Family Name]

## Overview
- DRG Family: [e.g., Heart Failure (291/292/293)]
- Weight Spread: [e.g., ~93% between base and MCC]
- Total Claims Analyzed: N
- Providers Compared: P
- Analysis is for coding/billing review, not clinical decision-making.

## Provider Comparison
| Provider | Claims | MCC | CC | Base | MCC Rate | vs Peer | Flag |
|----------|--------|-----|-----|------|----------|---------|------|
[data rows]

## Flags
[list of flagged providers with severity, finding, and reasoning]

## Financial Impact
- Per-case MCC vs Base payment difference: ~$X
- Estimated excess MCC cases for flagged provider: N
- Total estimated revenue impact: $Y

## Recommendations
- HIGH flag: Chart review of CC/MCC documentation for [N] cases
- MODERATE flag (undercoding): CDI program assessment at [provider]
- Consider national benchmark comparison for context
```
