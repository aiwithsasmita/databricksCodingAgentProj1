# UnitedHealthcare Acupuncture Policy - Claims Adjudication Analysis

## Policy Reference

| Attribute | Value |
|-----------|-------|
| **Policy Number** | 2025R6006A |
| **Policy Name** | Acupuncture Policy, Professional |
| **Applies To** | UnitedHealthcare Commercial and Individual Exchange |
| **Claim Form** | CMS-1500 |
| **Attachment** | [UHC Acupuncture Policy PDF](https://www.uhcprovider.com/content/dam/provider/docs/public/policies/comm-reimbursement/COMM-Acupuncture-Policy.pdf) |

---

## 1. Policy Overview

### Scope
- Applies to CMS-1500 claims for UnitedHealthcare Commercial and Individual Exchange benefit plans
- Covers all network and non-network providers
- Includes non-network authorized and percent of charge contract physicians

### Definition
Acupuncture involves selection and manipulation of specific acupuncture points through:
- Needle insertion ("needling")
- Non-needling techniques focused on acupuncture points

### Billing Basis
- Services reported in **15-minute increments of personal face-to-face contact** with the patient
- Time is NOT based on duration of needle placement
- Only one initial CPT code (97810 or 97813) should be reported per day

---

## 2. CPT Codes and Maximum Frequency Per Day (MFD)

| CPT Code | Description | Max Units/Day (MFD) |
|----------|-------------|---------------------|
| 97810 | Acupuncture, 1 or more needles; without electrical stimulation, initial 15 minutes | 1 |
| 97811 | Acupuncture, without electrical stimulation, each additional 15 minutes | 2 |
| 97813 | Acupuncture, 1 or more needles; with electrical stimulation, initial 15 minutes | 1 |
| 97814 | Acupuncture, with electrical stimulation, each additional 15 minutes | 2 |
| S8930 | Acupuncture with electrical stimulation | 3 |

### Bundled Supply Codes (Not Separately Billable)

| Supply Code | Description | Status |
|-------------|-------------|--------|
| A4212 | Non-coring needle or stylet with or without catheter | Included in acupuncture service |
| A4215 | Needle, sterile, any size, each | Included in acupuncture service |

### Mutually Exclusive Electrical Stimulation Codes

| Code | Description | Cannot Bill With |
|------|-------------|------------------|
| 97014 | Electrical stimulation (unattended) | 97813, 97814, S8930 |
| 97032 | Electrical stimulation (manual) | 97813, 97814, S8930 |
| G0283 | Electrical stimulation (other than wound care) | 97813, 97814, S8930 |

---

## 3. Claim Denial Rules

### DR-001: Maximum Frequency Per Day Exceeded

| Attribute | Value |
|-----------|-------|
| **Rule ID** | DR-001 |
| **Rule Name** | MFD Exceeded |
| **Condition** | Units billed > MFD value for the CPT code |
| **Patient Condition** | Same patient |
| **Date Condition** | Same date of service |
| **Provider Condition** | Same or any rendering provider |
| **Action** | DENY excess units beyond MFD |
| **Denial Reason** | Units exceed maximum frequency per day per CMS MUE guidelines |

**MFD Reference Table:**
- 97810: Max 1 unit
- 97811: Max 2 units
- 97813: Max 1 unit
- 97814: Max 2 units
- S8930: Max 3 units

---

### DR-002: Multiple Initial Codes on Same Date

| Attribute | Value |
|-----------|-------|
| **Rule ID** | DR-002 |
| **Rule Name** | Multiple Initial Acupuncture Codes |
| **Condition** | Both 97810 AND 97813 billed on same claim/date |
| **Patient Condition** | Same patient |
| **Date Condition** | Same date of service |
| **Provider Condition** | Any provider combination |
| **Action** | DENY one initial code (typically the lower reimbursement code) |
| **Denial Reason** | CPT guidelines allow only one initial acupuncture code per day |

**Example Scenario:**
- Treatment started without electrical stimulation (97810)
- New needle inserted to complete treatment with electrical stimulation (97813)
- **Correct Billing**: 97810 (initial 15 min) + 97814 (additional time with electrical stim)
- **Incorrect Billing**: 97810 + 97813

---

### DR-003: Bundled Supply Codes

| Attribute | Value |
|-----------|-------|
| **Rule ID** | DR-003 |
| **Rule Name** | Bundled Needle Supplies |
| **Condition** | A4212 or A4215 billed with any acupuncture CPT code |
| **Patient Condition** | Same patient |
| **Date Condition** | Same date of service |
| **Acupuncture Codes** | 97810, 97811, 97813, 97814, S8930 |
| **Action** | DENY supply codes A4212 and A4215 |
| **Denial Reason** | Needle supplies included in Practice Expense per CMS NPFS |

---

### DR-004: Electrical Stimulation Mutual Exclusivity

| Attribute | Value |
|-----------|-------|
| **Rule ID** | DR-004 |
| **Rule Name** | Electrical Stimulation Code Conflict |
| **Condition** | Electrical stimulation code billed with acupuncture + electrical stim code |
| **Patient Condition** | Same patient |
| **Date Condition** | Same date of service |
| **Site Condition** | Same anatomical site/body area |
| **Conflicting Pairs** | (97014, 97032, G0283) with (97813, 97814, S8930) |
| **Action** | DENY electrical stimulation code |
| **Denial Reason** | Mutually exclusive procedures per CMS NCCI PTP edits |

**Exception Condition:**
- Modifier (59, XE, XS, XP, XU) appended to electrical stimulation code
- Documentation supports service performed on distinctly separate body part
- Services were not related to acupuncture treatment

---

### DR-005: Invalid E/M Service

| Attribute | Value |
|-----------|-------|
| **Rule ID** | DR-005 |
| **Rule Name** | E/M Service Without Separate Identifiable Service |
| **Condition** | E/M code billed without significant, separately identifiable service |
| **Patient Condition** | Same patient |
| **Date Condition** | Same date of service |
| **Provider Condition** | Same rendering provider |
| **Documentation Required** | Separate chief complaint OR new/worsening condition requiring E/M level evaluation |
| **Action** | DENY E/M code |
| **Denial Reason** | E/M service not significant and separately identifiable from acupuncture service |

**Services INCLUDED in Initial Acupuncture (Not Separately Billable as E/M):**
- Assessment provided prior to needle insertion
- Assessment provided after needle insertion
- Treatment discussion and recommendations
- Preparation
- Documentation
- Home instruction

**Modifier Requirement:** Modifier -25 typically required for separate E/M service

---

### DR-006: Non-Face-to-Face Time

| Attribute | Value |
|-----------|-------|
| **Rule ID** | DR-006 |
| **Rule Name** | Invalid Time Calculation |
| **Condition** | Time counted when provider not in face-to-face contact with patient |
| **Patient Condition** | Same patient |
| **Date Condition** | Same date of service |
| **Action** | DENY excess units |
| **Denial Reason** | Acupuncture time must reflect actual face-to-face patient contact |

**NOT Billable Time:**
- Time patient resting with needles while provider is absent
- Time provider is with other patients
- Time for room preparation/cleanup
- Total exam room duration

**Billable Time Example:**
- After needle insertion, practitioner spent time assisting a nauseous patient who had vomited

---

## 4. Exploitation Tactics and Detection Patterns

### ET-001: Date Splitting / Service Fragmentation

| Attribute | Value |
|-----------|-------|
| **Tactic ID** | ET-001 |
| **Tactic Name** | Date Splitting |
| **Method** | Provider schedules patient for multiple visits on consecutive days to maximize MFD billing each day instead of single comprehensive session |
| **Abuse Pattern** | Breaking one treatment into multiple dates to circumvent daily limits |

**Detection Indicators:**
| Indicator | Threshold |
|-----------|-----------|
| Same patient, same provider | Consecutive dates (within 48 hours) |
| Units per visit | Exactly at MFD each day |
| Visit frequency | > 3 visits per week same patient |
| Treatment pattern | Identical CPT codes each visit |

**Audit Flag Criteria:**
- Patient with > 12 acupuncture visits per month
- Average units = MFD for each visit
- No documented medical necessity for high frequency

---

### ET-002: Modifier Abuse for Electrical Stimulation Unbundling

| Attribute | Value |
|-----------|-------|
| **Tactic ID** | ET-002 |
| **Tactic Name** | Modifier Abuse |
| **Method** | Adding modifier 59/XE/XS to electrical stimulation codes to bypass bundling edit without documentation of separate body site |
| **Abuse Pattern** | Using modifiers to unbundle mutually exclusive procedures |

**Detection Indicators:**
| Indicator | Threshold |
|-----------|-----------|
| Modifier usage rate | > 50% of claims with modifier 59/XE/XS on electrical stim |
| Documentation review | No anatomical modifier or conflicting site codes |
| Billing pattern | Always billing both acupuncture + electrical stim with modifier |
| Same site indicators | No different body area modifiers (LT, RT, specific anatomical) |

**Audit Flag Criteria:**
- Provider billing 97813/97814 + 97032 with modifier 59 on > 30% of acupuncture claims
- Missing documentation of separate anatomical treatment areas

---

### ET-003: E/M Upcoding

| Attribute | Value |
|-----------|-------|
| **Tactic ID** | ET-003 |
| **Tactic Name** | E/M Upcoding |
| **Method** | Routinely billing E/M service with every acupuncture visit, claiming standard pre/post assessment as "significant and separately identifiable" |
| **Abuse Pattern** | Systematic overbilling of E/M services |

**Detection Indicators:**
| Indicator | Threshold |
|-----------|-----------|
| E/M co-billing rate | E/M billed on > 80% of acupuncture visits |
| E/M level consistency | Same E/M level (e.g., 99213) on > 90% of claims |
| Documentation pattern | No separate chief complaint documented |
| Time documentation | E/M time overlapping with acupuncture time |

**Audit Flag Criteria:**
- Provider billing 99214 with 100% of acupuncture services
- E/M documentation mirrors acupuncture assessment notes

---

### ET-004: Time Inflation

| Attribute | Value |
|-----------|-------|
| **Tactic ID** | ET-004 |
| **Tactic Name** | Time Inflation |
| **Method** | Counting total room time including needle retention time (when provider absent) as face-to-face time |
| **Abuse Pattern** | Billing for non-face-to-face time |

**Detection Indicators:**
| Indicator | Threshold |
|-----------|-----------|
| Units per session | Units suggesting > 45 minutes face-to-face routinely |
| Industry comparison | Above 90th percentile for specialty |
| Documentation review | Lacks specific face-to-face time notation |
| Appointment duration | Short appointment slots with high unit billing |

**Audit Flag Criteria:**
- Average 4+ units per session (60+ minutes face-to-face claimed)
- Standard appointment scheduling of 30-45 minutes
- Documentation states "needles retained for 30 minutes" but bills full time

---

### ET-005: Code Selection Manipulation

| Attribute | Value |
|-----------|-------|
| **Tactic ID** | ET-005 |
| **Tactic Name** | Code Selection Manipulation |
| **Method** | Billing 97813/97814 (with electrical stimulation) when electrical stimulation was not actually applied or minimally applied |
| **Abuse Pattern** | Upcoding to higher-reimbursement electrical stimulation codes |

**Detection Indicators:**
| Indicator | Threshold |
|-----------|-----------|
| Code distribution | > 95% electrical stim codes vs non-electrical stim |
| Equipment verification | No electrical stimulation equipment on file |
| Provider credentials | No training in electroacupuncture documented |
| Diagnosis pattern | Diagnoses not typically requiring electrical stimulation |

**Audit Flag Criteria:**
- Provider never bills 97810/97811
- 100% of services are 97813/97814/S8930
- No electroacupuncture certification

---

### ET-006: S8930 Maximization

| Attribute | Value |
|-----------|-------|
| **Tactic ID** | ET-006 |
| **Tactic Name** | S8930 Maximization |
| **Method** | Using S8930 instead of 97813/97814 because S8930 allows 3 units vs 2 units for 97814 |
| **Abuse Pattern** | Code selection for maximum unit allowance |

**Detection Indicators:**
| Indicator | Threshold |
|-----------|-----------|
| S8930 usage | Exclusive use of S8930 over 97813/97814 |
| Unit billing | Always billing maximum 3 units of S8930 |
| Reimbursement comparison | S8930 x 3 > 97813 + 97814 x 2 |
| Payer mix | S8930 only billed to payers where MFD = 3 |

**Audit Flag Criteria:**
- 100% S8930 usage when 97813/97814 would be clinically appropriate
- Always 3 units regardless of treatment duration

---

### ET-007: Provider Stacking

| Attribute | Value |
|-----------|-------|
| **Tactic ID** | ET-007 |
| **Tactic Name** | Provider Stacking |
| **Method** | Multiple providers (same practice, same specialty) each billing initial acupuncture code on same patient, same date |
| **Abuse Pattern** | Circumventing single initial code rule via multiple providers |

**Detection Indicators:**
| Indicator | Threshold |
|-----------|-----------|
| Initial code count | Multiple 97810 or 97813 from different NPIs |
| Practice identifier | Same TIN (Tax ID Number) |
| Service date | Same date of service |
| Specialty | Same specialty (acupuncturist, LAc, etc.) |
| Location | Same service location/place of service |

**Audit Flag Criteria:**
- 2+ initial acupuncture codes, same TIN, same date, same patient
- Both providers are licensed acupuncturists
- No documented medical necessity for multiple practitioners

---

### ET-008: Supply Code Unbundling via Separate Claims

| Attribute | Value |
|-----------|-------|
| **Tactic ID** | ET-008 |
| **Tactic Name** | Supply Unbundling |
| **Method** | Submitting needle supplies (A4212, A4215) on separate claim or different date to avoid bundling edit |
| **Abuse Pattern** | Circumventing inclusive supply edits |

**Detection Indicators:**
| Indicator | Threshold |
|-----------|-----------|
| Date pattern | Supply codes billed 1 day before/after acupuncture |
| Claim splitting | Supply codes on separate claim same date |
| Frequency | Supply billing with every patient |
| Quantity | High quantity of supplies per claim |

**Audit Flag Criteria:**
- A4212/A4215 billed within +/- 1 day of acupuncture service
- Pattern of supply billing across patient population
- Supplies billed on separate claim ID same date as acupuncture

---

## 5. Decision Flow Diagram

```
                              ┌─────────────────────────────┐
                              │     INCOMING CLAIM          │
                              │   Acupuncture Services      │
                              └─────────────┬───────────────┘
                                            │
                                            ▼
                    ┌───────────────────────────────────────────────┐
                    │  STEP 1: Check MFD Limits (DR-001)            │
                    │  - 97810 ≤ 1 unit?                            │
                    │  - 97811 ≤ 2 units?                           │
                    │  - 97813 ≤ 1 unit?                            │
                    │  - 97814 ≤ 2 units?                           │
                    │  - S8930 ≤ 3 units?                           │
                    └─────────────┬─────────────┬───────────────────┘
                                  │             │
                         PASS     │             │ FAIL
                                  ▼             ▼
                    ┌─────────────────┐   ┌─────────────────────┐
                    │   Continue      │   │ DENY Excess Units   │
                    └────────┬────────┘   └─────────────────────┘
                             │
                             ▼
                    ┌───────────────────────────────────────────────┐
                    │  STEP 2: Check Initial Code Rule (DR-002)     │
                    │  - Both 97810 AND 97813 present?              │
                    │  - Same date of service?                      │
                    └─────────────┬─────────────┬───────────────────┘
                                  │             │
                         PASS     │             │ FAIL
                                  ▼             ▼
                    ┌─────────────────┐   ┌─────────────────────┐
                    │   Continue      │   │ DENY One Initial    │
                    └────────┬────────┘   └─────────────────────┘
                             │
                             ▼
                    ┌───────────────────────────────────────────────┐
                    │  STEP 3: Check Supply Bundling (DR-003)       │
                    │  - A4212 or A4215 present?                    │
                    │  - With acupuncture code same date?           │
                    └─────────────┬─────────────┬───────────────────┘
                                  │             │
                         PASS     │             │ FAIL
                                  ▼             ▼
                    ┌─────────────────┐   ┌─────────────────────┐
                    │   Continue      │   │ DENY Supply Codes   │
                    └────────┬────────┘   └─────────────────────┘
                             │
                             ▼
                    ┌───────────────────────────────────────────────┐
                    │  STEP 4: Check Electrical Stim Edit (DR-004)  │
                    │  - 97014/97032/G0283 with 97813/97814/S8930?  │
                    │  - Same date, same site?                      │
                    │  - Valid modifier with documentation?          │
                    └─────────────┬─────────────┬───────────────────┘
                                  │             │
                         PASS     │             │ FAIL
                                  ▼             ▼
                    ┌─────────────────┐   ┌─────────────────────┐
                    │   Continue      │   │ DENY Elec Stim Code │
                    └────────┬────────┘   └─────────────────────┘
                             │
                             ▼
                    ┌───────────────────────────────────────────────┐
                    │  STEP 5: Check E/M Validity (DR-005)          │
                    │  - E/M code present?                          │
                    │  - Significant separate service documented?   │
                    │  - Modifier -25 present?                      │
                    └─────────────┬─────────────┬───────────────────┘
                                  │             │
                         PASS     │             │ FAIL
                                  ▼             ▼
                    ┌─────────────────┐   ┌─────────────────────┐
                    │   Continue      │   │ DENY E/M Code       │
                    └────────┬────────┘   └─────────────────────┘
                             │
                             ▼
                    ┌───────────────────────────────────────────────┐
                    │  STEP 6: Exploitation Pattern Check           │
                    │  - Flag for audit if patterns detected        │
                    │  - ET-001 through ET-008                      │
                    └─────────────┬─────────────────────────────────┘
                                  │
                                  ▼
                    ┌───────────────────────────────────────────────┐
                    │           CLAIM PROCESSING COMPLETE           │
                    │  - Accept valid line items                    │
                    │  - Deny per rules applied                     │
                    │  - Flag for audit if exploitation detected    │
                    └───────────────────────────────────────────────┘
```

---

## 6. Q&A Reference (From Policy)

### Q1: Can room time be billed when provider is not present?
**Answer**: No. Acupuncture code selection is based on 15-minute increments of face-to-face patient contact only. Time spent away from patient cannot be counted.

**Billable Example**: After needle insertion, practitioner spent time assisting a nauseous patient who had vomited.

### Q2: Can electrical stimulation be billed separately when on different body part?
**Answer**: Yes, if modifiers are appropriately used based on services performed and modifier description criteria are met. Documentation must support services were not related to acupuncture.

### Q3: Can both 97810 and 97813 be reported on same day?
**Answer**: No. Only one initial code may be reported per day.

**Correct Billing**: 97810 for initial 15 minutes without electrical stimulation, then 97814 for additional face-to-face time with electrical stimulation.

### Q4: What services are included in initial acupuncture (not separately billable as E/M)?
**Answer**:
- Assessment provided prior to and after needle insertion
- Treatment discussion and recommendations
- Preparation
- Documentation
- Home instruction

---

## 7. Resources

| Resource | Description |
|----------|-------------|
| American Medical Association | CPT® codes and guidelines |
| CMS HCPCS | Healthcare Common Procedure Coding System |
| CMS NCCI | National Correct Coding Initiative procedure edits |
| CMS NPFS | National Physician Fee Schedule |
| AAAOM | American Association of Acupuncture and Oriental Medicine position statements |

---

## 8. Policy History

| Date | Change |
|------|--------|
| 12/1/2017 | Policy implemented by UnitedHealthcare Employer & Individual |
| 7/12/2017 | Policy approved by Reimbursement Policy Oversight Committee |
| 8/17/2023 | Logo updated, Table of Contents removed, verbiage updated |
| 10/8/2023 | CPTs 20560 and 20561 removed from MFD table |
| 4/1/2024 | Template update - transferred to shared policy template for Commercial and Individual Exchange |
| 8/4/2025 | Policy version change, history entries archived |

---

*Document Generated: January 2026*
*Policy Source: UnitedHealthcare Reimbursement Policy 2025R6006A*
