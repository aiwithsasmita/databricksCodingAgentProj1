---
name: drg-fundamentals
description: Core MS-DRG concepts, MDC categories, IPPS payment calculation, and CC/MCC severity system. Load this skill when the user asks about DRG basics, payment methodology, or how the grouper works.
tags:
  - healthcare
  - drg
  - fundamentals
  - payment
---

# MS-DRG Fundamentals

> DATA SOURCE: CMS FY 2026 IPPS Final Rule, Table 5 (CMS-1833-F).
> DRG weights and mean LOS values are exact FY 2026 Final Rule numbers.
> MDC assignments, ICD-10 codes, payment formula, and CC/MCC concepts
> are from official CMS documentation.

## What Is MS-DRG?

MS-DRG (Medicare Severity Diagnosis Related Groups) is the CMS patient
classification system that groups inpatient hospital discharges into
clinically coherent categories with similar resource consumption.
Current version: V43.1 (FY 2026, effective April 1, 2026).

## Key Terms

- **Relative Weight (RW)**: Cost multiplier assigned to each DRG.
  Higher weight = higher expected resource use and payment.
- **Geometric Mean LOS (GMLOS)**: Typical stay length for the DRG.
  Used as the threshold for short-stay and long-stay outliers.
- **Arithmetic Mean LOS (AMLOS)**: Average stay length including
  outliers. Always >= GMLOS.
- **MCC**: Major Complication or Comorbidity. A severe secondary
  diagnosis that bumps a case to the highest-paying DRG tier.
- **CC**: Complication or Comorbidity. A moderate secondary diagnosis
  that bumps to the middle DRG tier.
- **Principal Diagnosis**: The condition established after study to be
  chiefly responsible for the admission. This drives DRG assignment.
- **Grouper**: The CMS software that takes ICD-10-CM/PCS codes as
  input and outputs the assigned MS-DRG.

## Major Diagnostic Categories (MDC)

All 770 MS-DRGs in Table 5 are organized into 25 MDCs by body system.
The principal diagnosis determines the MDC.

| MDC | Description | Example DRGs in our data |
|-----|-------------|--------------------------|
| 01 | Diseases and Disorders of the Nervous System | 064-066 (Stroke) |
| 04 | Diseases and Disorders of the Respiratory System | 193-195 (Pneumonia), 190-192 (COPD) |
| 05 | Diseases and Disorders of the Circulatory System | 250-251 (percutaneous cardiovascular procedures), 291-293 (heart failure) |
| 06 | Diseases and Disorders of the Digestive System | 392 (GI Disorders) |
| 08 | Diseases and Disorders of the Musculoskeletal System | 469-470 (Hip/Knee Replacement) |
| 11 | Diseases and Disorders of the Kidney and Urinary Tract | 689-690 (UTI) |
| 18 | Infectious and Parasitic Diseases (Systemic) | 871-872 (Sepsis) |
| 19 | Mental Diseases and Disorders | 885 (Psychoses) |

Pre-MDC DRGs are assigned BEFORE MDC grouping and override normal
logic: transplants (001-013), ECMO (003), tracheostomy (003-004).

## IPPS Payment Calculation

CMS Medicare payment formula for inpatient stays:

```
Payment = Base Rate * DRG Relative Weight * Wage Index Adjustment
```

| Component | FY 2026 Value | Source |
|-----------|---------------|--------|
| National Base Rate (operating + capital) | ~$6,300 | CMS IPPS Final Rule |
| DRG Relative Weight | Varies by DRG (Table 5) | CMS Table 5 |
| Wage Index | Varies by MSA (labor market) | CMS Wage Index files |

Worked examples (at wage index = 1.0):
- DRG 470 (Joint Replacement): $6,300 * 1.9289 = ~$12,152
- DRG 291 (Heart Failure MCC): $6,300 * 1.2838 = ~$8,088
- DRG 293 (Heart Failure base): $6,300 * 0.5660 = ~$3,566
- **Shift impact**: DRG 291 vs 293 = ~$4,522 more per case

Additional payment adjustments:
- **Outlier**: Extra payment when charges exceed fixed-loss threshold
- **DSH**: Disproportionate Share for hospitals serving low-income patients
- **IME**: Indirect Medical Education for teaching hospitals
- **HAC Penalty**: 1% payment reduction for high hospital-acquired conditions
- **HRRP Penalty**: Up to 3% reduction for excess readmissions

## CC/MCC Severity System

### Three Tiers
Secondary diagnoses are classified into severity levels:
- **MCC**: Bumps to highest-paying DRG in the family
- **CC**: Bumps to middle-paying DRG
- **Non-CC**: No severity impact, stays at base DRG

### CC/MCC Exclusion Lists (Critical for Auditing)
Not all CCs/MCCs count for every DRG. CMS maintains exclusion lists
where certain diagnoses are excluded because they are:
- Inherent to the principal diagnosis (e.g., respiratory failure as
  CC when principal dx is pneumonia -- it's expected, not a complication)
- Too closely related to be a true independent complication

When auditing a claim coded as DRG 291 (HF with MCC), verify that at
least one secondary diagnosis on the claim:
1. IS on the CMS MCC list
2. Is NOT on the exclusion list for that DRG

### Common MCC Codes (Real CMS designations)

| ICD-10 | Description | Commonly used with |
|--------|-------------|-------------------|
| N17.9 | Acute kidney failure, unspecified | Sepsis, Heart Failure |
| J96.01 | Acute respiratory failure with hypoxia | Pneumonia, Sepsis |
| R65.20 | Severe sepsis without septic shock | Sepsis (required for 871) |
| R65.21 | Severe sepsis with septic shock | Sepsis (required for 871) |
| G93.41 | Metabolic encephalopathy | Sepsis, Stroke |
| E87.1 | Hypo-osmolality and hyponatremia | Heart Failure |
| D69.6 | Thrombocytopenia, unspecified | Sepsis |
| I48.91 | Unspecified atrial fibrillation | Heart Failure, Stroke |
