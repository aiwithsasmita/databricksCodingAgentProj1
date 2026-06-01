# Data Dictionary — FL Medical Spend & CPT Cost Driver POC

This document defines every data field required to run both dashboards. If you are plugging in real claims data, map your columns to these field names.

---

## Dashboard 1: Florida Medical Spend Dashboard (port 8050)

### Required Data: Provider-Level Monthly Claims Summary

One row per **month x provider x clinical cluster** combination.

| # | Field | Type | Required | Description | Example | Source in Claims System |
|---|-------|------|----------|-------------|---------|------------------------|
| 1 | `month` | date | Yes | First day of the service month | 2024-01-01 | Derived from claim service date |
| 2 | `year` | int | Yes | Calendar year | 2024 | Derived from `month` |
| 3 | `quarter` | str | Yes | Calendar quarter | Q1, Q2, Q3, Q4 | Derived from `month` |
| 4 | `provider_name` | str | Yes | Hospital or clinic name | AdventHealth Orlando | Provider master / TIN file |
| 5 | `npi` | str | Yes | National Provider Identifier (10-digit) | 1234567890 | NPPES registry / claims header |
| 6 | `provider_type` | str | Yes | Facility classification | Hospital System, Academic Medical Center, Specialty Center, Specialty Clinic | Provider master file |
| 7 | `region` | str | Yes | Geographic region within state | Central, Southeast, West, etc. | Derived from county or zip code |
| 8 | `county` | str | Yes | County name | Orange, Miami-Dade | Provider address or member address |
| 9 | `bed_count` | int | Yes | Number of licensed/certified beds (0 for outpatient clinics) | 1368 | CMS Provider of Services file or state licensure |
| 10 | `clinical_cluster` | str | Yes | Disease/service category grouping | Oncology / Cancer, Cardiovascular, Dermatology / Skin | Derived from ICD-10 diagnosis codes on claims |
| 11 | `member_count` | int | Yes | Unique members with claims in this group for this month | 126 | Count distinct member IDs |
| 12 | `claim_count` | int | Yes | Total claim lines in this group for this month | 315 | Count of claim line records |
| 13 | `total_paid` | float | Yes | Plan paid amount (dollars) — the core cost metric | 450000.00 | Sum of paid amounts on claims |
| 14 | `allowed_amount` | float | Yes | Contractually allowed amount before member cost share | 540000.00 | Sum of allowed amounts on claims |
| 15 | `billed_amount` | float | Yes | Provider-submitted charges (always highest) | 1080000.00 | Sum of billed/charged amounts |
| 16 | `member_cost_share` | float | Yes | Total copays + deductibles + coinsurance | 72000.00 | Sum of member responsibility fields |
| 17 | `pmpm` | float | Derived | Per Member Per Month cost = `total_paid / member_count` | 3571.43 | Calculated |
| 18 | `high_cost_claimants` | int | Optional | Members exceeding stop-loss threshold (e.g., >$100K/year) | 3 | Count members above threshold |
| 19 | `high_cost_amount` | float | Optional | Total paid for high-cost members only | 85000.00 | Sum paid for flagged members |
| 20 | `admits_per_1000` | float | Optional | Inpatient admissions per 1,000 members per month | 14.5 | (Admit count / member_count) x 1000 |
| 21 | `er_visits_per_1000` | float | Optional | ER visits per 1,000 members per month | 42.3 | (ER visit count / member_count) x 1000 |
| 22 | `readmission_rate` | float | Optional | 30-day readmission rate (0.0 to 1.0) | 0.12 | Readmits within 30 days / total admits |
| 23 | `avg_length_of_stay` | float | Optional | Average inpatient days per admission | 4.5 | Sum of LOS / admit count |
| 24 | `avg_risk_score` | float | Optional | HCC risk adjustment score (1.0 = average) | 1.65 | CMS HCC model output or plan's risk scoring |

### Clinical Cluster Definitions

The `clinical_cluster` field maps diagnosis codes to 12 disease categories. Here is how to derive it from ICD-10 codes:

