# UnitedHealthcare Policy Fraud Tactics & Denial Rules

**Source Policy:** Same Day/Same Service Policy (Policy Number 2025R0002A)  
**Payer:** UnitedHealthcare Commercial and Individual Exchange  
**Form:** CMS 1500  
**Extracted:** January 2026

---

## FRAUD TACTICS CATALOG (Derived from Same Day/Same Service Policy 2025R0002A)

### Category 1: E/M Unbundling Tactics

| Tactic ID | Tactic Name | Policy Reference | Description | Detection Logic | CPT Codes Involved |
|-----------|-------------|------------------|-------------|-----------------|-------------------|
| `SDSS-FT001` | E/M Code Unbundling | NCCI Policy Manual | Billing multiple E/M codes when a single comprehensive code describes all services | Count E/M codes per patient per day > 1 by same provider | 99201-99215, 99221-99223, 99231-99239 |
| `SDSS-FT002` | Initial + Subsequent Per Diem Stacking | CCI Definitive Edit | Billing initial per diem E/M with subsequent per diem E/M on same date | Initial E/M (99221-99223) + Subsequent E/M (99231-99233) same DOS | 99221, 99222, 99223, 99231, 99232, 99233 |
| `SDSS-FT003` | Hospital Visit + Discharge Same Day | Q&A #2 | Billing both hospital visit and discharge day management on final day | Hospital visit code + 99238/99239 same DOS | 99231-99233, 99238, 99239 |
| `SDSS-FT004` | Observation Admit/Discharge Split | Q&A #3 | Billing separate admit and discharge for same-day observation instead of combined code | Admit + Discharge codes instead of 99234-99236 | 99234, 99235, 99236 |

---

### Category 2: Provider Identity Manipulation Tactics

| Tactic ID | Tactic Name | Policy Reference | Description | Detection Logic | Conditions |
|-----------|-------------|------------------|-------------|-----------------|------------|
| `SDSS-FT005` | Same Specialty Group Double Billing | Medicare Claims Processing Manual | Two physicians in same group/specialty billing separately for same patient same day | Same TIN + Same Specialty + Same DOS + Same Patient | SAME_GROUP, SAME_SPECIALTY, SAME_DAY |
| `SDSS-FT006` | Covering Physician Double Billing | Q&A #5 | Covering physician (B) billing separately when primary physician (A) already billed for same day | Different NPI + Same TIN + Same Specialty + Same DOS (per diem) | SAME_GROUP, SAME_SPECIALTY, PER_DIEM |
| `SDSS-FT007` | Subspecialty Splitting | Q&A #8 | Attempting separate billing by claiming different subspecialties within same specialty | Same Specialty Code + Different Subspecialty + Same Group + Same DOS | SAME_SPECIALTY (subspecialty NOT considered) |
| `SDSS-FT008` | Physician + QHP Same Specialty Duplicate | Q&A #9 | Physician and Qualified Healthcare Professional (same specialty/group) both billing per diem E/M | Same Taxonomy Code Family + Same TIN + Same DOS + Per Diem codes | SAME_GROUP, SAME_TAXONOMY, PER_DIEM |
| `SDSS-FT009` | Same Individual Multiple Per Diem | Q&A #10 | Same provider (same NPI) billing multiple per diem E/M services on single DOS | Same NPI + Multiple Per Diem codes + Same DOS | SAME_PROVIDER, PER_DIEM, SAME_DAY |

---

### Category 3: Site of Service Manipulation Tactics

| Tactic ID | Tactic Name | Policy Reference | Description | Detection Logic | CPT Codes Involved |
|-----------|-------------|------------------|-------------|-----------------|-------------------|
| `SDSS-FT010` | ER + Initial Hospital Same Day | Q&A #6 | Billing ER visit separately when patient admitted to hospital same day | ER E/M (99281-99285) + Initial Hospital (99221-99223) same DOS, same provider | 99281-99285, 99221-99223 |
| `SDSS-FT011` | Office Visit + Hospital Admission Same Day | Policy Overview | Billing office visit when patient admitted to hospital from office same day | Office E/M (99201-99215) + Initial Hospital (99221-99223) same DOS | 99201-99215, 99221-99223 |
| `SDSS-FT012` | Nursing Facility + Hospital Same Day | Q&A #6 (implied) | Billing nursing facility visit when patient transferred/admitted to hospital same day | SNF E/M + Initial Hospital E/M same DOS | 99304-99310, 99221-99223 |

