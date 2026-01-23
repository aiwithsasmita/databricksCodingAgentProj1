# Cigna Healthcare Acupuncture Policy - Claims Adjudication Analysis

## Policy Reference

| Attribute | Value |
|-----------|-------|
| **Policy Number** | CPG 024 |
| **Policy Name** | Acupuncture - Therapy Services |
| **Applies To** | Cigna Healthcare / American Specialty Health® (ASH) |
| **Effective Date** | 4/15/2025 |
| **Next Review Date** | 4/15/2026 |
| **Attachment** | [Cigna Acupuncture Policy PDF](https://static.cigna.com/assets/chcp/pdf/coveragePolicies/medical/cpg024_acupuncture.pdf) |

---

## 1. Policy Overview

### Scope
- Applies to Cigna benefit plans administered by Cigna Companies and American Specialty Health (ASH)
- Coverage depends on specific benefit plan document terms
- Reimbursement requires submission with covered diagnosis AND procedure codes

### Definition
Acupuncture is a form of complementary and alternative medicine involving:
- Stimulation of specific anatomical locations on the skin through penetration of fine needles
- Goal: Relieving pain or treating disease
- Stimulation methods: Manual (twisting motion) or electrical stimulation (electroacupuncture)

### Key Principle
Based on traditional Chinese medicine concepts of:
- Meridians coursing through the body
- Discrete acupuncture points corresponding to specific organs
- Vital energy "chi" flowing through meridians regulating bodily functions

---

## 2. Covered Conditions (Medical Necessity Required)

### Approved Indications

| Condition | Co-Management Required |
|-----------|------------------------|
| Tension-type Headache | No |
| Migraine Headache (with or without Aura) | No |
| Musculoskeletal joint and soft tissue pain (hip, knee, spine) resulting in functional deficit | No |
| Nausea Associated with Pregnancy | **YES - Must be co-managed by medical physician** |
| Post-Surgical Nausea | **YES - Must be co-managed by medical physician** |
| Nausea Associated with Chemotherapy | **YES - Must be co-managed by medical physician** |

### Functional Deficit Examples (for Musculoskeletal Pain)
- Inability to perform household chores
- Interference with job functions
- Loss of range of motion

---

## 3. Medical Necessity Criteria

### ALL of the Following Must Be Met:

| Criterion | Description |
|-----------|-------------|
| **Defined Goals** | Services must be delivered toward defined reasonable and evidence-based goals |
| **Patient Presentation** | Decisions based on diagnosis, severity, and documented clinical findings |
| **Progression Required** | Continuation contingent upon progression towards defined treatment goals |
| **Objective Improvements** | Evidenced by specific significant objective functional improvements (outcome assessment scales, range of motion) |
| **Co-Management** | Certain conditions require co-management by medical physician |
| **Outcome Monitoring** | Change in treatment or withdrawal if patient not improving or regressing |

### Treatment Planning/Outcome Factors (ALL Required):

| Factor | Requirement |
|--------|-------------|
| **Individualized Plan** | Frequency and duration correlated with clinical findings and evidence |
| **Therapeutic Improvement** | Expected significant improvement over clearly defined period |
| **Therapeutic Goals** | Functionally oriented, realistic, measurable, evidence-based |
| **Discharge Date** | Proposed date of release/discharge from treatment estimated |
| **Functional Outcome Measures (FOM)** | Must demonstrate Minimal Clinically Important Difference (MCID) from baseline through periodic re-assessments |
| **Documentation** | Substantiates diagnosis and treatment plan |
| **Active Self-Care Progression** | Demonstration of progression toward home/self-care and discharge |
| **Maximum Benefit Not Reached** | Maximum therapeutic benefit has not been reached |

---

## 4. Not Medically Necessary Conditions

### Explicitly Excluded Indications

| Exclusion Category | Description |
|--------------------|-------------|
| General Physical Condition | Treatment intended to improve or maintain general physical condition |
| Maintenance Services | Maintenance acupuncture when significant therapeutic improvement not expected |
| Self-Administered Activities | Services that can be practiced independently and self-administered safely |
| Home Exercise Programs | Programs that can be performed safely and independently without skilled supervision |
| **Infertility** | Acupuncture for infertility - NOT medically necessary |
| **Recurrent Pregnancy Loss** | Acupuncture for recurrent pregnancy loss - NOT medically necessary |
| **Any Other Indication** | Any condition not explicitly listed as covered |

---

## 5. Experimental/Investigational/Unproven

| Procedure | Status |
|-----------|--------|
| **Acupuncture Point Injection Therapy** | Experimental, Investigational, or Unproven |

**Definition**: Procedure where pharmaceuticals and natural biologic products (vitamins, herbal extracts, homeopathics, isotonic saline) are injected into the body at acupuncture points.

---

## 6. Claim Denial Rules

### DR-001: Non-Covered Diagnosis

| Attribute | Value |
|-----------|-------|
| **Rule ID** | DR-001 |
| **Rule Name** | Non-Covered Diagnosis |
| **Condition** | Diagnosis code not in covered conditions list |
| **Covered Diagnoses** | Tension headache, Migraine, Musculoskeletal pain with functional deficit, Pregnancy/Post-surgical/Chemotherapy nausea |
| **Action** | DENY entire claim |
| **Denial Reason** | Diagnosis not covered under acupuncture benefit; service not medically necessary |

**Key Exclusions:**
- Infertility (ICD codes related to infertility)
- Recurrent pregnancy loss
- General wellness/maintenance
- Any diagnosis not explicitly listed

---

### DR-002: Missing Co-Management Documentation

| Attribute | Value |
|-----------|-------|
| **Rule ID** | DR-002 |
| **Rule Name** | Co-Management Requirement Not Met |
| **Condition** | Nausea-related diagnosis without evidence of medical physician co-management |
| **Applicable Diagnoses** | Pregnancy nausea, Post-surgical nausea, Chemotherapy nausea |
| **Documentation Required** | Referral from or concurrent treatment by MD/DO |
| **Action** | DENY claim |
| **Denial Reason** | Co-management by medical physician required for this indication |

---

### DR-003: No Functional Deficit Documented

| Attribute | Value |
|-----------|-------|
| **Rule ID** | DR-003 |
| **Rule Name** | Functional Deficit Not Documented |
| **Condition** | Musculoskeletal pain diagnosis without documented functional deficit |
| **Required Documentation** | Specific functional limitations (ADL impairment, work limitations, ROM deficit) |
| **Action** | DENY claim |
| **Denial Reason** | Musculoskeletal pain must result in functional deficit to be medically necessary |

---

### DR-004: No Individualized Treatment Plan

| Attribute | Value |
|-----------|-------|
| **Rule ID** | DR-004 |
| **Rule Name** | Missing Treatment Plan |
| **Condition** | Services billed without individualized treatment plan on file |
| **Required Elements** | Frequency, duration, goals, estimated discharge date |
| **Action** | DENY claim pending documentation |
| **Denial Reason** | Individualized treatment plan required per medical necessity criteria |

---

### DR-005: No Demonstrated Progress/Outcome Measures

| Attribute | Value |
|-----------|-------|
| **Rule ID** | DR-005 |
| **Rule Name** | Lack of Documented Progress |
| **Condition** | Continued services without documented functional improvement |
| **Required Documentation** | FOM showing MCID, updated objective findings, progression toward goals |
| **Trigger Point** | Typically after initial treatment period (4-6 visits) |
| **Action** | DENY continued services |
| **Denial Reason** | No demonstrated progression toward treatment goals; maximum therapeutic benefit may have been reached |

---

### DR-006: Maintenance Treatment

| Attribute | Value |
|-----------|-------|
| **Rule ID** | DR-006 |
| **Rule Name** | Maintenance/Palliative Services |
| **Condition** | Services to maintain current status without expected improvement |
| **Indicators** | Plateau in functional measures, same treatment indefinitely, no discharge plan |
| **Action** | DENY as not medically necessary |
| **Denial Reason** | Maintenance acupuncture services not covered when significant therapeutic improvement not expected |

---

### DR-007: Maximum Therapeutic Benefit Reached

| Attribute | Value |
|-----------|-------|
| **Rule ID** | DR-007 |
| **Rule Name** | Maximum Benefit Achieved |
| **Condition** | Patient has reached maximum therapeutic benefit |
| **Indicators** | No further functional improvement documented, treatment goals achieved, stable condition |
| **Action** | DENY further services |
| **Denial Reason** | Maximum therapeutic benefit reached; continued treatment not medically necessary |

---

### DR-008: Experimental/Investigational Procedure

| Attribute | Value |
|-----------|-------|
| **Rule ID** | DR-008 |
| **Rule Name** | Experimental Procedure |
| **Condition** | Acupuncture point injection therapy billed |
| **Applicable Codes** | Injection therapy codes at acupuncture points |
| **Action** | DENY as experimental/investigational |
| **Denial Reason** | Acupuncture point injection therapy is experimental, investigational, or unproven |

---

### DR-009: Self-Administered/Home Program Services

| Attribute | Value |
|-----------|-------|
| **Rule ID** | DR-009 |
| **Rule Name** | Services Not Requiring Skilled Provider |
| **Condition** | Services billed that can be self-administered or performed independently |
| **Examples** | Home exercise instruction only, self-acupressure training |
| **Action** | DENY as not medically necessary |
| **Denial Reason** | Services do not require skills of qualified acupuncture provider |

---

### DR-010: Missing/Invalid Diagnosis Code

| Attribute | Value |
|-----------|-------|
| **Rule ID** | DR-010 |
| **Rule Name** | Invalid Diagnosis Coding |
| **Condition** | Claim submitted without covered diagnosis code OR with non-covered diagnosis |
| **Action** | DENY as not covered |
| **Denial Reason** | Claims submitted for services not accompanied by covered code(s) will be denied as not covered |

---

## 7. Exploitation Tactics and Detection Patterns

### ET-001: Diagnosis Code Manipulation

| Attribute | Value |
|-----------|-------|
| **Tactic ID** | ET-001 |
| **Tactic Name** | Diagnosis Code Manipulation |
| **Method** | Provider assigns covered diagnosis code (e.g., musculoskeletal pain) when actual treatment is for non-covered condition (e.g., infertility, wellness) |
| **Abuse Pattern** | Upcoding diagnosis to obtain coverage |

**Detection Indicators:**
| Indicator | Threshold |
|-----------|-----------|
| Diagnosis pattern | Same diagnosis code for all patients |
| Documentation mismatch | Notes describe non-covered condition |
| Treatment location | Points used inconsistent with billed diagnosis |
| Patient history | Prior claims for infertility or non-covered conditions |

**Audit Flag Criteria:**
- Provider billing 95%+ of claims with same diagnosis code
- Documentation mentions "fertility," "wellness," "stress" when diagnosis is musculoskeletal

---

### ET-002: Fabricated Functional Deficit

| Attribute | Value |
|-----------|-------|
| **Tactic ID** | ET-002 |
| **Tactic Name** | Fabricated Functional Deficit |
| **Method** | Provider documents functional deficit without actual patient impairment to meet medical necessity for musculoskeletal conditions |
| **Abuse Pattern** | Creating false documentation to satisfy coverage criteria |

**Detection Indicators:**
| Indicator | Threshold |
|-----------|-----------|
| Documentation template | Identical functional deficit language across patients |
| Outcome measures | Same baseline scores for all patients |
| Improvement pattern | Identical improvement percentages |
| Visit pattern | Fixed number of visits regardless of presentation |

**Audit Flag Criteria:**
- Templated functional deficit documentation
- No variation in baseline or outcome measures
- 100% of patients have identical functional limitations documented

---

### ET-003: Phantom Co-Management

| Attribute | Value |
|-----------|-------|
| **Tactic ID** | ET-003 |
| **Tactic Name** | Phantom Co-Management |
| **Method** | Provider claims co-management with medical physician for nausea conditions without actual coordination of care |
| **Abuse Pattern** | False attestation of required co-management |

**Detection Indicators:**
| Indicator | Threshold |
|-----------|-----------|
| Referral verification | No referral on file from MD/DO |
| Coordination notes | No communication documentation |
| Treating physician contact | Invalid or unverifiable physician listed |
| Cross-claim verification | No claims from listed co-managing physician |

**Audit Flag Criteria:**
- High volume of nausea claims with co-management attestation
- Unable to verify co-managing physician
- No corresponding claims from medical physician for same patient

---

### ET-004: Perpetual Treatment Without Progress

| Attribute | Value |
|-----------|-------|
| **Tactic ID** | ET-004 |
| **Tactic Name** | Perpetual Treatment |
| **Method** | Provider continues treatment indefinitely by documenting minimal progress to avoid maintenance classification |
| **Abuse Pattern** | Extending treatment beyond therapeutic benefit |

**Detection Indicators:**
| Indicator | Threshold |
|-----------|-----------|
| Treatment duration | > 12 weeks without significant documented improvement |
| Outcome measures | Minimal changes that don't meet MCID |
| Visit count | > 20 visits for same condition |
| Documentation pattern | Same findings visit after visit |
| No discharge planning | Treatment plan never updated with discharge date |

**Audit Flag Criteria:**
- Patient receiving treatment > 6 months for same diagnosis
- FOM scores showing < MCID improvement
- No documented discharge plan or goal achievement

---

### ET-005: Outcome Measure Gaming

| Attribute | Value |
|-----------|-------|
| **Tactic ID** | ET-005 |
| **Tactic Name** | Outcome Measure Manipulation |
| **Method** | Provider manipulates Functional Outcome Measures (FOM) scores to show artificial MCID improvement |
| **Abuse Pattern** | Falsifying clinical measurements |

**Detection Indicators:**
| Indicator | Threshold |
|-----------|-----------|
| Score patterns | All patients show exactly MCID improvement |
| Timing | Improvement always documented at specific visit intervals |
| Score consistency | Identical score progressions across patients |
| Baseline inflation | Artificially high baseline scores |

**Audit Flag Criteria:**
- 90%+ of patients show exactly MCID improvement
- Baseline scores consistently at high end of scale
- No patients with documented regression or plateau

---

### ET-006: Treatment Plan Recycling

| Attribute | Value |
|-----------|-------|
| **Tactic ID** | ET-006 |
| **Tactic Name** | Treatment Plan Recycling |
| **Method** | Provider uses identical treatment plan template for all patients regardless of individual presentation |
| **Abuse Pattern** | Failing to individualize required treatment plans |

**Detection Indicators:**
| Indicator | Threshold |
|-----------|-----------|
| Plan similarity | Identical frequency/duration across patients |
| Goal language | Same therapeutic goals word-for-word |
| Discharge dates | Same treatment length for all |
| Clinical findings | Identical findings documented |

**Audit Flag Criteria:**
- Treatment plans > 90% identical across patient population
- No variation in prescribed frequency or duration
- Goals not specific to individual patient presentation

---

### ET-007: Diagnosis Creep/Rotation

| Attribute | Value |
|-----------|-------|
| **Tactic ID** | ET-007 |
| **Tactic Name** | Diagnosis Creep |
| **Method** | When maximum benefit reached for one diagnosis, provider switches to new covered diagnosis to restart treatment |
| **Abuse Pattern** | Rotating through diagnoses to extend coverage |

**Detection Indicators:**
| Indicator | Threshold |
|-----------|-----------|
| Diagnosis changes | New diagnosis every 8-12 weeks |
| Sequential coverage | One diagnosis ends, another begins immediately |
| Condition pattern | Rotating through headache → knee → spine → hip |
| Documentation timing | New complaint documented right when prior plateaus |

**Audit Flag Criteria:**
- Patient with 3+ different covered diagnoses in 12 months
- Each diagnosis treated to plateau then switched
- No break in treatment between diagnoses

---

### ET-008: Experimental Procedure Disguising

| Attribute | Value |
|-----------|-------|
| **Tactic ID** | ET-008 |
| **Tactic Name** | Experimental Procedure Disguising |
| **Method** | Provider performs acupuncture point injection therapy but bills as standard acupuncture |
| **Abuse Pattern** | Billing non-covered experimental procedure as covered service |

**Detection Indicators:**
| Indicator | Threshold |
|-----------|-----------|
| Supply billing | Injection supplies billed separately |
| Medication claims | Injectable medications claimed same date |
| Documentation | Notes mention "injection," "vitamin injection," "homeopathic injection" |
| Procedure time | Extended procedure time inconsistent with needling |

**Audit Flag Criteria:**
- Injection supplies or medications billed with acupuncture
- Documentation references injection therapy
- Patient complaints of injection vs. needling

---

### ET-009: Wellness Services as Medical Treatment

| Attribute | Value |
|-----------|-------|
| **Tactic ID** | ET-009 |
| **Tactic Name** | Wellness Disguised as Treatment |
| **Method** | Provider bills ongoing wellness/maintenance acupuncture as medically necessary treatment |
| **Abuse Pattern** | Converting non-covered wellness to covered medical treatment |

**Detection Indicators:**
| Indicator | Threshold |
|-----------|-----------|
| Visit pattern | Regular interval visits (weekly, bi-weekly) indefinitely |
| Documentation | Language like "wellness," "stress reduction," "preventive" |
| Functional status | No functional deficit documented |
| Patient statements | Patient describes visits as "relaxation" or "tune-up" |

**Audit Flag Criteria:**
- Ongoing treatment > 12 months with stable condition
- No documented functional limitations
- Regular recurring visits without active treatment goals

---

## 8. Key Differences from Other Payers (Summary for Comparison)

| Feature | Cigna Approach |
|---------|----------------|
| **Coverage Model** | Diagnosis-specific with medical necessity criteria |
| **Covered Conditions** | Limited to 6 specific conditions |
| **Functional Requirement** | Required for musculoskeletal pain |
| **Co-Management** | Required for all nausea indications |
| **Outcome Measures** | FOM with MCID required for continuation |
| **Treatment Planning** | Individualized plan with discharge date required |
| **Maintenance** | Explicitly excluded |
| **Infertility** | Explicitly NOT covered |
| **Point Injection** | Experimental/Investigational - NOT covered |
| **Progress Documentation** | Ongoing demonstration required |

---

## 9. Decision Flow Diagram

```
                              ┌─────────────────────────────┐
                              │     INCOMING CLAIM          │
                              │   Acupuncture Services      │
                              └─────────────┬───────────────┘
                                            │
                                            ▼
                    ┌───────────────────────────────────────────────┐
                    │  STEP 1: Diagnosis Code Check (DR-001/DR-010) │
                    │  - Is diagnosis in covered list?              │
                    │  - Headache, Migraine, MSK pain, Nausea?      │
                    └─────────────┬─────────────┬───────────────────┘
                                  │             │
                         PASS     │             │ FAIL
                                  ▼             ▼
                    ┌─────────────────┐   ┌─────────────────────┐
                    │   Continue      │   │ DENY - Non-Covered  │
                    └────────┬────────┘   │ Diagnosis           │
                             │            └─────────────────────┘
                             ▼
                    ┌───────────────────────────────────────────────┐
                    │  STEP 2: Co-Management Check (DR-002)         │
                    │  - If nausea diagnosis, is co-management      │
                    │    with MD/DO documented?                     │
                    └─────────────┬─────────────┬───────────────────┘
                                  │             │
                    PASS/N/A      │             │ FAIL (Nausea only)
                                  ▼             ▼
                    ┌─────────────────┐   ┌─────────────────────┐
                    │   Continue      │   │ DENY - Co-Management│
                    └────────┬────────┘   │ Required            │
                             │            └─────────────────────┘
                             ▼
                    ┌───────────────────────────────────────────────┐
                    │  STEP 3: Functional Deficit Check (DR-003)    │
                    │  - If MSK pain, is functional deficit         │
                    │    documented?                                │
                    └─────────────┬─────────────┬───────────────────┘
                                  │             │
                    PASS/N/A      │             │ FAIL (MSK only)
                                  ▼             ▼
                    ┌─────────────────┐   ┌─────────────────────┐
                    │   Continue      │   │ DENY - No Functional│
                    └────────┬────────┘   │ Deficit             │
                             │            └─────────────────────┘
                             ▼
                    ┌───────────────────────────────────────────────┐
                    │  STEP 4: Treatment Plan Check (DR-004)        │
                    │  - Individualized treatment plan on file?     │
                    │  - Includes frequency, duration, goals,       │
                    │    discharge date?                            │
                    └─────────────┬─────────────┬───────────────────┘
                                  │             │
                         PASS     │             │ FAIL
                                  ▼             ▼
                    ┌─────────────────┐   ┌─────────────────────┐
                    │   Continue      │   │ DENY - Missing      │
                    └────────┬────────┘   │ Treatment Plan      │
                             │            └─────────────────────┘
                             ▼
                    ┌───────────────────────────────────────────────┐
                    │  STEP 5: Progress/Outcome Check (DR-005/006/7)│
                    │  - FOM shows MCID improvement?                │
                    │  - Not maintenance treatment?                 │
                    │  - Maximum benefit not yet reached?           │
                    └─────────────┬─────────────┬───────────────────┘
                                  │             │
                         PASS     │             │ FAIL
                                  ▼             ▼
                    ┌─────────────────┐   ┌─────────────────────┐
                    │   Continue      │   │ DENY - No Progress/ │
                    └────────┬────────┘   │ Maintenance/Max     │
                             │            └─────────────────────┘
                             ▼
                    ┌───────────────────────────────────────────────┐
                    │  STEP 6: Experimental Procedure Check (DR-008)│
                    │  - Is service acupuncture point injection?    │
                    └─────────────┬─────────────┬───────────────────┘
                                  │             │
                         PASS     │             │ FAIL
                                  ▼             ▼
                    ┌─────────────────┐   ┌─────────────────────┐
                    │   Continue      │   │ DENY - Experimental │
                    └────────┬────────┘   └─────────────────────┘
                             │
                             ▼
                    ┌───────────────────────────────────────────────┐
                    │  STEP 7: Exploitation Pattern Check           │
                    │  - Flag for audit if patterns detected        │
                    │  - ET-001 through ET-009                      │
                    └─────────────┬─────────────────────────────────┘
                                  │
                                  ▼
                    ┌───────────────────────────────────────────────┐
                    │           CLAIM PROCESSING COMPLETE           │
                    │  - Accept if all criteria met                 │
                    │  - Deny per rules applied                     │
                    │  - Flag for audit if exploitation detected    │
                    └───────────────────────────────────────────────┘
```

---

## 10. Documentation Requirements Summary

| Requirement | Initial Visit | Follow-Up Visits | Continued Care |
|-------------|---------------|------------------|----------------|
| Covered Diagnosis | Required | Required | Required |
| Functional Deficit (MSK) | Required | Update | Update |
| Co-Management (Nausea) | Required | Verify ongoing | Verify ongoing |
| Individualized Treatment Plan | Required | N/A | Update if changed |
| Treatment Goals | Required | Progress notes | Progress notes |
| Estimated Discharge Date | Required | Update | Update |
| Baseline FOM | Required | N/A | N/A |
| FOM Re-assessment | N/A | Periodic | Required |
| MCID Demonstration | N/A | Required | Required |
| Progression Documentation | N/A | Required | Required |

---

## 11. Policy History

| Date | Change |
|------|--------|
| 4/15/2025 | Current effective date |
| 4/15/2026 | Next scheduled review date |

---

*Document Generated: January 2026*
*Policy Source: Cigna Medical Coverage Policy CPG 024 - Acupuncture*
