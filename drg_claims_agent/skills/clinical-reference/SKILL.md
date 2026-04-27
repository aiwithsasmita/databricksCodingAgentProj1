---
name: clinical-reference
description: Reference data for discharge status codes, payer analysis patterns, and the claims table schema. Load this skill when the user asks about discharge dispositions, payer mix, charge-to-payment ratios, or what columns are available in the data.
tags:
  - healthcare
  - reference
  - payer
  - discharge
  - schema
---

# Clinical & Data Reference

## Claims Table Schema

The `healthcare.claims.drg_claims` table:

| Column | Type | Description |
|--------|------|-------------|
| claim_id | STRING | Unique ID (CLM001-CLM087) |
| patient_id | STRING | Patient ID (PAT101-PAT187) |
| admission_date | DATE | Admission date |
| discharge_date | DATE | Discharge date |
| drg_code | STRING | Assigned MS-DRG (e.g., 470, 871) |
| drg_description | STRING | DRG full name |
| principal_diagnosis | STRING | ICD-10-CM code driving the DRG |
| secondary_diagnoses | ARRAY | CC/MCC and other secondary ICD codes |
| procedures | ARRAY | ICD-10-PCS procedure codes |
| provider_id | STRING | Hospital ID (PRV01-PRV04) |
| provider_name | STRING | Hospital name |
| payer | STRING | Insurance payer |
| total_charges | DECIMAL | Hospital billed amount (list price) |
| total_payments | DECIMAL | Amount actually paid by payer |
| length_of_stay | INT | Days admitted |
| discharge_status | STRING | Disposition (see below) |
| readmission_flag | BOOLEAN | True if readmitted within 30 days |
| created_at | TIMESTAMP | Record timestamp |

### Providers in the data
| ID | Name | Type |
|----|------|------|
| PRV01 | City General Hospital | Community hospital |
| PRV02 | Regional Medical Center | Regional referral center |
| PRV03 | University Hospital | Academic teaching hospital |
| PRV04 | Behavioral Health Center | Psychiatric facility |

### Payers in the data
Medicare, Medicaid, BlueCross, Aetna, UnitedHealth, Cigna

### Date range
Q1 2025 (Jan-Mar) through Q2 2025 (Apr-Jun)

## Discharge Status Codes

| Status | Full Name | Clinical Meaning |
|--------|-----------|-----------------|
| Home | Home or Self Care | Normal discharge, patient can manage independently |
| SNF | Skilled Nursing Facility | Needs ongoing skilled nursing (wound care, IV meds) |
| Rehab | Inpatient Rehab Facility | Needs intensive PT/OT (stroke, joint replacement) |
| LTAC | Long-Term Acute Care | Extended complex medical needs (ventilator, wound vac) |
| Group Home | Supervised Residential | Behavioral health, cognitive impairment |
| Expired | Died During Stay | Mortality -- triggers quality review |

### Why discharge status matters for analysis:
- DRG payment does NOT change based on discharge disposition
  (except a few neonatal DRGs)
- But SNF/Rehab/LTAC discharges correlate with:
  - Higher readmission risk
  - Higher case complexity
  - Higher total episode cost (acute + post-acute)
- Expired cases warrant mortality rate analysis by DRG and provider

## Payer Analysis Patterns

### Reimbursement by Payer Type

| Payer | Payment Model | Typical Charge-to-Payment Ratio |
|-------|--------------|-------------------------------|
| Medicare | DRG-based (IPPS federal rate) | 3:1 to 4:1 |
| Medicaid | DRG-based (state-set rates, below Medicare) | 4:1 to 6:1 |
| BlueCross | Negotiated (% of charges or DRG multiplier) | 1.5:1 to 2.5:1 |
| Aetna | Negotiated | 1.5:1 to 2.5:1 |
| UnitedHealth | Negotiated | 1.5:1 to 2.5:1 |
| Cigna | Negotiated | 1.5:1 to 2.5:1 |

### Useful Payer Queries (via Genie)

- Revenue concentration:
  `SELECT payer, COUNT(*) as claims, SUM(total_payments) as revenue
   FROM drg_claims GROUP BY payer ORDER BY revenue DESC`

- CPR by payer:
  `SELECT payer, ROUND(AVG(total_charges / total_payments), 2) as avg_cpr
   FROM drg_claims WHERE total_payments > 0 GROUP BY payer`

- DRG mix by payer (are commercial payers getting higher-weight DRGs?):
  `SELECT payer, drg_code, COUNT(*) FROM drg_claims
   GROUP BY payer, drg_code ORDER BY payer, COUNT(*) DESC`

### CPR Flag Thresholds

| Condition | Meaning |
|-----------|---------|
| CPR < 1.0 | Hospital losing money (payment > charges is rare) |
| CPR > 5.0 for Medicare | Unusually high charges relative to DRG payment |
| CPR > 3.0 for Commercial | May indicate aggressive charge structure |
| CPR varies >50% across payers for same DRG | Worth investigating contract terms |