---

### Category 4: Modifier Abuse Tactics

| Tactic ID | Tactic Name | Policy Reference | Description | Detection Logic | Modifier |
|-----------|-------------|------------------|-------------|-----------------|----------|
| `SDSS-FT013` | Modifier 25 with Per Diem Codes | Edit Types Section | Using modifier 25 inappropriately to bypass same day/same service edits on per diem codes | Modifier 25 + Per Diem E/M code + Another E/M same DOS | Modifier 25 |
| `SDSS-FT014` | Modifier 25 Without Documentation | Edit Types Section | Claiming modifier 25 without significant, separately identifiable E/M documentation | Modifier 25 frequency analysis vs documentation | Modifier 25 |
| `SDSS-FT015` | Modifier 25 with Comprehensive Code Exists | Edit Types Section | Using modifier 25 when a more comprehensive code should describe all services | Modifier 25 + related procedure codes that should bundle | Modifier 25 |

---

### Category 5: Unrelated Problem Claims

| Tactic ID | Tactic Name | Policy Reference | Description | Detection Logic | Conditions |
|-----------|-------------|------------------|-------------|-----------------|------------|
| `SDSS-FT016` | False Unrelated Problem Claim | Q&A #7 | Claiming services are for "unrelated problems" when they are clinically related | Different specialty physicians + Same group + Diagnosis code relationship analysis | Different diagnosis required |
| `SDSS-FT017` | Related Diagnosis Splitting | Implicit | Assigning different but related diagnosis codes to justify separate billing | ICD code family/chapter analysis + Same DOS + Same provider group | Diagnosis code clustering |

---

## DENIAL RULES EXTRACTED FROM POLICY

| Rule ID | Rule Name | Source | Denial Code | Auto-Deny | Conditions | CPT Codes |
|---------|-----------|--------|-------------|-----------|------------|-----------|
| `DEN-001` | Per Diem Duplicate - Same Provider | CCI Definitive | SDSS-PD-SP | Yes | SAME_PROVIDER + SAME_DAY + PER_DIEM | 99221-99239 |
| `DEN-002` | Per Diem Duplicate - Same Group/Specialty | Medicare Manual | SDSS-PD-SG | Yes | SAME_GROUP + SAME_SPECIALTY + SAME_DAY + PER_DIEM | 99221-99239 |
| `DEN-003` | Initial + Subsequent Same Day | CCI Definitive | SDSS-IS | Yes | SAME_DAY + Initial code + Subsequent code | 99221-99223 + 99231-99233 |
| `DEN-004` | Hospital Visit + Discharge Same Day | CPT Descriptor | SDSS-VD | Yes | SAME_DAY + Visit code + Discharge code | 99231-99233 + 99238-99239 |
| `DEN-005` | ER + Hospital Admission Same Day | Medicare Manual | SDSS-ER-HA | Yes | SAME_DAY + SAME_PROVIDER + ER code + Initial Hospital code | 99281-99285 + 99221-99223 |
| `DEN-006` | Office + Hospital Admission Same Day | Medicare Manual | SDSS-OF-HA | Yes | SAME_DAY + SAME_PROVIDER + Office code + Initial Hospital code | 99201-99215 + 99221-99223 |
| `DEN-007` | Same Day Observation Admit/Discharge | CPT Descriptor | SDSS-OBS | Yes | SAME_DAY + Admit + Discharge (use 99234-99236 instead) | 99234-99236 |
| `DEN-008` | Covering Physician Duplicate | Medicare Manual | SDSS-COV | Yes | SAME_GROUP + SAME_SPECIALTY + SAME_DAY + Different NPI + PER_DIEM | 99221-99239 |
| `DEN-009` | Physician + QHP Duplicate | Policy Q&A #9 | SDSS-QHP | Yes | SAME_GROUP + SAME_TAXONOMY + SAME_DAY + PER_DIEM | 99221-99239 |
| `DEN-010` | Subspecialty Split Attempt | Policy Q&A #8 | SDSS-SUB | Yes | SAME_SPECIALTY + Different Subspecialty + SAME_GROUP + SAME_DAY | All E/M codes |

---

## MODIFIER REFERENCE (Policy-Relevant)

