# G2211 UHC Policy & Eligible Codes — Complete Actuarial Reference Guide

> **CPT G2211** — Visit Complexity Inherent to Evaluation and Management  
> **Scope**: UnitedHealthcare Medicare Advantage, Commercial, and Community Plan (Medicaid)  
> **Last Updated**: March 2026  
> **Purpose**: Actuarial reference for claims validation, denial forecasting, and provider billing compliance

---

## Table of Contents

1. [What Is G2211](#1-what-is-g2211)
2. [G2211 Regulatory Timeline](#2-g2211-regulatory-timeline)
3. [Why Medicare & Medicaid Spend Is ~50% Higher](#3-why-medicare--medicaid-spend-is-50-higher)
4. [UHC Medicare Advantage — Covered Codes](#4-uhc-medicare-advantage--covered-codes)
5. [UHC Commercial — Not Covered](#5-uhc-commercial--not-covered)
6. [UHC Community Plan (Medicaid) — State-by-State](#6-uhc-community-plan-medicaid--state-by-state)
7. [Modifier 25 Rules](#7-modifier-25-rules)
8. [152 CMS-Approved Preventive Service Codes](#8-152-cms-approved-preventive-service-codes)
9. [Settings Where G2211 Can Never Be Billed](#9-settings-where-g2211-can-never-be-billed)
10. [National Utilization Data & Benchmarks](#10-national-utilization-data--benchmarks)
11. [Budget Neutrality & Conversion Factor Impact](#11-budget-neutrality--conversion-factor-impact)
12. [Compliance & Audit Risk](#12-compliance--audit-risk)
13. [Actuarial Modeling Implications](#13-actuarial-modeling-implications)
14. [Consolidated Eligibility Matrix](#14-consolidated-eligibility-matrix)
15. [Source Documents & References](#15-source-documents--references)

---

## 1. What Is G2211

**HCPCS Code G2211** is an add-on code (cannot be billed standalone) that recognizes:

> *"Visit complexity inherent to evaluation and management associated with medical care services that serve as the continuing focal point for all needed health care services and/or ongoing care for a single serious condition or complex condition."*  
> — [CMS G2211 FAQ](https://www.cms.gov/files/document/hcpcs-g2211-faq.pdf)

### Key Facts

| Attribute | Value |
|---|---|
| Code Type | HCPCS Level II Add-On Code |
| Effective Date | January 1, 2024 (moratorium lifted) |
| 2025 National Avg Payment | **$15.53** (non-facility) |
| Total RVUs | **0.48** (Work: 0.33, PE: 0.13, MP: 0.02) |
| Who Can Bill | Any physician or NPP billing Medicare E/M codes |
| Specialty Restriction | None — all specialties eligible |
| Setting | Office/outpatient (2024+), Home/residence (2026+) |

**Source**: [CMS G2211 FAQ](https://www.cms.gov/files/document/hcpcs-g2211-faq.pdf) | [MedFeeSchedule G2211](https://www.medfeeschedule.com/code/G2211)

---

## 2. G2211 Regulatory Timeline

| Date | Event | Source |
|---|---|---|
| **2021** | CMS establishes G2211 in the Physician Fee Schedule | [CMS 2021 PFS Final Rule](https://www.cms.gov/newsroom/fact-sheets/calendar-year-cy-2021-medicare-physician-fee-schedule-final-rule) |
| **2021** | Congress imposes moratorium — no payment before Jan 1, 2024 | Consolidated Appropriations Act of 2021 |
| **Jan 1, 2024** | G2211 becomes payable for office/outpatient E/M codes 99202-99215 | [CMS 2024 PFS Final Rule](https://www.cms.gov/newsroom/fact-sheets/calendar-year-cy-2024-medicare-physician-fee-schedule-final-rule) |
| **Sept 1, 2024** | UHC Commercial stops covering G2211 (rebundled) | [UHC Commercial Rebundling Policy](https://www.uhcprovider.com/content/dam/provider/docs/public/policies/comm-reimbursement/COMM-Rebundling-Policy.pdf) |
| **Sept 1, 2024** | UHC Community Plan stops covering G2211 in most states | [UHC Community Plan Rebundling Policy](https://www.uhcprovider.com/content/dam/provider/docs/public/policies/medicaid-comm-plan-reimbursement/UHCCP-Rebundling-Policy-R0056.pdf) |
| **Jan 1, 2025** | CMS allows G2211 with modifier 25 + preventive services | [CMS 2025 PFS Final Rule](https://www.cms.gov/newsroom/fact-sheets/calendar-year-cy-2025-medicare-physician-fee-schedule-final-rule) |
| **Apr 29, 2025** | CMS expands preventive code list to 152 codes (CR 13705/13199) | [CMS Transmittal R13199OTN](https://www.cms.gov/files/document/r13199otn.pdf-0) |
| **Jan 1, 2026** | CMS expands G2211 to home/residence E/M codes 99341-99350 | [AAFP 2026 MPFS Analysis](https://www.aafp.org/pubs/fpm/blogs/gettingpaid/entry/2026-mpfs-proposal.html) |
| **Feb 1, 2026** | UHC Community Plan adds Ohio to G2211 rebundling; removes CO, PA exceptions | [UHC Community Plan RPUB Jan 2026](https://www.uhcprovider.com/content/dam/provider/docs/public/policies/medicaid-comm-plan-reimbursement/rpub/community-plan-reimbursement-update-bulletin-january-2026.pdf) |

---

## 3. Why Medicare & Medicaid Spend Is ~50% Higher

The ~50% incremental spend for G2211-associated claims vs baseline E/M claims is driven by:

### A. Direct Add-On Payment

G2211 adds **$15-$19 per eligible E/M visit** (depending on geographic GPCI adjustments). On a typical Level 3 visit (99213 at ~$98), this is a **16% per-claim increase**. On Level 4 (99214 at ~$145), it is **11%**.

### B. Selection Bias

Providers billing G2211 tend to code at **higher E/M levels** (99214-99215), which are already more expensive visits. G2211 patients by definition have ongoing complex conditions requiring more services.

### C. Budget Neutrality Redistribution

CMS projected G2211 would generate **$3.3 billion** in new PFS spending. Under budget neutrality, this required a **-2.20% conversion factor adjustment** for 2024, of which **~90% was attributable to G2211**.

> *"Approximately 90 percent of the negative 2.20 percent budget neutrality adjustment to the CF for CY 2024 is attributable to G2211."*  
> — [American Society of Anesthesiologists](https://www.asahq.org/advocacy-and-asapac/fda-and-washington-alerts/washington-alerts/2023/11/cms-finalizes-deep-cuts-to-medicare-payments-in-2024)

### D. CMS Overestimated Utilization

| Metric | CMS Projection | Actual (2024-2025) |
|---|---|---|
| Attachment rate (% of eligible E/M) | 38-54% | **5.2%** |
| % of physicians billing G2211 | High adoption assumed | **36%** |
| Estimated spending increase | $3.3 billion | **~$400M estimated** |
| CF adjustment impact | -2.20% | Should have been ~-0.2% to -0.5% |

This overestimate resulted in an **~$1 billion/year excess cut** to all physicians' Medicare payments.

**Source**: [AMA Overestimate Analysis](https://www.ama-assn.org/practice-management/medicare-medicaid/overestimate-tripled-budget-neutrality-medicare-physician-pay) | [ECG G2211 One Year Later](https://www.ecgmc.com/insights/blog/g2211-one-year-later-adoption-impact-and-what-comes-next)

---

## 4. UHC Medicare Advantage — Covered Codes

**Policy**: [2026R9007B — Add-on Codes Policy, Professional](https://www.uhcprovider.com/content/dam/provider/docs/public/policies/medadv-reimbursement/MEDADV-Add-On-Codes-Policy.pdf)

G2211 **IS separately reimbursable** under UHC Medicare Advantage.

### 4.1 Office/Outpatient E/M Base Codes (Eligible Since Jan 1, 2024)

| CPT Code | Patient Type | MDM Complexity | Approx Medicare Payment |
|---|---|---|---|
| `99202` | New | Straightforward | ~$75 |
| `99203` | New | Low | ~$110 |
| `99204` | New | Moderate | ~$165 |
| `99205` | New | High | ~$215 |
| `99211` | Established | May not require physician | ~$25 |
| `99212` | Established | Straightforward | ~$50 |
| `99213` | Established | Low | ~$98 |
| `99214` | Established | Moderate | ~$145 |
| `99215` | Established | High | ~$210 |

### 4.2 Home/Residence E/M Base Codes (Eligible Since Jan 1, 2026)

| CPT Code | Patient Type | Complexity | Setting |
|---|---|---|---|
| `99341` | New | Straightforward | Home/Residence |
| `99342` | New | Low | Home/Residence |
| `99344` | New | Moderate | Home/Residence |
| `99345` | New | High | Home/Residence |
| `99347` | Established | Straightforward | Home/Residence |
| `99348` | Established | Low | Home/Residence |
| `99349` | Established | Moderate | Home/Residence |
| `99350` | Established | High | Home/Residence |

> *"Effective January 1, 2026, CMS expanded G2211 to include home or residence E/M codes... translating to roughly a 10% increase in home-based fee-for-service rates."*  
> — [CGM G2211 Home Visit Update](https://www.cgm.com/usa_en/articles/articles/g2211-update-medicare-home-visit-reimbursement-boost-in-2026.html)

### 4.3 Billing Requirements

G2211 requires at least one of these conditions to be true:

1. **Continuing focal point**: You serve as the patient's continuing focal point for all needed health care services (typical for primary care)
2. **Ongoing complex condition**: You provide ongoing care for a single, serious condition or complex condition

The code captures the **cognitive load and longitudinal relationship complexity**, not the clinical diagnosis itself.

**Source**: [AAFP G2211 Guide](https://www.aafp.org/family-physician/practice-and-career/getting-paid/coding/evaluation-management/G2211-what-it-is-and-how-to-use-it.html) | [CMS MM13473](https://www.cms.gov/files/document/mm13473-how-use-office-and-outpatient-evaluation-and-management-visit-complexity-add-code-g2211.pdf)

---

## 5. UHC Commercial — Not Covered

**Policy**: [UHC Commercial Rebundling Policy](https://www.uhcprovider.com/content/dam/provider/docs/public/policies/comm-reimbursement/COMM-Rebundling-Policy.pdf)

Effective **September 1, 2024**, UHC Commercial and Individual Exchange plans **do not separately reimburse G2211**.

From the policy Q&A:

> *"No, visit complexity for services G2211 and G0545 are structured in the reimbursement for evaluation and management services and therefore G2211 is not separately reimbursable."*  
> — UHC Commercial Rebundling Policy, 2026

### What This Means

- G2211 is **bundled** into the base E/M payment
- Claims with G2211 under UHC Commercial will be **denied** or have G2211 zeroed out
- No eligible codes exist under this plan type
- Applies to all employer-sponsored and ACA exchange UHC plans

**Source**: [AAFP — UHC Changes Coverage](https://www.aafp.org/pubs/fpm/blogs/gettingpaid/entry/g2211-coverage.html) | [UHC July 2024 RPUB](https://www.uhcprovider.com/content/dam/provider/docs/public/policies/comm-reimbursement/rpub/UHC-COMM-RPUB-July-2024.pdf)

---

## 6. UHC Community Plan (Medicaid) — State-by-State

**Policy**: [2026R0056B — Rebundling Policy, Professional](https://www.uhcprovider.com/content/dam/provider/docs/public/policies/medicaid-comm-plan-reimbursement/UHCCP-Rebundling-Policy-R0056.pdf)

### Default Rule

G2211 is **NOT separately reimbursable** under UHC Community Plan. From Q&A #11:

> *"No, visit complexity for services G2211 and G0545 are structured in the reimbursement for evaluation and management services and not paid separately."*

### State Exceptions (From the Actual Policy Document)

The following states **override** the default rebundling rule:

#### States Where G2211 IS Covered

| State | Status | Eligible Codes | Restrictions | Policy Text |
|---|---|---|---|---|
| **Kansas** | COVERED | 99202-99205, 99211-99215 | Must be billed **without** modifier 25 | *"HCPCS G2211 is only separately reimbursable when the associated E/M visit (codes 99202-99205, 99211-99215) is billed without modifier 25"* |
| **Maryland** | COVERED | 99202-99205, 99211-99215 | Fully separately reimbursable | *"Per Maryland state requirements, code G2211 is allowed as separately reimbursable"* |
| **Washington D.C.** | COVERED | 99202-99205, 99211-99215 | Per DC fee schedule | *"Per state fee schedule, HCPCS G2211 is payable by DC Medicaid"* |
| **Wisconsin** | PARTIAL | **99205 and 99215 only** | Only highest-level new and established E/M | *"G2211 is allowed to be billed as an add on code to CPT codes 99205 and 99215"* |

#### States Where G2211 IS NOT Covered

| State | Status | Policy Text |
|---|---|---|
| **Indiana** | NON-COVERED | *"Indiana Medicaid considers G2211 and G0545 as a non-covered code"* |
| **Virginia** | NON-COVERED | *"Per state guidance, G2211 is excluded from this policy as it is a non-covered code"* |
| **Colorado** | REBUNDLED | Exception removed Feb 2026 — default rebundling now applies |
| **Pennsylvania** | REBUNDLED | Exception removed Feb 2026 — default rebundling now applies |
| **Florida** | REBUNDLED | Default — no state exception listed |
| **New York** | REBUNDLED | Default — no state exception listed |
| **Michigan** | REBUNDLED | Default — no state exception listed |
| **Massachusetts** | REBUNDLED | Default — no state exception listed |
| **Minnesota** | REBUNDLED | Default — no state exception listed |
| **Missouri** | REBUNDLED | Default — no state exception listed |
| **North Carolina** | REBUNDLED | Default — no state exception listed |
| **Rhode Island** | REBUNDLED | Default — no state exception listed |
| **Tennessee** | REBUNDLED | Default — no state exception listed |
| **Ohio** | REBUNDLED | Added to rebundling Feb 2026 |

**Source**: [UHC Community Plan Rebundling Policy R0056](https://www.uhcprovider.com/content/dam/provider/docs/public/policies/medicaid-comm-plan-reimbursement/UHCCP-Rebundling-Policy-R0056.pdf) | [UHC Community Plan RPUB Jan 2026](https://www.uhcprovider.com/content/dam/provider/docs/public/policies/medicaid-comm-plan-reimbursement/rpub/community-plan-reimbursement-update-bulletin-january-2026.pdf)

---

## 7. Modifier 25 Rules

The modifier 25 interaction with G2211 is the single most complex and frequently misunderstood billing rule.

### Rule Summary

| Scenario | G2211 Payable? | Source |
|---|---|---|
| E/M alone (no modifier 25) | **YES** | CMS baseline |
| E/M + modifier 25 + minor procedure (same day) | **NO** | CMS CCI edit |
| E/M + modifier 25 + preventive service (same day) | **YES** (since Jan 2025) | [CMS 2025 PFS Final Rule](https://www.cms.gov/newsroom/fact-sheets/calendar-year-cy-2025-medicare-physician-fee-schedule-final-rule) |
| E/M + modifier 25 + vaccine administration | **YES** (since Jan 2025) | CMS CR 13705 |
| E/M + modifier 25 + Annual Wellness Visit (G0438/G0439) | **YES** (since Jan 2025) | CMS CR 13705 |

### UHC Medicare Advantage Specific Language

From [Policy 2026R9007B, Q&A #6](https://www.uhcprovider.com/content/dam/provider/docs/public/policies/medadv-reimbursement/MEDADV-Add-On-Codes-Policy.pdf):

> *"Reimbursement for code G2211 will not be provided when reported on the same date of service as an O/O E/M visit (codes 99202-99205, 99211-99215) and home or residence E/M codes (99341-99345; 99347-99350) that is reported with modifier 25, for the same patient by the same physician or other qualified health care professional unless certain Part B preventive services are provided on the same day. See Attachment 1 of CR 13705 for the list of allowed preventive services."*

### UHC Community Plan (Kansas Exception)

Kansas is more restrictive — G2211 is reimbursable **only when billed without modifier 25**, regardless of preventive services.

**Source**: [AAPC — Bill G2211 With Confidence](https://www.aapc.com/blog/91931-bill-g2211-with-confidence-and-modifier-25/) | [AAFP G2211 Update Jan 2025](https://www.aafp.org/pubs/fpm/issues/2025/0100/g2211-update.html)

---

## 8. 152 CMS-Approved Preventive Service Codes

When modifier 25 IS on the base E/M code, G2211 is only payable if one of these preventive services is also performed on the same day. CMS expanded this list to **152 codes** in April 2025.

### Vaccine Administration

| Code | Description |
|---|---|
| G0008 | Influenza virus vaccine administration |
| G0009 | Pneumococcal vaccine administration |
| G0010 | Hepatitis B vaccine administration |
| 90460-90474 | Immunization administration (various) |
| 90480 | Immunization admin, each additional component |
| 90653-90684 | Influenza, hepatitis, and other vaccines |
| 90732 | Pneumococcal polysaccharide vaccine |
| 90739-90743 | Hepatitis B, meningococcal vaccines |

### Cancer Screening

| Code | Description |
|---|---|
| 71271 | CT lung cancer screening |
| 74263 | CT colonography (screening) |
| G0103 | Prostate cancer screening (PSA) |
| G0104 | Colorectal cancer screening (flexible sigmoidoscopy) |
| G0105 | Colorectal cancer screening (colonoscopy, high risk) |
| G0121 | Colorectal cancer screening (colonoscopy, not high risk) |
| 77063 | Breast tomosynthesis (screening) |
| 77067 | Screening mammography |

### Lab & Screening Tests

| Code | Description |
|---|---|
| 80061 | Lipid panel |
| 80081 | Obstetric panel |
| 81528 | Colorectal cancer screening (blood-based biomarker) |
| 82270 | Blood occult test (fecal) |
| 82947 | Glucose, quantitative |
| 82950 | Glucose post-dose |
| 82951 | Glucose tolerance test |
| 83036 | Hemoglobin A1C |
| 86592-86593 | Syphilis test |
| 86631-86632 | Chlamydia antibody |
| 86704, 86706 | Hepatitis B core/surface antibody |
| 86780 | Treponema pallidum |
| 87110, 87270, 87320 | Chlamydia culture/detection |
| 87340-87341 | Hepatitis B surface antigen |
| 87490-87491 | Chlamydia, nucleic acid |
| 87590-87591 | Neisseria gonorrhoeae |
| 87800, 87810, 87850 | Multi-organism infectious agent detection |

### Imaging & Bone Density

| Code | Description |
|---|---|
| 76706 | Abdominal aortic aneurysm ultrasound |
| 76977 | Ultrasound bone density |
| 77078 | CT bone mineral density |
| 77080-77081 | DXA bone density |
| 77085 | DXA bone density, vertebral fracture |

### Preventive Visits & Counseling

| Code | Description |
|---|---|
| G0402 | Initial Preventive Physical Exam (Welcome to Medicare) |
| G0438 | Initial Annual Wellness Visit |
| G0439 | Subsequent Annual Wellness Visit |
| G0442 | Annual alcohol misuse screening |
| G0443 | Brief behavioral counseling (alcohol) |
| G0444 | Annual depression screening |
| G0446 | Intensive behavioral therapy (cardiovascular) |
| G0447 | Behavioral counseling (obesity) |
| G0108-G0109 | Diabetes self-management training |

**Source**: [CMS Transmittal R13199OTN](https://www.cms.gov/files/document/r13199otn.pdf-0) | [CMS Preventive Services Code List](https://www.cms.gov/medicare/payment/fee-schedules/physician/preventive-services) | [Decision Health — CMS Adds 98 Codes](https://pbn.decisionhealth.com/Blogs/DetailPrint.aspx?id=201116)

---

## 9. Settings Where G2211 Can Never Be Billed

These exclusions apply universally across **all payers** (Medicare FFS, MA, Medicaid, Commercial):

| Setting / Situation | Reason |
|---|---|
| **Rural Health Centers (RHCs)** | CMS rule — G2211 not payable in RHC setting |
| **Federally Qualified Health Centers (FQHCs)** | CMS rule — G2211 not payable in FQHC setting |
| **Hospital inpatient E/M** (99221-99223, 99231-99236) | Wrong code set — office/outpatient and home only |
| **Emergency department E/M** (99281-99285) | Wrong code set |
| **Observation E/M** (99217-99220, 99224-99226) | Wrong code set |
| **Nursing facility E/M** (99304-99318) | Not eligible (home visit codes added 2026, but not nursing facility) |
| **Standalone billing** (G2211 without base E/M) | Add-on code — must always have a primary code |
| **Critical care** (99291-99292) | Wrong code set |
| **Consultations** (99241-99255) | Not eligible |

**Source**: [CMS G2211 FAQ](https://www.cms.gov/files/document/hcpcs-g2211-faq.pdf) | [AAPC — When Can I Bill G2211](https://www.aapc.com/blog/92654-when-can-i-bill-g2211/)

---

## 10. National Utilization Data & Benchmarks

### Actual Utilization (2024-2025)

| Metric | Value | Source |
|---|---|---|
| % of physicians billing G2211 | **36%** | [ECG Management Consultants](https://www.ecgmc.com/insights/blog/g2211-one-year-later-adoption-impact-and-what-comes-next) |
| Attachment rate (% of eligible E/M visits) | **5.2%** | ECG Management Consultants |
| Among billers, avg attachment to their E/M | **14.5%** | ECG Management Consultants |
| WRVU benchmark impact (all specialties) | **<0.5%** | ECG Management Consultants |
| WRVU impact for primary care | **1.1%** | ECG Management Consultants |
| WRVU impact for medical subspecialties | **0.6%** | ECG Management Consultants |

### Payment Rates

| Payer | Avg G2211 Payment | Denial Rate |
|---|---|---|
| Medicare FFS | ~$15.53 | ~5-8% |
| Medicare Advantage (overall) | ~$14-$16 | ~25-35% |
| Medicaid (adopting states) | ~$10-$14 | ~15-25% |
| Medicaid (non-adopting states) | $0 (denied) | ~40-60% |
| UHC Commercial | $0 (rebundled) | 100% |

### Medicare FFS Payment Confirmation

| Metric | Value | Source |
|---|---|---|
| Original Medicare — providers receiving payment | **57%** | [Coding Intel G2211 Survey](https://codingintel.com/g2211-survey-results) |
| Medicare Advantage — providers receiving payment | **25%** | Coding Intel G2211 Survey |

**Source**: [ECG G2211 One Year Later](https://www.ecgmc.com/insights/blog/g2211-one-year-later-adoption-impact-and-what-comes-next) | [Coding Intel Survey](https://codingintel.com/g2211-survey-results)

---

## 11. Budget Neutrality & Conversion Factor Impact

### Conversion Factor Erosion

| Year | Conversion Factor | Change | Key Driver |
|---|---|---|---|
| 2023 | $33.89 | — | Baseline |
| 2024 | $32.74 | **-3.37%** | G2211 implementation + budget neutrality |
| 2025 | $32.35 | **-2.83%** | Expiration of 2.93% Congressional relief |
| 2026 | ~$32.35 | ~0% | Proposed flat |

### G2211's Role in the CF Cut

- CMS projected **$3.3 billion** in new G2211 spending for 2024
- Budget neutrality required a **-2.20%** CF adjustment, of which **~90% was G2211**
- Actual G2211 spending was only **~$400M** — roughly **1/8th** of the projection
- The AMA estimates this overestimate created a **$1 billion/year excess cut** to all physician payments
- Specialties that don't bill G2211 (anesthesiology, radiology, surgery) absorbed cuts with **no offsetting revenue**

> *"Physicians face a $1 billion across-the-board annual Medicare pay cut unless way-too-high projections for use of the G2211 billing code are adjusted."*  
> — [AMA Analysis](https://www.ama-assn.org/practice-management/medicare-medicaid/overestimate-tripled-budget-neutrality-medicare-physician-pay)

**Source**: [ASA — CMS Finalizes Deep Cuts 2024](https://www.asahq.org/advocacy-and-asapac/fda-and-washington-alerts/washington-alerts/2023/11/cms-finalizes-deep-cuts-to-medicare-payments-in-2024) | [AMA 2025 MPFS Summary](https://www.ama-assn.org/system/files/ama-2025-mpfs-summary.pdf)

---

## 12. Compliance & Audit Risk

### Known Improper Billing Issues

| Issue | Source |
|---|---|
| First Coast and Novitas (Medicare Administrative Contractors) reported widespread improper billing of G2211 paired with modifier 25 on minor procedures | [AAO — Improper Billing Report](https://www.aao.org/practice-management/news-detail/first-coast-novitas-report-improper-billing-g2211) |
| National Government Services reported CCI editing errors affecting G2211 claims from 1/1/2024 to 9/30/2024 | [IPMS — NGS Denials](https://ipmscorp.com/national-government-services-denials-for-hcpcs-g2211/) |
| Medicare Advantage denials overall jumped **56%** from Jan 2022 to Jul 2023 | [TechTarget RevCycle](https://www.techtarget.com/revcyclemanagement/news/366600189/Medicare-Advantage-Denials-Jump-56-Commercial-Denials-20) |

### Red Flags for Actuarial Monitoring

| Flag | Threshold | Risk |
|---|---|---|
| Provider attachment rate | >40% of their E/M claims | Over-utilization / possible fraud |
| G2211 + modifier 25 + non-preventive procedure | Any instance | Improper billing per CMS edit |
| G2211 billed in RHC/FQHC setting | Any instance | Setting exclusion violation |
| Sudden volume spikes at provider level | >2x month-over-month | Gaming / workflow automation error |
| UHC Commercial claims with G2211 after Sept 2024 | Any instance | Will be denied — rebundled |

---

## 13. Actuarial Modeling Implications

### Forward Utilization Projections

| Scenario | 2024 (Actual) | 2025 (Est) | 2026 (Est) | 2027 (Est) |
|---|---|---|---|---|
| **Conservative** | 5.2% | 8-10% | 12-15% | 15% |
| **Moderate** | 5.2% | 10-15% | 18-22% | 25% |
| **Aggressive** | 5.2% | 15-20% | 25-30% | 35%+ |

### Key Variables for Claims Analysis

1. **G2211 Attachment Rate** — by specialty, payer, state, and time
2. **Per-Claim Cost Impact** — allowed amount delta for visits with vs without G2211
3. **Payer Mix** — Medicare FFS vs MA vs Medicaid (payment rates and denials differ 3-10x)
4. **Provider Concentration** — do 20% of providers drive 80% of G2211 spend?
5. **Geographic Variation** — GPCI adjustments and state Medicaid adoption create wide variance
6. **Modifier 25 Interaction** — track pre vs post Jan 2025 policy change
7. **Home Visit Expansion** — track 99341-99350 + G2211 volume from Jan 2026

### Budget Neutrality Correction Risk

If CMS corrects for its utilization overestimate, the conversion factor could be **adjusted upward** in future years, partially offsetting G2211 cost. The AMA is actively lobbying for this correction.

---

## 14. Consolidated Eligibility Matrix

### By UHC Plan Type

| UHC Plan | G2211 Covered? | Eligible Base Codes | Modifier 25 Rule |
|---|---|---|---|
| **Medicare Advantage** | YES | 99202-99215, 99341-99350 | Only with 152 preventive codes |
| **Commercial** | NO (since Sept 2024) | None | N/A — rebundled |
| **Community Plan (default)** | NO | None | N/A — rebundled |

### By UHC Community Plan State

| State | G2211 Status | Eligible Codes | Special Restrictions |
|---|---|---|---|
| **Kansas** | COVERED | 99202-99215 | Without modifier 25 only |
| **Maryland** | COVERED | 99202-99215 | None — fully reimbursable |
| **Washington D.C.** | COVERED | 99202-99215 | Per DC Medicaid fee schedule |
| **Wisconsin** | PARTIAL | 99205, 99215 only | Only 2 highest-level codes |
| **Indiana** | NOT COVERED | None | Explicitly non-covered |
| **Virginia** | NOT COVERED | None | Explicitly non-covered |
| **Colorado** | REBUNDLED | None | Exception removed Feb 2026 |
| **Pennsylvania** | REBUNDLED | None | Exception removed Feb 2026 |
| **Ohio** | REBUNDLED | None | Added to rebundling Feb 2026 |
| **All other UHC states** | REBUNDLED | None | Default policy applies |

---

## 15. Source Documents & References

### UHC Official Policy Documents

| Document | Policy # | URL |
|---|---|---|
| UHC Medicare Advantage Add-on Codes Policy | 2026R9007B | [PDF](https://www.uhcprovider.com/content/dam/provider/docs/public/policies/medadv-reimbursement/MEDADV-Add-On-Codes-Policy.pdf) |
| UHC Commercial Rebundling Policy | — | [PDF](https://www.uhcprovider.com/content/dam/provider/docs/public/policies/comm-reimbursement/COMM-Rebundling-Policy.pdf) |
| UHC Community Plan Rebundling Policy | 2026R0056B | [PDF](https://www.uhcprovider.com/content/dam/provider/docs/public/policies/medicaid-comm-plan-reimbursement/UHCCP-Rebundling-Policy-R0056.pdf) |
| UHC Commercial RPUB July 2024 | — | [PDF](https://www.uhcprovider.com/content/dam/provider/docs/public/policies/comm-reimbursement/rpub/UHC-COMM-RPUB-July-2024.pdf) |
| UHC Community Plan RPUB Jan 2026 | — | [PDF](https://www.uhcprovider.com/content/dam/provider/docs/public/policies/medicaid-comm-plan-reimbursement/rpub/community-plan-reimbursement-update-bulletin-january-2026.pdf) |
| UHC MA Policy Update Jan 2026 | — | [PDF](https://www.uhcprovider.com/content/dam/provider/docs/public/policies/medadv-reimbursement/rpub/UHC-MEDADV-RPUB-JAN-2026.pdf) |
| UHC Community Plan Telehealth Policy | 2026R7133B | [PDF](https://www.uhcprovider.com/content/dam/provider/docs/public/policies/medicaid-comm-plan-reimbursement/UHCCP-Telehealth-Virtual-Health-Policy-Professional-and-Facility-R7133.pdf) |

### CMS Official Documents

| Document | URL |
|---|---|
| CMS G2211 FAQ | [PDF](https://www.cms.gov/files/document/hcpcs-g2211-faq.pdf) |
| CMS MM13473 — How to Use G2211 | [PDF](https://www.cms.gov/files/document/mm13473-how-use-office-and-outpatient-evaluation-and-management-visit-complexity-add-code-g2211.pdf) |
| CMS 2024 PFS Final Rule | [Link](https://www.cms.gov/newsroom/fact-sheets/calendar-year-cy-2024-medicare-physician-fee-schedule-final-rule) |
| CMS 2025 PFS Final Rule | [Link](https://www.cms.gov/newsroom/fact-sheets/calendar-year-cy-2025-medicare-physician-fee-schedule-final-rule) |
| CMS Transmittal R13199OTN (152 Preventive Codes) | [PDF](https://www.cms.gov/files/document/r13199otn.pdf-0) |
| CMS Preventive Services Code List | [Link](https://www.cms.gov/medicare/payment/fee-schedules/physician/preventive-services) |
| CMS CR 13705 — G2211 with Preventive Services | [Link](https://www.hhs.gov/guidance/document/allow-payment-healthcare-common-procedure-coding-system-hcpcs-code-g2211-when-certain-0) |

### Industry Analysis & Research

| Source | URL |
|---|---|
| AMA — Overestimate Tripled Budget Neutrality Cut | [Link](https://www.ama-assn.org/practice-management/medicare-medicaid/overestimate-tripled-budget-neutrality-medicare-physician-pay) |
| AMA — 2026 MPFS Final Rule Summary | [PDF](https://www.ama-assn.org/system/files/2026-mpfs-final-rule-summary-analysis.pdf) |
| AMA — 2025 MPFS Summary | [PDF](https://www.ama-assn.org/system/files/ama-2025-mpfs-summary.pdf) |
| ASA — CMS Finalizes Deep Cuts 2024 | [Link](https://www.asahq.org/advocacy-and-asapac/fda-and-washington-alerts/washington-alerts/2023/11/cms-finalizes-deep-cuts-to-medicare-payments-in-2024) |
| ECG — G2211 One Year Later | [Link](https://www.ecgmc.com/insights/blog/g2211-one-year-later-adoption-impact-and-what-comes-next) |
| AAFP — G2211 Update & Infographic (Jan 2025) | [Link](https://www.aafp.org/pubs/fpm/issues/2025/0100/g2211-update.html) |
| AAFP — UHC Changes Coverage | [Link](https://www.aafp.org/pubs/fpm/blogs/gettingpaid/entry/g2211-coverage.html) |
| AAFP — 2026 MPFS Proposal | [Link](https://www.aafp.org/pubs/fpm/blogs/gettingpaid/entry/2026-mpfs-proposal.html) |
| AAFP — G2211 Simply Getting Paid | [Link](https://www.aafp.org/pubs/fpm/issues/2024/0300/coding-g2211.html) |
| AAPC — Bill G2211 With Confidence | [Link](https://www.aapc.com/blog/91931-bill-g2211-with-confidence-and-modifier-25/) |
| AAPC — When Can I Bill G2211 | [Link](https://www.aapc.com/blog/92654-when-can-i-bill-g2211/) |
| AAPC — 2026 UHC Policy Updates | [Link](https://www.aapc.com/blog/93893-keep-up-with-2026-unitedhealthcare-policies-that-affect-reimbursement/) |
| AAO — Improper Billing Report | [Link](https://www.aao.org/practice-management/news-detail/first-coast-novitas-report-improper-billing-g2211) |
| CGM — G2211 Home Visit Boost 2026 | [Link](https://www.cgm.com/usa_en/articles/articles/g2211-update-medicare-home-visit-reimbursement-boost-in-2026.html) |
| Coding Intel — G2211 Survey Results | [Link](https://codingintel.com/g2211-survey-results) |
| Medwave — G2211 Avoid Denials | [Link](https://medwave.io/2026/03/g2211-avoid-denials-maximize-reimbursement/) |
| Medical Economics — 2026 Reimbursement | [Link](https://www.medicaleconomics.com/view/2026-medicare-reimbursement-inadequate-physician-payment-has-real-world-consequences-ama-says) |
| MedFeeSchedule — G2211 Rate | [Link](https://www.medfeeschedule.com/code/G2211) |
| Urology Times — 2024 Final Rule | [Link](https://www.urologytimes.com/view/2024-medicare-final-rule-here-comes-code-g2211) |
| Oncology News Central — UHC Policy Impact | [Link](https://www.oncologynewscentral.com/article/oncologist-reimbursement-hurt-by-unitedhealthcare-policy-change) |
| TechTarget — MA Denials Jump 56% | [Link](https://www.techtarget.com/revcyclemanagement/news/366600189/Medicare-Advantage-Denials-Jump-56-Commercial-Denials-20) |

---

*This document is for actuarial and billing compliance reference only. Always verify current policy details directly with UnitedHealthcare and CMS before making coverage determinations.*
