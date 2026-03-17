# G2211 Fraud Detection Logic Guide

> **Purpose**: Identify and flag fraudulent, wasteful, and abusive billing patterns for CPT G2211  
> **Scope**: Medicare FFS, Medicare Advantage (UHC), Medicaid (UHC Community Plan)  
> **For**: Actuarial teams, SIU (Special Investigations Unit), compliance auditors  
> **Last Updated**: March 2026

---

## Fraud Type Index

| ID | Fraud Type | Risk | Category |
|---|---|---|---|
| [FRD-G01](#frd-g01-standalone-g2211-billing) | Standalone G2211 Billing (No Base E/M) | CRITICAL | Coding Error / Fraud |
| [FRD-G02](#frd-g02-excluded-setting-billing) | Excluded Setting Billing (RHC, FQHC, Inpatient, ED) | CRITICAL | Setting Violation |
| [FRD-G03](#frd-g03-modifier-25-violation) | Modifier 25 + Non-Preventive Procedure | HIGH | CMS Edit Violation |
| [FRD-G04](#frd-g04-uhc-commercial-post-sept-2024) | UHC Commercial G2211 After Sept 2024 | HIGH | Payer Policy Violation |
| [FRD-G05](#frd-g05-uhc-medicaid-non-covered-state) | UHC Medicaid in Non-Covered State | HIGH | State Policy Violation |
| [FRD-G06](#frd-g06-wisconsin-ineligible-code-level) | Wisconsin — Ineligible E/M Level | MEDIUM | State-Specific Violation |
| [FRD-G07](#frd-g07-kansas-modifier-25-violation) | Kansas — G2211 With Modifier 25 | MEDIUM | State-Specific Violation |
| [FRD-G08](#frd-g08-abnormally-high-attachment-rate) | Abnormally High Attachment Rate (>50%) | HIGH | Over-Utilization |
| [FRD-G09](#frd-g09-no-longitudinal-relationship) | No Longitudinal Relationship (Single Visit Patients) | HIGH | Medical Necessity |
| [FRD-G10](#frd-g10-em-upcoding-with-g2211) | E/M Upcoding Coincident with G2211 Adoption | HIGH | Upcoding |
| [FRD-G11](#frd-g11-duplicate-g2211-same-day) | Duplicate G2211 on Same Day | CRITICAL | Duplicate Billing |
| [FRD-G12](#frd-g12-non-eligible-base-code) | G2211 Paired with Non-Eligible Base Code | CRITICAL | Coding Error |
| [FRD-G13](#frd-g13-ineligible-provider-type) | Ineligible Provider Type (Urgent Care, ER Moonlighting) | MEDIUM | Provider Eligibility |
| [FRD-G14](#frd-g14-sudden-volume-spike) | Sudden Volume Spike at Provider Level | HIGH | Aberrant Pattern |
| [FRD-G15](#frd-g15-g2211-on-every-visit) | G2211 on 100% of E/M Visits (Blanket Billing) | CRITICAL | Systematic Fraud |
| [FRD-G16](#frd-g16-home-visit-g2211-before-2026) | Home Visit G2211 Before Jan 1, 2026 | CRITICAL | Date Violation |
| [FRD-G17](#frd-g17-high-denial-rebill-pattern) | Denied G2211 Repeatedly Rebilled | MEDIUM | Abusive Rebilling |
| [FRD-G18](#frd-g18-g2211-with-global-surgery-period) | G2211 During Global Surgery Period | HIGH | Global Period Violation |

---

## FRD-G01: Standalone G2211 Billing

**Risk**: CRITICAL  
**Category**: Coding Error / Fraud

### Description

G2211 is an **add-on code only** — it can never be billed without an accompanying base E/M code on the same date of service by the same provider. Any standalone G2211 claim is either a coding error or intentional fraud.

### Detection Logic

Find G2211 claims where there is no matching base E/M code (99202-99215 or 99341-99350) on the same date, same patient, same provider.

```sql
SELECT
    g.claim_id,
    g.provider_npi,
    g.patient_id,
    g.date_of_service,
    g.allowed_amount,
    g.payer_type
FROM claims g
WHERE g.cpt_code = 'G2211'
AND NOT EXISTS (
    SELECT 1 FROM claims b
    WHERE b.provider_npi = g.provider_npi
      AND b.patient_id = g.patient_id
      AND b.date_of_service = g.date_of_service
      AND b.cpt_code IN (
          '99202','99203','99204','99205',
          '99211','99212','99213','99214','99215',
          '99341','99342','99344','99345',
          '99347','99348','99349','99350'
      )
)
ORDER BY g.provider_npi, g.date_of_service
```

### Threshold

**Zero tolerance** — any result is a flag.

### Action

- Deny claim / recoup payment
- Flag provider for education or audit

---

## FRD-G02: Excluded Setting Billing

**Risk**: CRITICAL  
**Category**: Setting Violation

### Description

G2211 is **not payable** in Rural Health Centers (RHCs), Federally Qualified Health Centers (FQHCs), hospital inpatient, emergency departments, or observation settings. Billing in these settings violates CMS rules.

### Detection Logic

```sql
SELECT
    c.claim_id,
    c.provider_npi,
    c.place_of_service,
    c.facility_type,
    c.date_of_service,
    c.allowed_amount
FROM claims c
WHERE c.cpt_code = 'G2211'
AND (
    c.place_of_service IN ('50','72')  -- FQHC (50), RHC (72)
    OR c.place_of_service IN ('21','23') -- Inpatient (21), ER (23)
    OR c.place_of_service = '22'  -- Outpatient Hospital (facility)
    OR c.facility_type IN ('RHC','FQHC')
    OR c.provider_taxonomy LIKE '%261Q%'  -- FQHC taxonomy
    OR c.provider_taxonomy LIKE '%291U%'  -- RHC taxonomy
)
ORDER BY c.provider_npi
```

### Place of Service Code Reference

| POS | Setting | G2211 Allowed? |
|---|---|---|
| 11 | Office | YES |
| 12 | Home | YES (2026+) |
| 02 | Telehealth (in patient home) | YES |
| 10 | Telehealth (in provider facility) | YES |
| 21 | Inpatient Hospital | NO |
| 22 | Outpatient Hospital | NO (facility) |
| 23 | Emergency Room | NO |
| 50 | FQHC | NO |
| 72 | RHC | NO |

### Threshold

**Zero tolerance** — any result is a flag.

---

## FRD-G03: Modifier 25 Violation

**Risk**: HIGH  
**Category**: CMS Edit Violation

### Description

G2211 is **not payable** when the base E/M code has modifier 25 appended, **unless** certain Part B preventive services are also performed on the same day (per CMS CR 13705). This is the most common improper billing pattern, flagged by First Coast and Novitas MACs.

### Detection Logic

```sql
-- Find G2211 claims where the base E/M has modifier 25
-- but NO qualifying preventive service exists on same day

WITH g2211_claims AS (
    SELECT claim_id, provider_npi, patient_id, date_of_service
    FROM claims
    WHERE cpt_code = 'G2211'
),
em_with_mod25 AS (
    SELECT provider_npi, patient_id, date_of_service
    FROM claims
    WHERE cpt_code IN ('99202','99203','99204','99205',
                        '99211','99212','99213','99214','99215',
                        '99341','99342','99344','99345',
                        '99347','99348','99349','99350')
    AND modifier LIKE '%25%'
),
preventive_services AS (
    SELECT provider_npi, patient_id, date_of_service
    FROM claims
    WHERE cpt_code IN (
        -- Vaccines & administration
        'G0008','G0009','G0010',
        '90460','90461','90471','90472','90473','90474','90480',
        '90653','90654','90655','90656','90657','90658','90660',
        '90670','90672','90674','90675','90676','90680','90681',
        '90682','90684','90732','90739','90740','90743',
        -- Cancer screening
        '71271','74263','G0103','G0104','G0105','G0121',
        '77063','77067',
        -- Lab screening
        '80061','80081','81528','82270','82947','82950','82951',
        '83036','86592','86593','86631','86632','86704','86706',
        '86780','87110','87270','87320','87340','87341',
        '87490','87491','87590','87591','87800','87810','87850',
        -- Imaging / bone density
        '76706','76977','77078','77080','77081','77085',
        -- AWV & preventive visits
        'G0402','G0438','G0439',
        -- Counseling
        'G0442','G0443','G0444','G0446','G0447',
        'G0108','G0109'
    )
)

SELECT
    g.claim_id,
    g.provider_npi,
    g.patient_id,
    g.date_of_service,
    'MODIFIER 25 WITHOUT PREVENTIVE SERVICE' AS fraud_flag
FROM g2211_claims g
INNER JOIN em_with_mod25 m
    ON g.provider_npi = m.provider_npi
    AND g.patient_id = m.patient_id
    AND g.date_of_service = m.date_of_service
LEFT JOIN preventive_services p
    ON g.provider_npi = p.provider_npi
    AND g.patient_id = p.patient_id
    AND g.date_of_service = p.date_of_service
WHERE p.provider_npi IS NULL  -- No preventive service found
ORDER BY g.provider_npi, g.date_of_service
```

### Threshold

**Zero tolerance** — this is a CMS edit violation. Any result = improper billing.

### Source

[AAO — Improper Billing of G2211](https://www.aao.org/practice-management/news-detail/first-coast-novitas-report-improper-billing-g2211)

---

## FRD-G04: UHC Commercial Post-Sept 2024

**Risk**: HIGH  
**Category**: Payer Policy Violation

### Description

UHC Commercial and Individual Exchange plans stopped covering G2211 effective September 1, 2024 (rebundled into E/M). Any G2211 claims billed to UHC Commercial after this date should be denied. If they were paid, they are recoupment targets.

### Detection Logic

```sql
SELECT
    c.claim_id,
    c.provider_npi,
    c.date_of_service,
    c.payer_type,
    c.plan_name,
    c.allowed_amount,
    c.paid_amount,
    CASE WHEN c.paid_amount > 0 THEN 'IMPROPERLY PAID' ELSE 'CORRECTLY DENIED' END AS status
FROM claims c
WHERE c.cpt_code = 'G2211'
AND c.payer_type = 'UHC_Commercial'
AND c.date_of_service >= '2024-09-01'
ORDER BY c.date_of_service
```

### Threshold

Any **paid** claim after Sept 1, 2024 = recoupment candidate.

### Source

[UHC Commercial Rebundling Policy](https://www.uhcprovider.com/content/dam/provider/docs/public/policies/comm-reimbursement/COMM-Rebundling-Policy.pdf)

---

## FRD-G05: UHC Medicaid Non-Covered State

**Risk**: HIGH  
**Category**: State Policy Violation

### Description

UHC Community Plan (Medicaid) only covers G2211 in Kansas, Maryland, Washington D.C., and Wisconsin (partial). All other UHC Medicaid states rebundle G2211. Paid claims in non-covered states are recoupment targets.

### Detection Logic

```sql
SELECT
    c.claim_id,
    c.provider_npi,
    c.provider_state,
    c.date_of_service,
    c.allowed_amount,
    c.paid_amount,
    CASE
        WHEN c.provider_state IN ('KS','MD','DC','WI') THEN 'COVERED STATE'
        ELSE 'NON-COVERED STATE - FLAG'
    END AS coverage_status
FROM claims c
WHERE c.cpt_code = 'G2211'
AND c.payer_type = 'UHC_Medicaid'
AND c.provider_state NOT IN ('KS','MD','DC','WI')
AND c.paid_amount > 0
ORDER BY c.provider_state, c.date_of_service
```

### Source

[UHC Community Plan Rebundling Policy R0056](https://www.uhcprovider.com/content/dam/provider/docs/public/policies/medicaid-comm-plan-reimbursement/UHCCP-Rebundling-Policy-R0056.pdf)

---

## FRD-G06: Wisconsin Ineligible Code Level

**Risk**: MEDIUM  
**Category**: State-Specific Violation

### Description

Wisconsin UHC Community Plan only covers G2211 as an add-on to **99205 and 99215** (highest-level new and established visits). G2211 billed with any other E/M code (99202-99204, 99211-99214) in Wisconsin Medicaid is non-covered.

### Detection Logic

```sql
SELECT
    g.claim_id,
    g.provider_npi,
    g.date_of_service,
    b.cpt_code AS base_em_code,
    g.allowed_amount
FROM claims g
INNER JOIN claims b
    ON g.provider_npi = b.provider_npi
    AND g.patient_id = b.patient_id
    AND g.date_of_service = b.date_of_service
    AND b.cpt_code IN ('99202','99203','99204','99211','99212','99213','99214')
WHERE g.cpt_code = 'G2211'
AND g.payer_type = 'UHC_Medicaid'
AND g.provider_state = 'WI'
AND g.paid_amount > 0
ORDER BY g.date_of_service
```

### Threshold

Any paid claim with base code other than 99205/99215 in Wisconsin = flag.

---

## FRD-G07: Kansas Modifier 25 Violation

**Risk**: MEDIUM  
**Category**: State-Specific Violation

### Description

Kansas UHC Medicaid covers G2211 **only when billed without modifier 25**. This is more restrictive than the CMS national policy (which allows mod-25 with preventive services). Any Kansas Medicaid G2211 claim where the base E/M has modifier 25 is non-covered.

### Detection Logic

```sql
SELECT
    g.claim_id,
    g.provider_npi,
    g.date_of_service,
    b.cpt_code AS base_em_code,
    b.modifier,
    g.allowed_amount
FROM claims g
INNER JOIN claims b
    ON g.provider_npi = b.provider_npi
    AND g.patient_id = b.patient_id
    AND g.date_of_service = b.date_of_service
    AND b.cpt_code IN ('99202','99203','99204','99205',
                        '99211','99212','99213','99214','99215')
WHERE g.cpt_code = 'G2211'
AND g.payer_type = 'UHC_Medicaid'
AND g.provider_state = 'KS'
AND b.modifier LIKE '%25%'
ORDER BY g.date_of_service
```

---

## FRD-G08: Abnormally High Attachment Rate

**Risk**: HIGH  
**Category**: Over-Utilization

### Description

National average G2211 attachment rate is **5.2%** of eligible E/M visits. Among billers, the average is **14.5%**. Providers with attachment rates above **40-50%** are statistical outliers and potential over-utilizers. Rates above **80%** strongly suggest blanket billing without clinical justification.

### Detection Logic

```sql
WITH provider_rates AS (
    SELECT
        provider_npi,
        provider_specialty,
        provider_state,
        COUNT(*) AS total_em_claims,
        SUM(CASE WHEN cpt_code = 'G2211' THEN 1 ELSE 0 END) AS g2211_claims,
        SUM(CASE WHEN cpt_code = 'G2211' THEN allowed_amount ELSE 0 END) AS g2211_spend,
        COUNT(DISTINCT patient_id) AS unique_patients
    FROM claims
    WHERE cpt_code IN ('99202','99203','99204','99205',
                        '99211','99212','99213','99214','99215',
                        '99341','99342','99344','99345',
                        '99347','99348','99349','99350','G2211')
    GROUP BY provider_npi, provider_specialty, provider_state
    HAVING COUNT(*) >= 30  -- minimum volume for statistical significance
)

SELECT
    provider_npi,
    provider_specialty,
    provider_state,
    total_em_claims,
    g2211_claims,
    ROUND(g2211_claims * 100.0 / total_em_claims, 1) AS attachment_rate_pct,
    g2211_spend,
    unique_patients,
    CASE
        WHEN g2211_claims * 1.0 / total_em_claims > 0.80 THEN 'CRITICAL - BLANKET BILLING'
        WHEN g2211_claims * 1.0 / total_em_claims > 0.50 THEN 'HIGH - AUDIT REQUIRED'
        WHEN g2211_claims * 1.0 / total_em_claims > 0.40 THEN 'ELEVATED - REVIEW'
        ELSE 'NORMAL'
    END AS risk_level
FROM provider_rates
WHERE g2211_claims * 1.0 / total_em_claims > 0.40
ORDER BY g2211_claims * 1.0 / total_em_claims DESC
```

### Thresholds

| Attachment Rate | Risk Level | Action |
|---|---|---|
| >80% | CRITICAL | Immediate audit — likely blanket billing |
| 50-80% | HIGH | Full chart review required |
| 40-50% | ELEVATED | Targeted review, compare to specialty peers |
| <40% | NORMAL | Routine monitoring |

### Benchmark

National average among billers is 14.5%. Primary care may reach 20-25% legitimately.

**Source**: [ECG — G2211 One Year Later](https://www.ecgmc.com/insights/blog/g2211-one-year-later-adoption-impact-and-what-comes-next)

---

## FRD-G09: No Longitudinal Relationship

**Risk**: HIGH  
**Category**: Medical Necessity

### Description

G2211 requires a **continuing longitudinal relationship** — the provider serves as the patient's ongoing focal point for care, or provides ongoing care for a complex condition. Patients seen **only once** by a provider cannot qualify for G2211 because no longitudinal relationship exists.

### Detection Logic

```sql
WITH patient_visit_counts AS (
    SELECT
        provider_npi,
        patient_id,
        COUNT(DISTINCT date_of_service) AS visit_count,
        MIN(date_of_service) AS first_visit,
        MAX(date_of_service) AS last_visit,
        SUM(CASE WHEN cpt_code = 'G2211' THEN 1 ELSE 0 END) AS g2211_count
    FROM claims
    WHERE cpt_code IN ('99202','99203','99204','99205',
                        '99211','99212','99213','99214','99215',
                        '99341','99342','99344','99345',
                        '99347','99348','99349','99350','G2211')
    GROUP BY provider_npi, patient_id
)

SELECT
    provider_npi,
    patient_id,
    visit_count,
    first_visit,
    last_visit,
    g2211_count,
    'SINGLE VISIT - NO LONGITUDINAL RELATIONSHIP' AS fraud_flag
FROM patient_visit_counts
WHERE visit_count = 1
AND g2211_count > 0
ORDER BY provider_npi
```

### Provider-Level Summary

```sql
-- Providers billing G2211 predominantly for single-visit patients
WITH single_visit_g2211 AS (
    SELECT
        provider_npi,
        patient_id,
        COUNT(DISTINCT date_of_service) AS visits
    FROM claims
    WHERE cpt_code IN ('99202','99203','99204','99205',
                        '99211','99212','99213','99214','99215','G2211')
    GROUP BY provider_npi, patient_id
)

SELECT
    s.provider_npi,
    COUNT(*) AS total_g2211_patients,
    SUM(CASE WHEN s.visits = 1 THEN 1 ELSE 0 END) AS single_visit_patients,
    ROUND(SUM(CASE WHEN s.visits = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1)
        AS pct_single_visit
FROM single_visit_g2211 s
INNER JOIN claims c ON s.provider_npi = c.provider_npi
    AND s.patient_id = c.patient_id
    AND c.cpt_code = 'G2211'
GROUP BY s.provider_npi
HAVING COUNT(*) >= 10
AND SUM(CASE WHEN s.visits = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) > 0.50
ORDER BY pct_single_visit DESC
```

### Threshold

If >50% of a provider's G2211 patients are single-visit patients, flag for review.

---

## FRD-G10: E/M Upcoding With G2211

**Risk**: HIGH  
**Category**: Upcoding

### Description

When providers adopt G2211, some simultaneously **upcode their E/M level** (e.g., shifting from 99213 to 99214, or 99214 to 99215) to maximize total reimbursement. Compare a provider's E/M level distribution **before** and **after** they started billing G2211.

### Detection Logic

```sql
WITH provider_g2211_start AS (
    SELECT provider_npi, MIN(date_of_service) AS g2211_start_date
    FROM claims WHERE cpt_code = 'G2211'
    GROUP BY provider_npi
),
em_distribution AS (
    SELECT
        c.provider_npi,
        CASE
            WHEN c.date_of_service < g.g2211_start_date THEN 'BEFORE_G2211'
            ELSE 'AFTER_G2211'
        END AS period,
        c.cpt_code,
        COUNT(*) AS claim_count
    FROM claims c
    INNER JOIN provider_g2211_start g ON c.provider_npi = g.provider_npi
    WHERE c.cpt_code IN ('99211','99212','99213','99214','99215')
    GROUP BY c.provider_npi, period, c.cpt_code
)

SELECT
    b.provider_npi,
    b.cpt_code,
    b.claim_count AS before_count,
    a.claim_count AS after_count,
    ROUND((a.claim_count * 1.0 / NULLIF(b.claim_count, 0) - 1) * 100, 1) AS pct_change
FROM em_distribution b
INNER JOIN em_distribution a
    ON b.provider_npi = a.provider_npi
    AND b.cpt_code = a.cpt_code
WHERE b.period = 'BEFORE_G2211'
AND a.period = 'AFTER_G2211'
AND a.cpt_code IN ('99214','99215')  -- Focus on high-level codes
AND a.claim_count * 1.0 / NULLIF(b.claim_count, 0) > 1.30  -- >30% increase
ORDER BY pct_change DESC
```

### Threshold

| Shift | Risk |
|---|---|
| >30% increase in 99214/99215 after G2211 adoption | ELEVATED — review |
| >50% increase | HIGH — probable upcoding |
| Average E/M level jumps by >0.5 units | HIGH — systematic shift |

---

## FRD-G11: Duplicate G2211 Same Day

**Risk**: CRITICAL  
**Category**: Duplicate Billing

### Description

G2211 should only be billed **once per encounter** (per patient, per provider, per date). Multiple G2211 lines on the same day = duplicate billing.

### Detection Logic

```sql
SELECT
    provider_npi,
    patient_id,
    date_of_service,
    COUNT(*) AS g2211_count,
    SUM(allowed_amount) AS total_g2211_allowed
FROM claims
WHERE cpt_code = 'G2211'
GROUP BY provider_npi, patient_id, date_of_service
HAVING COUNT(*) > 1
ORDER BY g2211_count DESC
```

### Threshold

**Zero tolerance** — any duplicate = flag and recoup.

---

## FRD-G12: Non-Eligible Base Code

**Risk**: CRITICAL  
**Category**: Coding Error

### Description

G2211 can only be paired with specific E/M base codes. Any pairing with inpatient, ED, consultation, nursing facility, or other non-eligible codes is improper.

### Detection Logic

```sql
-- Find G2211 claims where the ONLY E/M code on that date is non-eligible
WITH g2211_dates AS (
    SELECT DISTINCT provider_npi, patient_id, date_of_service
    FROM claims WHERE cpt_code = 'G2211'
),
eligible_em AS (
    SELECT provider_npi, patient_id, date_of_service
    FROM claims
    WHERE cpt_code IN (
        '99202','99203','99204','99205',
        '99211','99212','99213','99214','99215',
        '99341','99342','99344','99345',
        '99347','99348','99349','99350'
    )
),
non_eligible_em AS (
    SELECT provider_npi, patient_id, date_of_service, cpt_code
    FROM claims
    WHERE cpt_code IN (
        -- Inpatient
        '99221','99222','99223','99231','99232','99233',
        '99234','99235','99236','99238','99239',
        -- ED
        '99281','99282','99283','99284','99285',
        -- Observation
        '99217','99218','99219','99220','99224','99225','99226',
        -- Consultation
        '99241','99242','99243','99244','99245',
        -- Nursing Facility
        '99304','99305','99306','99307','99308','99309','99310',
        -- Critical Care
        '99291','99292'
    )
)

SELECT
    g.provider_npi,
    g.patient_id,
    g.date_of_service,
    n.cpt_code AS paired_non_eligible_code,
    'G2211 WITH NON-ELIGIBLE BASE CODE' AS fraud_flag
FROM g2211_dates g
LEFT JOIN eligible_em e
    ON g.provider_npi = e.provider_npi
    AND g.patient_id = e.patient_id
    AND g.date_of_service = e.date_of_service
INNER JOIN non_eligible_em n
    ON g.provider_npi = n.provider_npi
    AND g.patient_id = n.patient_id
    AND g.date_of_service = n.date_of_service
WHERE e.provider_npi IS NULL  -- No eligible E/M exists
ORDER BY g.provider_npi
```

---

## FRD-G13: Ineligible Provider Type

**Risk**: MEDIUM  
**Category**: Provider Eligibility

### Description

G2211 is designed for providers with **longitudinal patient relationships**. Certain provider types rarely maintain ongoing relationships: urgent care providers, emergency medicine physicians moonlighting in offices, locum tenens, and hospitalists. High G2211 volume from these provider types is suspicious.

### Detection Logic

```sql
SELECT
    provider_npi,
    provider_specialty,
    provider_state,
    COUNT(*) FILTER (WHERE cpt_code = 'G2211') AS g2211_claims,
    COUNT(*) AS total_claims,
    ROUND(COUNT(*) FILTER (WHERE cpt_code = 'G2211') * 100.0 / COUNT(*), 1) AS attach_rate
FROM claims
WHERE provider_specialty IN (
    'Urgent Care',
    'Emergency Medicine',
    'Hospitalist',
    'Locum Tenens',
    'Critical Care Medicine'
)
AND cpt_code IN ('99202','99203','99204','99205',
                  '99211','99212','99213','99214','99215','G2211')
GROUP BY provider_npi, provider_specialty, provider_state
HAVING COUNT(*) FILTER (WHERE cpt_code = 'G2211') > 5
ORDER BY attach_rate DESC
```

### Threshold

Any urgent care or ER provider billing G2211 at >5% rate warrants review.

---

## FRD-G14: Sudden Volume Spike

**Risk**: HIGH  
**Category**: Aberrant Pattern

### Description

A provider's G2211 volume suddenly jumps (e.g., from 0 to 50+ claims in a month) without a corresponding increase in total E/M volume. This suggests they received billing training or installed EHR prompts and may be applying G2211 retroactively or indiscriminately.

### Detection Logic

```sql
WITH monthly_volume AS (
    SELECT
        provider_npi,
        DATE_TRUNC('month', date_of_service) AS month,
        SUM(CASE WHEN cpt_code = 'G2211' THEN 1 ELSE 0 END) AS g2211_count,
        COUNT(*) AS total_em
    FROM claims
    WHERE cpt_code IN ('99202','99203','99204','99205',
                        '99211','99212','99213','99214','99215','G2211')
    GROUP BY provider_npi, DATE_TRUNC('month', date_of_service)
),
with_lag AS (
    SELECT
        provider_npi,
        month,
        g2211_count,
        total_em,
        LAG(g2211_count) OVER (PARTITION BY provider_npi ORDER BY month) AS prev_g2211,
        LAG(total_em) OVER (PARTITION BY provider_npi ORDER BY month) AS prev_total
    FROM monthly_volume
)

SELECT
    provider_npi,
    month,
    prev_g2211,
    g2211_count,
    g2211_count - COALESCE(prev_g2211, 0) AS g2211_increase,
    total_em,
    'SUDDEN SPIKE' AS flag
FROM with_lag
WHERE g2211_count > 20
AND (prev_g2211 IS NULL OR prev_g2211 = 0)
ORDER BY g2211_count DESC
```

### Threshold

Going from 0 to >20 G2211 claims in a single month = flag for review.

---

## FRD-G15: G2211 on 100% of E/M Visits

**Risk**: CRITICAL  
**Category**: Systematic Fraud

### Description

No provider legitimately has 100% of their patients qualifying for G2211. A 100% attachment rate means the provider is billing G2211 on every single E/M visit without clinical differentiation — this is blanket billing and strong evidence of systematic abuse.

### Detection Logic

```sql
WITH provider_stats AS (
    SELECT
        provider_npi,
        provider_specialty,
        provider_state,
        COUNT(DISTINCT date_of_service || patient_id) AS total_encounters,
        COUNT(DISTINCT CASE WHEN cpt_code = 'G2211'
              THEN date_of_service || patient_id END) AS g2211_encounters
    FROM claims
    WHERE cpt_code IN ('99202','99203','99204','99205',
                        '99211','99212','99213','99214','99215','G2211')
    GROUP BY provider_npi, provider_specialty, provider_state
    HAVING COUNT(DISTINCT date_of_service || patient_id) >= 50
)

SELECT *,
    ROUND(g2211_encounters * 100.0 / total_encounters, 1) AS attach_rate_pct
FROM provider_stats
WHERE g2211_encounters * 1.0 / total_encounters >= 0.95
ORDER BY total_encounters DESC
```

### Threshold

>=95% attachment rate with >=50 encounters = immediate audit referral.

---

## FRD-G16: Home Visit G2211 Before 2026

**Risk**: CRITICAL  
**Category**: Date Violation

### Description

CMS only expanded G2211 to home/residence E/M codes (99341-99350) effective **January 1, 2026**. Any G2211 billed with a home visit code before that date is non-covered.

### Detection Logic

```sql
SELECT
    g.claim_id,
    g.provider_npi,
    g.date_of_service,
    b.cpt_code AS home_visit_code,
    g.allowed_amount
FROM claims g
INNER JOIN claims b
    ON g.provider_npi = b.provider_npi
    AND g.patient_id = b.patient_id
    AND g.date_of_service = b.date_of_service
    AND b.cpt_code IN ('99341','99342','99344','99345',
                        '99347','99348','99349','99350')
WHERE g.cpt_code = 'G2211'
AND g.date_of_service < '2026-01-01'
ORDER BY g.date_of_service
```

### Threshold

**Zero tolerance** — any result before Jan 1, 2026 is a flag.

---

## FRD-G17: High Denial Rebill Pattern

**Risk**: MEDIUM  
**Category**: Abusive Rebilling

### Description

Provider submits G2211, gets denied, then resubmits the same claim repeatedly hoping for payment. This is especially common for UHC Commercial (which rebundles G2211) and non-covered Medicaid states.

### Detection Logic

```sql
SELECT
    provider_npi,
    patient_id,
    date_of_service,
    COUNT(*) AS submission_count,
    SUM(CASE WHEN denied THEN 1 ELSE 0 END) AS denial_count,
    MAX(CASE WHEN paid_amount > 0 THEN 'PAID' ELSE 'ALL DENIED' END) AS final_status
FROM claims
WHERE cpt_code = 'G2211'
GROUP BY provider_npi, patient_id, date_of_service
HAVING COUNT(*) >= 3
ORDER BY submission_count DESC
```

### Threshold

3+ submissions for the same G2211 service = abusive rebilling pattern.

---

## FRD-G18: G2211 During Global Surgery Period

**Risk**: HIGH  
**Category**: Global Period Violation

### Description

When a provider performs a surgical procedure with a 10-day or 90-day global period, post-operative E/M visits are included in the surgical payment. G2211 billed during the global period (without modifier 24 for unrelated E/M) may be improper.

### Detection Logic

```sql
WITH surgical_claims AS (
    SELECT
        provider_npi,
        patient_id,
        date_of_service AS surgery_date,
        cpt_code AS surgery_code,
        global_days
    FROM claims
    WHERE global_days IN ('010','090')  -- 10-day or 90-day global
),
g2211_claims AS (
    SELECT claim_id, provider_npi, patient_id, date_of_service
    FROM claims WHERE cpt_code = 'G2211'
)

SELECT
    g.claim_id,
    g.provider_npi,
    g.patient_id,
    s.surgery_date,
    s.surgery_code,
    s.global_days,
    g.date_of_service AS g2211_date,
    DATEDIFF(g.date_of_service, s.surgery_date) AS days_post_surgery,
    'G2211 DURING GLOBAL PERIOD' AS fraud_flag
FROM g2211_claims g
INNER JOIN surgical_claims s
    ON g.provider_npi = s.provider_npi
    AND g.patient_id = s.patient_id
    AND g.date_of_service > s.surgery_date
    AND g.date_of_service <= DATEADD(DAY, CAST(s.global_days AS INT), s.surgery_date)
ORDER BY g.provider_npi, s.surgery_date
```

---

## Composite Risk Score

Combine all fraud flags into a single provider risk score:

```sql
WITH fraud_flags AS (
    -- Union all fraud detection queries above, each producing:
    -- provider_npi, fraud_type_id, claim_count, severity_weight

    SELECT provider_npi, 'FRD-G01' AS fraud_type, COUNT(*) AS flag_count, 10 AS weight
    FROM frd_g01_results GROUP BY provider_npi

    UNION ALL

    SELECT provider_npi, 'FRD-G08', 1, 
        CASE WHEN attach_rate > 0.80 THEN 10
             WHEN attach_rate > 0.50 THEN 7
             WHEN attach_rate > 0.40 THEN 4 END
    FROM frd_g08_results

    -- ... add all other fraud types ...
)

SELECT
    provider_npi,
    COUNT(DISTINCT fraud_type) AS distinct_fraud_types,
    SUM(flag_count) AS total_flagged_claims,
    SUM(flag_count * weight) AS composite_risk_score,
    CASE
        WHEN SUM(flag_count * weight) >= 50 THEN 'CRITICAL - IMMEDIATE AUDIT'
        WHEN SUM(flag_count * weight) >= 25 THEN 'HIGH - PRIORITY REVIEW'
        WHEN SUM(flag_count * weight) >= 10 THEN 'ELEVATED - SCHEDULED REVIEW'
        ELSE 'LOW - ROUTINE MONITORING'
    END AS risk_tier
FROM fraud_flags
GROUP BY provider_npi
ORDER BY composite_risk_score DESC
```

### Severity Weights

| Fraud Type | Weight | Rationale |
|---|---|---|
| FRD-G01 (Standalone) | 10 | Clear coding error or fraud |
| FRD-G02 (Excluded setting) | 10 | Definitive CMS rule violation |
| FRD-G11 (Duplicate) | 10 | Obvious duplicate billing |
| FRD-G15 (100% blanket) | 10 | Systematic abuse |
| FRD-G16 (Pre-2026 home) | 10 | Date-based violation |
| FRD-G03 (Mod 25 violation) | 8 | CMS edit violation |
| FRD-G08 (High attach rate) | 4-10 | Tiered by severity |
| FRD-G09 (No relationship) | 7 | Medical necessity concern |
| FRD-G10 (Upcoding) | 7 | Revenue manipulation |
| FRD-G12 (Wrong base code) | 8 | Definitive code violation |
| FRD-G18 (Global period) | 7 | Post-surgical billing abuse |
| FRD-G04 (UHC Commercial) | 6 | Payer policy violation |
| FRD-G05 (Medicaid state) | 6 | State policy violation |
| FRD-G14 (Volume spike) | 5 | Requires investigation |
| FRD-G06 (Wisconsin level) | 4 | State-specific |
| FRD-G07 (Kansas mod 25) | 4 | State-specific |
| FRD-G13 (Provider type) | 3 | Circumstantial |
| FRD-G17 (Rebilling) | 3 | Abusive but may be admin error |

---

## Sources

| Reference | URL |
|---|---|
| CMS G2211 FAQ | [PDF](https://www.cms.gov/files/document/hcpcs-g2211-faq.pdf) |
| CMS MM13473 — How to Use G2211 | [PDF](https://www.cms.gov/files/document/mm13473-how-use-office-and-outpatient-evaluation-and-management-visit-complexity-add-code-g2211.pdf) |
| CMS CR 13705 — Preventive Services List | [Link](https://www.hhs.gov/guidance/document/allow-payment-healthcare-common-procedure-coding-system-hcpcs-code-g2211-when-certain-0) |
| UHC MA Add-on Codes Policy 2026R9007B | [PDF](https://www.uhcprovider.com/content/dam/provider/docs/public/policies/medadv-reimbursement/MEDADV-Add-On-Codes-Policy.pdf) |
| UHC Commercial Rebundling Policy | [PDF](https://www.uhcprovider.com/content/dam/provider/docs/public/policies/comm-reimbursement/COMM-Rebundling-Policy.pdf) |
| UHC Community Plan Rebundling R0056 | [PDF](https://www.uhcprovider.com/content/dam/provider/docs/public/policies/medicaid-comm-plan-reimbursement/UHCCP-Rebundling-Policy-R0056.pdf) |
| AAO — Improper Billing Report | [Link](https://www.aao.org/practice-management/news-detail/first-coast-novitas-report-improper-billing-g2211) |
| IPMS — NGS Denials for G2211 | [Link](https://ipmscorp.com/national-government-services-denials-for-hcpcs-g2211/) |
| ECG — G2211 One Year Later | [Link](https://www.ecgmc.com/insights/blog/g2211-one-year-later-adoption-impact-and-what-comes-next) |
| AAFP — G2211 Update Jan 2025 | [Link](https://www.aafp.org/pubs/fpm/issues/2025/0100/g2211-update.html) |
| AAPC — When Can I Bill G2211 | [Link](https://www.aapc.com/blog/92654-when-can-i-bill-g2211/) |

---

*This fraud detection guide is for actuarial, SIU, and compliance use. SQL queries assume a standardized claims schema — adapt column names and table references to your Databricks environment.*