| Modifier | Name | Allowed Use (per Policy) | Abuse Scenario |
|----------|------|--------------------------|----------------|
| **25** | Significant, Separately Identifiable E/M | Second physician in same group/specialty for UNRELATED problem (non per-diem only) | Using with per-diem codes; using without documentation; using when comprehensive code exists |
| **59** | Distinct Procedural Service | Not specifically addressed in this policy | N/A for this policy |
| **76** | Repeat Procedure by Same Physician | Not specifically addressed in this policy | N/A for this policy |
| **77** | Repeat Procedure by Another Physician | Not specifically addressed in this policy | N/A for this policy |

---

## CPT CODE CATEGORIES (Policy-Relevant)

### Per Diem E/M Codes (Contain "per day" in descriptor)

| Code Range | Description | Per Diem | Site of Service |
|------------|-------------|----------|-----------------|
| 99221-99223 | Initial Hospital Care | Yes | Inpatient |
| 99231-99233 | Subsequent Hospital Care | Yes | Inpatient |
| 99234-99236 | Observation/Inpatient Same Day Admit & Discharge | Yes | Observation/Inpatient |
| 99238-99239 | Hospital Discharge Day Management | Yes | Inpatient |

### Non Per Diem E/M Codes (Can potentially use Modifier 25)

| Code Range | Description | Per Diem | Site of Service |
|------------|-------------|----------|-----------------|
| 99201-99215 | Office/Outpatient Visit | No | Office |
| 99281-99285 | Emergency Department Visit | No | ED |
| 99304-99310 | Nursing Facility Services | No | SNF |

### HCPCS Codes Referenced in Policy

| Code | Description | Policy Reference |
|------|-------------|------------------|
| G0245 | Initial physician evaluation for diabetic sensory neuropathy | CMS Definitive Edit |
| G0246 | Follow-up physician evaluation for diabetic sensory neuropathy | CMS Definitive Edit |
| G0247 | Routine foot care (must be billed with G0245 or G0246) | CMS Definitive Edit - requires principal procedure |

---

## CONDITION TYPES FOR RULE ENGINE

| Condition Type | Description | Example Value |
|----------------|-------------|---------------|
| `SAME_DAY` | Services on same date | `date_of_service = date_of_service` |
| `SAME_PROVIDER` | Same rendering provider (NPI) | `npi = npi` |
| `SAME_GROUP` | Same tax ID / group practice | `tin = tin` |
| `SAME_SPECIALTY` | Same provider specialty | `specialty_code = specialty_code` |
| `SAME_PATIENT` | Same member/patient | `member_id = member_id` |
| `PER_DIEM` | Per-day billing rule | `service_type = per_diem` |
| `SAME_TAXONOMY` | Same taxonomy code family | `taxonomy_code LIKE pattern` |

---

## DEFINITIONS (From Policy)

| Term | Definition |
|------|------------|
| **Same Specialty Physician or Other Qualified Health Care Professional** | Physicians and/or Other Qualified Healthcare Professionals of the same group and same specialty reporting the same federal Tax Identification Number. For qualified health care professionals United may, at times, identify same specialty by related taxonomy codes. |
| **Same Individual Physician or Other Qualified Health Care Professional** | The same individual rendering health care services, reporting the same National Provider Identifier (NPI). |
| **Taxonomy Code** | A unique 10-character code that designates your classification and specialization. To find the taxonomy code that most closely describes your provider type, classification, or specialization, use the National Uniform Claim Committee (NUCC) code set list. |
| **Per Diem Code** | E/M codes whose descriptors contain the phrase "per day" - meaning the code and payment represent ALL services provided on that date. |

---

## EDIT SOURCES

| Source | Type | Description |
|--------|------|-------------|
| CCI Definitive | Definitive | Sourced to specific billing guidelines from the National Correct Coding Policy Manual published by CMS |
| CMS Definitive | Definitive | Based on CMS Program Memorandums and Transmittals |
| CPT Interpreted | Interpreted | Based on interpretation of CPT book guidelines |
| Medicare Manual | Definitive | Medicare Claims Processing Manual guidance |

---

## POLICY SOURCE

**Document:** UnitedHealthcare Same Day/Same Service Policy, Professional  
**Policy Number:** 2025R0002A  
**URL:** [https://www.uhcprovider.com/content/dam/provider/docs/public/policies/comm-reimbursement/COMM-Same-Day-Service-Policy.pdf](https://www.uhcprovider.com/content/dam/provider/docs/public/policies/comm-reimbursement/COMM-Same-Day-Service-Policy.pdf)  
**Last Updated:** 5/25/2025  
**Copyright:** Proprietary information of UnitedHealthcare. Copyright 2025 United HealthCare Services, Inc.