| Cluster | ICD-10 Code Ranges (Primary) | Description |
|---------|------------------------------|-------------|
| Oncology / Cancer | C00-C96, D00-D09 | All malignant neoplasms and carcinoma in situ |
| Dermatology / Skin | L00-L99 | Diseases of the skin and subcutaneous tissue |
| Cardiovascular | I00-I99 | Diseases of the circulatory system |
| Orthopedic / MSK | M00-M99 | Diseases of the musculoskeletal system |
| Neurological | G00-G99 | Diseases of the nervous system |
| Respiratory / Pulmonary | J00-J99 | Diseases of the respiratory system |
| Gastrointestinal | K00-K95 | Diseases of the digestive system |
| Behavioral Health | F01-F99 | Mental, behavioral, and neurodevelopmental disorders |
| Maternity / OB-GYN | O00-O9A, Z33-Z39 | Pregnancy, childbirth, and puerperium |
| Renal / Nephrology | N00-N29, Z49 (dialysis) | Diseases of the kidney and ureter |
| Endocrine / Diabetes | E08-E13, E00-E89 | Endocrine, nutritional, and metabolic diseases |
| Autoimmune / Rheumatology | M05-M06, M30-M36, L40 | Rheumatoid conditions, systemic connective tissue |

---

## Dashboard 2: CPT Cost Driver & Early Warning (port 8051)

### Required Data: CPT-Level Monthly Claims Summary

One row per **month x state x plan_type x CPT code** combination.

| # | Field | Type | Required | Description | Example | Source in Claims System |
|---|-------|------|----------|-------------|---------|------------------------|
| 1 | `month` | date | Yes | First day of the service month | 2024-01-01 | Derived from claim service date |
| 2 | `year` | int | Yes | Calendar year | 2024 | Derived from `month` |
| 3 | `quarter` | str | Yes | Calendar quarter | Q1 | Derived from `month` |
| 4 | `state` | str | Yes | State abbreviation (2-letter) | FL, CA, TX, NY | Member or provider state |
| 5 | `plan_type` | str | Yes | Insurance program | Medicare, Medicaid, Dual | Enrollment/eligibility system |
| 6 | `member_months` | int | Yes | Total member-months in this group (denominator for PMPM) | 408375 | Sum of enrolled member-months |
| 7 | `cpt_code` | str | Yes | CPT/HCPCS procedure code | 99213, 27447, J9271 | Claim line procedure code field |
| 8 | `cpt_description` | str | Yes | Short description of the procedure | Office visit estab low | CPT master file or CMS HCPCS |
| 9 | `category` | str | Yes | Service category | E&M, Surgery, Radiology, Lab, Medicine, Anesthesia, DME/Supply, Behavioral Health | Derived from CPT code range (see mapping below) |
| 10 | `subcategory` | str | Yes | More specific grouping | Office Visit, Cardiac, MRI, Psychotherapy | Derived from CPT code range |
| 11 | `rvu_work` | float | Recommended | CMS Work RVU for this code | 1.30 | CMS PFS Relative Value File |
| 12 | `rvu_total` | float | Recommended | CMS Total RVU (Work + PE + MP) | 2.73 | CMS PFS Relative Value File |
| 13 | `national_benchmark` | float | Recommended | CMS national average allowed amount ($) | 90.87 | CMS PFS National Payment File |
| 14 | `place_of_service` | str | Recommended | Setting where service was rendered | Office, Inpatient, ER, ASC, Telehealth, Other | Claim line POS code (mapped) |
| 15 | `total_units` | int | Yes | Total service units billed | 5420 | Sum of claim line units |
| 16 | `unit_cost` | float | Derived | Average allowed per unit = `allowed_amount / total_units` | 90.50 | Calculated |
| 17 | `allowed_amount` | float | Yes | Total contractually allowed amount ($) | 490510.00 | Sum of allowed amounts |
| 18 | `billed_amount` | float | Yes | Total provider-submitted charges ($) | 1127000.00 | Sum of billed amounts |
| 19 | `paid_amount` | float | Yes | Total plan paid amount ($) | 416933.50 | Sum of paid amounts |
| 20 | `member_cost_share` | float | Yes | Total member out-of-pocket ($) | 73576.50 | Sum of copay + deductible + coinsurance |
| 21 | `utilization_per_1000` | float | Derived | Services per 1,000 members = `(total_units / member_months) x 1000` | 13.28 | Calculated |
| 22 | `pmpm` | float | Derived | Per Member Per Month = `allowed_amount / member_months` | 1.2013 | Calculated |

### CPT Category Mapping

The `category` field groups CPT codes into 8 service categories:

| Category | CPT Code Ranges | Examples |
|----------|----------------|----------|
| E&M | 99201-99499, G0402, G0438, G0439, G2211 | Office visits, hospital visits, ER visits, preventive, telehealth, care management |
| Surgery | 10000-69999 | Orthopedic (TKA, THA), Cardiac (CABG, PCI), General (colonoscopy, cholecystectomy), Ophthalmology (cataract), Urology, Vascular |
| Radiology | 70000-79999 | X-ray, CT, MRI, Ultrasound, Nuclear medicine, Radiation therapy, Mammography |
| Lab | 80000-89999, 36415 | Chemistry panels (CMP, BMP), CBC, pathology, molecular/genetics |
| Medicine | 90000-99199 (excl E&M), J-codes | Cardiology diagnostics (echo, cath), pulmonary function, dialysis, infusions/injections, physical therapy, ophthalmology diagnostics, allergy, vaccines |
| Anesthesia | 00100-01999, 62000-64999 | General anesthesia, regional, pain management (epidurals, facet injections, RFA) |
| DME/Supply | A0000-A9999, E0000-E9999, L0000-L9999 | Orthotics, CPAP, oxygen, hospital beds, diabetic supplies |
| Behavioral Health | 90785-90899, H0001-H0050, 96130-96139 | Psychotherapy, psychiatric evaluation, substance abuse, neuropsych testing |

### Place of Service Mapping

Map the CMS Place of Service (POS) code from claims to these categories:

| POS Code | Category | Description |
|----------|----------|-------------|
| 11 | Office | Physician office |
| 21, 22, 23 | Inpatient | Inpatient hospital, outpatient hospital, ER |
| 24 | ASC | Ambulatory Surgical Center |
| 02 | Telehealth | Telehealth (added during COVID) |
| All others | Other | SNF, Home, Hospice, etc. |

---

## Reference Data (Enrich Your Claims)

These reference datasets can be joined to your claims to add context:

### Provider Reference

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `npi` | str | National Provider Identifier | NPPES NPI Registry (download from CMS) |
| `provider_name` | str | Legal business name | NPPES |
| `provider_state` | str | State where provider is located | NPPES |
| `provider_type` | str | Taxonomy classification | NPPES taxonomy code → category |
| `bed_count` | int | Certified bed count | CMS Provider of Services File (use `download_bed_counts.py`) |
| `network_status` | str | In-Network / Out-of-Network | Your plan's provider network file |
| `health_system` | str | Parent organization name | CMS POS file `MLT_FAC_ORG_NAME` column |

### Member Enrollment Reference

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `member_id` | str | Unique member identifier | Enrollment system |
| `enrollment_month` | date | Month member was active | Eligibility file |
| `plan_type` | str | Medicare / Medicaid / Dual / Commercial | Enrollment system |
| `state` | str | Member's state of residence | Enrollment address |
| `county` | str | Member's county | Enrollment address |
| `age_band` | str | Age group (0-17, 18-34, 35-44, 45-54, 55-64, 65+) | Derived from DOB |
| `gender` | str | M / F | Enrollment demographics |
| `risk_score` | float | HCC risk adjustment score (1.0 = avg) | CMS HCC model or plan's risk engine |

### CMS Fee Schedule Reference

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `cpt_code` | str | CPT/HCPCS code | CMS PFS Indicators file |
| `description` | str | Short procedure description | CMS PFS `sdesc` column |
| `rvu_work` | float | Work Relative Value Unit | CMS PFS Indicators file |
| `rvu_total` | float | Total RVU (Work + PE + MP) | CMS PFS `full_nfac_total` column |
| `national_avg_allowed` | float | National payment = RVU x Conversion Factor | Calculated from CMS PFS |
| `state_adjusted_allowed` | float | State payment = RVU x GPCI x CF | Use `CMS_FeeSchedule_Scraper` to compute |
| `conversion_factor` | float | CMS annual conversion factor | CMS PFS Final Rule (2023: $33.89, 2024: $33.29, 2025: $32.35) |

---

## How to Prepare Your Data

### Step 1: Extract from Claims Warehouse

```sql
-- Example SQL for Dashboard 1 (Provider-Level)
SELECT
    DATE_TRUNC('month', service_date)          AS month,
    YEAR(service_date)                         AS year,
    provider_name,
    provider_npi                               AS npi,
    provider_type,
    provider_region                            AS region,
    provider_county                            AS county,
    provider_bed_count                         AS bed_count,
    disease_cluster                            AS clinical_cluster,
    COUNT(DISTINCT member_id)                  AS member_count,
    COUNT(*)                                   AS claim_count,
    SUM(paid_amount)                           AS total_paid,
    SUM(allowed_amount)                        AS allowed_amount,
    SUM(billed_amount)                         AS billed_amount,
    SUM(member_responsibility)                 AS member_cost_share
FROM claims_detail
WHERE service_date BETWEEN '2023-01-01' AND '2025-12-31'
  AND state = 'FL'
GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9
```

```sql
-- Example SQL for Dashboard 2 (CPT-Level)
SELECT
    DATE_TRUNC('month', service_date)          AS month,
    YEAR(service_date)                         AS year,
    member_state                               AS state,
    plan_type,
    SUM(member_months)                         AS member_months,
    procedure_code                             AS cpt_code,
    procedure_description                      AS cpt_description,
    service_category                           AS category,
    service_subcategory                        AS subcategory,
    SUM(units)                                 AS total_units,
    SUM(allowed_amount)                        AS allowed_amount,
    SUM(billed_amount)                         AS billed_amount,
    SUM(paid_amount)                           AS paid_amount,
    SUM(member_responsibility)                 AS member_cost_share
FROM claims_detail c
JOIN member_enrollment e ON c.member_id = e.member_id
WHERE service_date BETWEEN '2023-01-01' AND '2025-12-31'
GROUP BY 1, 2, 3, 4, 6, 7, 8, 9
```

### Step 2: Add Derived Fields

```python
df["pmpm"] = df["allowed_amount"] / df["member_months"]
df["unit_cost"] = df["allowed_amount"] / df["total_units"]
df["utilization_per_1000"] = df["total_units"] / df["member_months"] * 1000
df["quarter"] = "Q" + ((df["month"].dt.month - 1) // 3 + 1).astype(str)
```

### Step 3: Add CMS Benchmarks (Optional but Recommended)

```python
from CMS_FeeSchedule_Scraper.cms_pfs_scraper import CMSFeeSchedule

pfs = CMSFeeSchedule()
pfs.download_all()

# For each unique CPT in your data
for cpt in df["cpt_code"].unique():
    result = pfs.lookup(cpt, year=2024, state="FL")
    df.loc[df["cpt_code"] == cpt, "rvu_work"] = result.get("rvu_work", 0)
    df.loc[df["cpt_code"] == cpt, "rvu_total"] = result.get("rvu_total_nonfacility", 0)
    df.loc[df["cpt_code"] == cpt, "national_benchmark"] = result.get("national_payment_nonfacility", 0)
```

### Step 4: Load into Dashboard

Edit `cpt_analysis/column_config.py`:

```python
DATA_PATH = r"D:\data\my_claims_cpt_level.csv"

COLUMN_MAP = {
    "PROC_CD": "cpt_code",
    "ALWD_AMT": "allowed_amount",
    # ... map your columns
}
```

---

## Minimum Viable Dataset

To run a basic demo, you need **at minimum** these fields:

### Dashboard 1 (Florida Provider)
| Must Have | Nice to Have |
|-----------|-------------|
| month, provider_name, clinical_cluster, total_paid, member_count | npi, region, county, bed_count, allowed_amount, billed_amount, admits_per_1000, er_visits_per_1000 |

### Dashboard 2 (CPT Cost Driver)
| Must Have | Nice to Have |
|-----------|-------------|
| month, state, plan_type, cpt_code, member_months, total_units, allowed_amount | category, subcategory, rvu_work, rvu_total, national_benchmark, place_of_service, billed_amount, paid_amount |

---

## Data Volume Expectations

| Dataset | Dummy Data | Typical Real Data |
|---------|-----------|-------------------|
| Dashboard 1 | 4,464 rows (36 mo x 12 clusters x ~10 providers) | 50K - 500K rows |
| Dashboard 2 | 209,520 rows (36 mo x 10 states x 3 plans x 194 CPTs) | 1M - 10M rows |
| CMS PFS Reference | 18,696 CPTs per year | Same |
| CMS POS Bed Counts | 654 FL hospitals | Same |
| Member Enrollment | Not used directly (aggregated into member_months) | 1M - 50M rows |
