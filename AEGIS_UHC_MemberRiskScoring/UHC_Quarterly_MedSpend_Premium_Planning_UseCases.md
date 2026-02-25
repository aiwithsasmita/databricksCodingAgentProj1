# UnitedHealthcare: Quarterly Total Medical Spend Prediction & Premium/Price Planning

## Agentic AI & ML Use Cases — Comprehensive Blueprint

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Business Context & Problem Statement](#2-business-context--problem-statement)
3. [Available Data Inventory](#3-available-data-inventory)
4. [Additional Data Sources Recommended](#4-additional-data-sources-recommended)
5. [Use Cases — Quarterly Total Medical Spend Prediction](#5-use-cases--quarterly-total-medical-spend-prediction)
6. [Use Cases — Premium / Price Planning for Members](#6-use-cases--premium--price-planning-for-members)
7. [Early Warning Signal Framework](#7-early-warning-signal-framework)
8. [Architecture & Pipeline Overview](#8-architecture--pipeline-overview)
9. [Model Selection & Evaluation](#9-model-selection--evaluation)
10. [Implementation Roadmap](#10-implementation-roadmap)

---

## 1. Executive Summary

UnitedHealthcare's Medical Loss Ratio (MLR) rose from 83.2% in 2023 to 85.5% in 2024 — a 2.3 percentage-point jump representing hundreds of millions in unexpected medical costs. As of 2025, UNH's MLR stands near 89.4%. Even a 1% forecast error at UHC's scale translates to **$2-3 billion** in mispriced risk.

This document defines a comprehensive set of **Agentic AI and ML use cases** to:

- **Predict quarterly total medical spend** at plan, region, LOB, and population levels
- **Optimize premium/price planning** using actuarial + ML hybrid models
- **Send early warning signals** weeks-to-months before spend spikes materialize

All use cases leverage the data assets described below and recommend additional data sources identified through industry research.

---

## 2. Business Context & Problem Statement

### 2.1 Why This Matters

| Metric | Impact |
|--------|--------|
| UHC 2024 MLR | 85.5% (up from 83.2% in 2023) |
| ACA MLR Threshold | 80% individual/small group, 85% large group |
| Revenue at Risk | ~$2-3B per 1% forecast error |
| CMS V28 HCC Impact | Significant risk-score recalibration affecting MA plans |
| Pharmacy Trend | 16.1% of fully-insured private plan premiums |
| High-Cost Concentration | 2.2% of claimants drive 23% of total reimbursements |

### 2.2 Core Objectives

1. **Quarterly Med Spend Forecasting** — Predict total medical expenditure per quarter at granular levels (plan type, LOB, geography, specialty, provider network tier)
2. **Premium/Price Planning** — Set competitive, actuarially sound premiums that balance member affordability, regulatory compliance (MLR floors), and profitability
3. **Early Signal Detection** — Identify emerging cost drivers 30-90 days before they hit financial statements

---

## 3. Available Data Inventory

### 3.1 Provider Data

All provider types: Rendering, Billing, Referring, Attending, Operating, Ordering, Supervising.

| Data Element | Description | Use in Models |
|-------------|-------------|---------------|
| **TIN (Tax ID Number)** | Provider organization identifier | Provider-level cost aggregation, network leakage detection |
| **NPI (National Provider Identifier)** | Individual/organizational provider ID | Provider efficiency scoring, referral pattern analysis |
| **Taxonomy Code** | Provider classification (e.g., 207R00000X = Internal Medicine) | Specialty-level spend trending, network adequacy |
| **Specialty** | Clinical specialty (cardiology, orthopedics, etc.) | Specialty cost PMPM, utilization rate modeling |
| **Contract Type** | Fee-for-service, capitation, value-based, bundled payment | Reimbursement variance modeling, contract optimization |
| **Contract Rates** | Negotiated fee schedules, cap rates, percent of Medicare | Unit cost prediction, allowed amount forecasting |
| **Network Tier** | In-network, out-of-network, preferred, non-preferred | Network leakage cost impact |
| **Provider ZIP Code** | Geographic location | Geographic cost variation, provider access modeling |
| **Facility Type** | Hospital, ASC, office, SNF, home health | Place-of-service cost differential |
| **Credentialing Status** | Active, suspended, terminated | Network integrity, fraud detection |
| **Panel Size / Attribution** | Number of members attributed to PCP | Care coordination efficiency |
| **Quality Scores** | HEDIS, Star Ratings, value-based metrics | Quality-adjusted cost modeling |

### 3.2 Claims Data (CMS-1500 / 837P Professional Claims)

Complete fields from the CMS-1500 form:

| Box # | Field | Description | Use in Models |
|-------|-------|-------------|---------------|
| 1 | Insurance Type | Medicare, Medicaid, CHAMPUS, Group, FECA, Other | LOB segmentation |
| 1a | Insured's ID | Member/subscriber ID | Member-level spend linkage |
| 2 | Patient Name | Last, First, MI | Member identity resolution |
| 3 | Patient DOB / Sex | Date of birth, gender | Age-sex risk factors |
| 4 | Insured's Name | Policyholder name | Subscriber-dependent relationship |
| 5 | Patient Address | Street, city, state, ZIP | Geographic risk modeling, SDOH proxy |
| 6 | Patient Relationship | Self, spouse, child, other | Family unit cost modeling |
| 7 | Insured's Address | Policyholder address | Household analysis |
| 8 | Reserved (NUCC) | Patient status | — |
| 9 | Other Insured's Name | Secondary insurance holder | COB / dual-coverage cost impact |
| 9a | Other Insured's Policy/Group # | Secondary plan ID | COB coordination |
| 9b | Reserved | — | — |
| 9c | Reserved | — | — |
| 9d | Insurance Plan Name | Secondary payer plan | COB impact modeling |
| 10a-c | Condition Related To | Employment, auto accident, other accident | Subrogation, liability cost recovery |
| 10d | Claim Codes | Reserved for NUCC use | — |
| 11 | Insured's Policy Group/FECA | Group number | Group-level trend analysis |
| 11a | Insured's DOB / Sex | Policy holder demographics | Family risk profiling |
| 11b | Other Claim ID | Unique claim reference | Claim linkage, episode grouping |
| 11c | Insurance Plan / Program Name | Plan identifier | Plan-level cost trending |
| 11d | Another Health Benefit Plan? | Yes/No | COB identification |
| 12 | Patient Signature / Auth | Release of information | — |
| 13 | Insured's Signature | Authorization of payment | — |
| 14 | Date of Current Illness | Onset or LMP date | Acute vs. chronic episode dating |
| 15 | Other Date | Related condition date | Episode timeline reconstruction |
| 16 | Dates Unable to Work | From-To | Disability/productivity loss |
| 17 | Name of Referring Provider | Referring/ordering physician | Referral cost chain analysis |
| 17a | ID of Referring Provider | NPI or qualifier | Referral pattern mining |
| 17b | NPI of Referring Provider | National Provider Identifier | Referral network analysis |
| 18 | Hospitalization Dates | Admission/discharge dates | Inpatient LOS, readmission prediction |
| 19 | Additional Claim Info | Free text / attachment codes | Supplemental clinical context |
| 20 | Outside Lab? / Charges | Yes/No, charges | Lab cost leakage |
| 21 | Diagnosis Codes (ICD-10) | Up to 12 ICD-10-CM codes (A-L pointers) | Disease burden, HCC risk scoring, episode grouping |
| 22 | Resubmission Code | Original ref # for corrected claims | Claim rework rate analysis |
| 23 | Prior Authorization # | Pre-auth reference | Auth compliance, prior auth cost impact |
| 24A | Dates of Service | From-To per line | Service utilization trending |
| 24B | Place of Service (POS) | 2-digit code (11=Office, 21=Inpatient, 23=ER, etc.) | POS cost differential analysis |
| 24C | EMG (Emergency) | Emergency indicator | ED utilization trending |
| 24D | CPT/HCPCS + Modifiers | Procedure codes (up to 4 modifiers) | Service-level cost modeling, procedure trending |
| 24E | Diagnosis Pointer | Links procedure to diagnosis (A-L) | Clinical appropriateness, medical necessity |
| 24F | Charges | Billed amount per line | Billed-to-allowed ratio, charge inflation |
| 24G | Units of Service | Days or units | Utilization intensity |
| 24H | EPSDT / Family Plan | Referral code | Pediatric/family planning utilization |
| 24I | ID Qualifier | Rendering provider qualifier | — |
| 24J | Rendering Provider NPI | NPI of provider who performed service | Provider-level efficiency scoring |
| 25 | Federal Tax ID (TIN) | Provider/group TIN | Provider organization analysis |
| 26 | Patient Account # | Provider's internal reference | Claim matching |
| 27 | Accept Assignment? | Yes/No | Balance billing exposure |
| 28 | Total Charge | Sum of line charges | Total billed per claim |
| 29 | Amount Paid | Patient or other payer payment | Member cost-sharing analysis |
| 30 | Reserved | — | — |
| 31 | Signature of Provider | Attestation | — |
| 32 | Service Facility Info | Name, address, NPI of facility | Facility cost benchmarking |
| 33 | Billing Provider Info | Name, address, NPI, phone | Billing entity cost aggregation |

### 3.3 Institutional Claims (UB-04 / 837I) — Key Additional Fields

| Field | Description | Use in Models |
|-------|-------------|---------------|
| Revenue Codes | Department/service classification | Facility service-level cost modeling |
| DRG (Diagnosis Related Group) | Inpatient case classification | Inpatient cost prediction, LOS modeling |
| Admission Type | Emergency, urgent, elective, newborn | Admission pattern trending |
| Admission Source | Physician referral, ER, transfer | Care pathway analysis |
| Discharge Status | Home, SNF, expired, AMA, hospice | Post-acute cost trajectory |
| Occurrence Codes/Dates | Accident date, last menstrual period, etc. | Episode dating |
| Value Codes/Amounts | Covered days, non-covered days, coinsurance | Cost-sharing modeling |
| Condition Codes | Coverage, billing condition indicators | Coverage gap analysis |
| Total Covered Charges | Facility charges after coverage rules | Allowed amount estimation |

### 3.4 Member Data

| Data Element | Description | Use in Models |
|-------------|-------------|---------------|
| Member ID | Unique subscriber/dependent ID | Member-level longitudinal tracking |
| Demographics | Age, sex, DOB, marital status | Age-sex rating factors |
| Plan Type | HMO, PPO, EPO, POS, HDHP, Medicare Advantage, Medicaid Managed Care | Plan-level cost segmentation |
| Plan Metal Level | Bronze, Silver, Gold, Platinum (ACA) | Actuarial value & induced utilization |
| Benefit Design | Deductible, copay, coinsurance, OOP max | Member cost-sharing behavior |
| Effective/Term Dates | Enrollment start/end | Member months calculation, churn analysis |
| Geographic Data | ZIP, county, state, MSA, rating area | Geographic cost factors, SDOH proxy |
| Employer Group | Group ID, SIC code, group size | Group-level trending, experience rating |
| Subscriber/Dependent | Relationship code, family size | Family unit cost modeling |
| Risk Score | HCC risk score (prospective/concurrent) | Risk-adjusted cost prediction |
| PCP Assignment | Attributed primary care provider | Medical home cost impact |
| Chronic Conditions | Flags for diabetes, CHF, COPD, etc. | Disease management targeting |
| Prior Utilization | Historical claims summary | Cost trajectory prediction |
| Eligibility Status | Active, COBRA, retiree, disabled | Population stratification |

### 3.5 Adjustment / Remittance Data (ERA 835)

| Data Element | Description | Use in Models |
|-------------|-------------|---------------|
| Adjustment Reason Code (ARC) | CAS codes: CO, PR, OA, PI, CR | Denial rate, adjustment trending |
| Claim Adjustment Group | Contractual (CO), Patient Responsibility (PR), Other (OA) | Cost-sharing vs. contractual adjustments |
| Remark Codes (RARC) | Supplemental explanation | Root-cause denial analysis |
| Paid Amount | Net payment after adjustments | Actual cost vs. allowed amount |
| Allowed Amount | Contract-based allowed charges | Unit cost trending |
| Deductible Applied | Member deductible consumed | Deductible leveraging analysis |
| Copay Amount | Fixed member copay | Cost-sharing effectiveness |
| Coinsurance Amount | Percentage-based member share | Member financial exposure |
| Interest/Penalty | Late payment interest | Cash flow impact |
| Withhold Amount | VBP or quality withhold | Value-based contract performance |
| Coordination of Benefits | Other payer payments | True cost-to-plan calculation |
| Check/EFT Date | Payment date | Payment lag analysis, IBNR estimation |
| Claim Status | Paid, denied, pended, adjusted | Claims lifecycle tracking |

### 3.6 Call Center Data (Member & Provider)

| Data Element | Description | Use in Models |
|-------------|-------------|---------------|
| Call Type | Benefits inquiry, claim status, authorization, complaint, appeal | Service demand forecasting |
| Call Reason Code | Structured reason taxonomy | Issue trending, early signal of plan friction |
| Caller ID | Member ID or Provider NPI | Linkage to claims/enrollment |
| Call Date/Time | Timestamp | Temporal pattern analysis |
| Call Duration | Handle time | Operational cost |
| Resolution Status | First-call resolution, escalated, callback | Member satisfaction proxy |
| Sentiment Score | NLP-derived or agent-rated | Disenrollment risk, quality signal |
| Complaint/Grievance Flag | Formal grievance indicator | Regulatory compliance, quality |
| Prior Auth Request | Auth number, status, urgency | Upcoming high-cost service signal |
| Provider Dispute | Contested payment | Contract friction, rate adequacy |
| Appeal Filed | Member or provider appeal | Cost reversal risk |
| Topic / NLP Categories | Auto-classified from call transcript | Emerging issue detection |

### 3.7 Revenue Cycle Management (RCM) / Association Data

| Data Element | Description | Use in Models |
|-------------|-------------|---------------|
| Charge Master Rates | Facility list prices | Billed charge inflation trending |
| Contracted Rates | Negotiated rates by service | Unit cost modeling |
| Payment Variance | Expected vs. actual payment | Underpayment/overpayment detection |
| Days in AR | Aging of receivables | Payment lag, IBNR estimation |
| Denial Rate by Category | Clinical, admin, technical denials | Denial cost recovery opportunity |
| Authorization Status | Approved, pended, denied, expired | Prior auth cost impact |
| Claim Edit Results | Pre/post adjudication edits | Payment integrity savings |
| Provider Dispute Volume | Contested claims count | Contract adequacy signal |
| Recoupment/Recovery | Post-pay audit recoveries | Net cost adjustment |

---

## 4. Additional Data Sources Recommended

Based on industry research and best practices, the following **additional data sources** significantly improve prediction accuracy:

### 4.1 Social Determinants of Health (SDOH) — HIGH PRIORITY

Research from JAMA Network Open and AJMC confirms SDOH adds **5-15% predictive lift** for high-cost utilizer identification. 80-90% of modifiable health-related behaviors are driven by social/economic factors; medical care accounts for only 10-20%.

| Data Source | Key Elements | Source |
|------------|-------------|--------|
| **AHRQ SDOH Database** | County-level social, economic, education, healthcare, neighborhood factors | ahrq.gov/sdoh/data-analytics |
| **Area Deprivation Index (ADI)** | Neighborhood socioeconomic disadvantage rank | University of Wisconsin |
| **Census / ACS Data** | Income, education, employment, housing, poverty rates by ZIP/census tract | census.gov |
| **Social Vulnerability Index (SVI)** | CDC's 16-variable composite of social vulnerability | ATSDR/CDC |
| **Food Access Research Atlas** | Food desert identification | USDA |
| **Health Professional Shortage Areas** | Provider shortage designations | HRSA |
| **LexisNexis SDOH Attributes** | Individual-level socioeconomic health attributes (commercial) | LexisNexis Risk Solutions |

---

#### 4.1.1 HOW TO GET SDOH DATA — Source-by-Source Acquisition Guide

---

##### SOURCE 1: AHRQ SDOH Database (FREE — Federal Government)

**What it is:** A consolidated database of 17,000+ variables from 44 federal data sources, pre-linked by geography. Created under Patient-Centered Outcomes Research (PCOR) Trust Fund.

**Coverage:**
- Geographic levels: County (2009-2020), ZIP Code Tabulation Area / ZCTA (2011-2020), Census Tract
- Five domains: Social Context, Economic Context, Education, Physical Infrastructure, Healthcare Context

**How to Get It:**

| Step | Action | Details |
|------|--------|---------|
| 1 | Go to download page | `https://www.ahrq.gov/sdoh/data-analytics/sdoh-data.html` |
| 2 | Select geographic level | Choose **County**, **ZCTA** (ZIP Code), or **Census Tract** |
| 3 | Select year | Available 2009-2020 (select most recent) |
| 4 | Download format | CSV files (public use data files, no registration required) |
| 5 | Review documentation | Download data dictionary from `https://www.ahrq.gov/sites/default/files/wysiwyg/sdoh/SDOH-Data-Sources-Documentation-v1-Final.pdf` |
| 6 | Join to member data | Match on **ZCTA** (5-digit ZIP → ZCTA crosswalk) or **County FIPS code** from member address |

**Key Variables for Med Spend Prediction:**
- `ACS_PCT_LT_HS` — % population without high school diploma
- `ACS_MEDIAN_HH_INC` — Median household income
- `ACS_PCT_UNINSURED` — % uninsured population
- `ACS_PCT_UNEMPLOY` — Unemployment rate
- `ACS_PCT_POVERTY` — % below poverty line
- `AHRF_TOT_PHYS_RATE` — Total physicians per 100K population
- `POS_DIST_ED_NEAREST` — Distance to nearest emergency department

**Linkage to Claims:**
```
Member Address ZIP → ZCTA Crosswalk (Census) → AHRQ SDOH ZCTA file
                  → County FIPS              → AHRQ SDOH County file
```

**Refresh Frequency:** Annual (typically 6-12 month lag from source surveys)

---

##### SOURCE 2: Area Deprivation Index / ADI (FREE — Academic / Creative Commons)

**What it is:** A factor-based index ranking neighborhoods by socioeconomic disadvantage using 17 Census indicators (income, education, employment, housing quality). Published in New England Journal of Medicine (2018). Validated for linking to health outcomes.

**Coverage:**
- 9-digit ZIP code level and Census Block Group level
- National percentile (1-100) and state-specific decile (1-10)
- All 50 states + DC

**How to Get It:**

| Step | Action | Details |
|------|--------|---------|
| 1 | Go to Neighborhood Atlas | `https://www.neighborhoodatlas.medicine.wisc.edu/` |
| 2 | Create free account | Register with email (required for download) |
| 3 | Select version | Choose most recent year (based on ACS 5-year estimates) |
| 4 | Download | CSV file with ADI rankings by 9-digit ZIP or Census Block Group FIPS |
| 5 | Alternative: R package | Use `sociome` R package: `get_adi(geography = "tract", year = 2021, state = "OH")` (requires Census API key) |
| 6 | Alternative: Python | GitHub repo `AyushDoshi/geocode-adi` — converts addresses to Census Block Group ADI |
| 7 | Alternative: BigQuery | Available on Redivis: `https://redivis.com/datasets/axrk-7jx8wdwc2` |

**Key Fields:**
- `ADI_NATRANK` — National percentile rank (1 = least deprived, 100 = most deprived)
- `ADI_STATEFIPS` — State FIPS code
- `ADI_STATERANK` — State-specific decile (1-10)
- `FIPS` — 12-digit Census Block Group FIPS code

**Linkage to Claims:**
```
Member 9-digit ZIP  → Direct join to ADI 9-digit ZIP file
Member Address      → Geocode to lat/long → Census Block Group FIPS → ADI Block Group file
Member 5-digit ZIP  → ZCTA-to-Block Group crosswalk (Census) → ADI (NOTE: not validated, approximate only)
```

**Important Note:** University of Wisconsin states that linking ADI to 5-digit ZIP codes or ZCTAs is "not a validated approach." For best accuracy, use 9-digit ZIP or geocode to Census Block Group.

**License:** Creative Commons Attribution-NonCommercial-ShareAlike 4.0 (free for research and internal use)

---

##### SOURCE 3: US Census American Community Survey / ACS (FREE — Federal Government API)

**What it is:** The most comprehensive ongoing survey of American demographics and socioeconomics. The "gold standard" for population-level SDOH features. Over 31,000 variables.

**Coverage:**
- ACS 1-Year: Areas with 65,000+ population (most recent data)
- ACS 5-Year: All geographies down to Census Block Group (more granular, slight lag)
- Years: Updated annually

**How to Get It:**

| Step | Action | Details |
|------|--------|---------|
| 1 | Get a Census API key | Register free at `https://api.census.gov/data/key_signup.html` (instant) |
| 2 | Choose survey | ACS 1-Year (latest: 2024) or ACS 5-Year (latest: 2023, more granular) |
| 3 | API endpoint | `https://api.census.gov/data/2024/acs/acs1?get=NAME,B19013_001E&for=county:*&in=state:*&key=YOUR_KEY` |
| 4 | Python library | `pip install census` or use `requests` directly |
| 5 | Bulk download | `https://www.census.gov/programs-surveys/acs/data.html` → Data Profiles, Subject Tables |
| 6 | Pre-built SDOH extract | `https://catalog.data.gov/dataset/sdoh-measures-for-place-acs-2017-2021` (CDC-curated) |

**Python Example to Pull SDOH Variables:**
```python
import requests

API_KEY = "your_census_api_key"
BASE_URL = "https://api.census.gov/data/2023/acs/acs5"

# Key SDOH variables
variables = [
    "B19013_001E",  # Median household income
    "B17001_002E",  # Population below poverty level
    "B15003_001E",  # Total population 25+ (education denominator)
    "B15003_002E",  # No schooling completed
    "B27001_001E",  # Total population (insurance denominator)
    "B23025_005E",  # Unemployed
    "B25064_001E",  # Median gross rent
    "B25077_001E",  # Median home value
]

params = {
    "get": f"NAME,{','.join(variables)}",
    "for": "zip code tabulation area:*",
    "key": API_KEY,
}

response = requests.get(BASE_URL, params=params)
data = response.json()
```

**Key Variable Groups for Healthcare Cost Prediction:**

| Variable Table | Description | Example Variable |
|---------------|-------------|-----------------|
| B19013 | Median Household Income | `B19013_001E` |
| B17001 | Poverty Status | `B17001_002E` (below poverty) |
| B15003 | Educational Attainment | `B15003_017E` (HS diploma), `B15003_022E` (bachelor's) |
| B27001 | Health Insurance Coverage | `B27001_005E` (uninsured, male 18-25) |
| B23025 | Employment Status | `B23025_005E` (unemployed) |
| B25064 | Median Gross Rent | `B25064_001E` |
| B25077 | Median Home Value | `B25077_001E` |
| B08301 | Means of Transportation to Work | `B08301_010E` (public transit) |
| B16004 | Language Spoken at Home | Limited English proficiency |
| B11001 | Household Type | Single-person, single-parent households |

**Linkage to Claims:**
```
Member 5-digit ZIP → ZCTA (ZIP Code Tabulation Area) → ACS 5-Year ZCTA tables
Member Address     → Geocode → Census Tract FIPS       → ACS 5-Year Tract tables
```

---

##### SOURCE 4: CDC Social Vulnerability Index / SVI (FREE — Federal Government)

**What it is:** A composite index of 16 social factors organized into 4 themes, ranking every Census tract and county on vulnerability. Developed by CDC's Agency for Toxic Substances and Disease Registry (ATSDR).

**Coverage:**
- Census Tract level, County level, ZCTA level (2022 only)
- All 50 states + DC + US territories
- Years available: 2000, 2010, 2014, 2016, 2018, 2020, 2022

**How to Get It:**

| Step | Action | Details |
|------|--------|---------|
| 1 | Download page | `https://svi.cdc.gov/dataDownloads/data-download.html` |
| 2 | Select year | Choose **2022** (most recent, includes ZCTA level) |
| 3 | Select geography | Census Tract (finest grain), County, or ZCTA |
| 4 | Select state | Individual state or "United States" for national |
| 5 | Select ranking scope | National ranking or State-specific ranking |
| 6 | Download format | **CSV** (table data) or **ESRI Geodatabase** (for GIS/mapping) |
| 7 | Alternative: API | Socrata Open Data API at `https://data.cdc.gov/Vaccinations/Social-Vulnerability-Index/ypqf-r5qs` |
| 8 | Alternative: ArcGIS | Search "CDC Social Vulnerability Index" in ArcGIS Online |

**4 SVI Themes and Their Variables:**

| Theme | Variables | Key Column |
|-------|----------|------------|
| **Theme 1: Socioeconomic Status** | Below 150% poverty, unemployed, housing cost burden, no health insurance, no high school diploma | `RPL_THEME1` (0-1 percentile) |
| **Theme 2: Household Characteristics** | Aged 65+, aged 17 and younger, civilian with disability, single-parent households, English language proficiency | `RPL_THEME2` |
| **Theme 3: Racial & Ethnic Minority Status** | Racial/ethnic minority populations | `RPL_THEME3` |
| **Theme 4: Housing Type / Transportation** | Multi-unit structures, mobile homes, crowding, no vehicle, group quarters | `RPL_THEME4` |
| **Overall** | Composite of all 16 variables | `RPL_THEMES` (0 = least vulnerable, 1 = most vulnerable) |

**Linkage to Claims:**
```
Member Address → Geocode → Census Tract FIPS (11-digit) → SVI Tract file (FIPS column)
Member 5-digit ZIP → ZCTA → SVI ZCTA file (2022 only)
Member County → County FIPS → SVI County file
```

---

##### SOURCE 5: USDA Food Access Research Atlas (FREE — Federal Government)

**What it is:** Census-tract-level data identifying food deserts — areas where residents have limited access to affordable and nutritious food. Food insecurity is a known driver of chronic disease (diabetes, hypertension) and ER utilization.

**Coverage:**
- Census Tract level (all US tracts)
- Current version based on 2019 data; previous versions from 2010, 2015

**How to Get It:**

| Step | Action | Details |
|------|--------|---------|
| 1 | Download page | `https://www.ers.usda.gov/data-products/food-access-research-atlas/download-the-data` |
| 2 | Download current data | CSV or Excel file with all Census tracts |
| 3 | Interactive map | `https://www.ers.usda.gov/data-products/food-access-research-atlas/go-to-the-atlas` |
| 4 | API access | USDA Geospatial API (see documentation on download page) |
| 5 | Alternative: data.gov | `https://catalog.data.gov/dataset/food-access-research-atlas` |

**Key Fields:**

| Field | Description | Use for Cost Prediction |
|-------|-------------|------------------------|
| `LILATracts_1And10` | Low Income AND Low Access (1 mile urban / 10 mile rural) | Primary food desert flag |
| `LILATracts_halfAnd10` | Low Income AND Low Access (0.5 mile urban / 10 mile rural) | Stricter food desert definition |
| `lapop1` | Population, low access at 1 mile | Affected population count |
| `lalowi1` | Low income, low access at 1 mile | Low-income population in food desert |
| `lasnap1` | SNAP recipients, low access at 1 mile | Safety-net population measure |
| `TractSNAP` | SNAP recipient count in tract | Food assistance utilization |

**Linkage to Claims:**
```
Member Address → Geocode → Census Tract FIPS (11-digit) → Food Access Atlas (CensusTract column)
```

---

##### SOURCE 6: HRSA Health Professional Shortage Areas / HPSA (FREE — Federal Government)

**What it is:** Federal designations of geographic areas, populations, or facilities with a shortage of primary care, dental, or mental health providers. Members in HPSAs have reduced access and tend toward higher ER utilization and delayed care (resulting in higher costs).

**Coverage:**
- Geographic HPSAs (entire counties or partial county areas)
- Population HPSAs (specific underserved populations within an area)
- Facility HPSAs (specific qualifying health facilities)
- HPSA Score (1-26, higher = greater shortage)

**How to Get It:**

| Step | Action | Details |
|------|--------|---------|
| 1 | Bulk data download | `https://data.hrsa.gov/data/download` → Select "Shortage Areas" |
| 2 | HPSA search tool | `https://data.hrsa.gov/tools/shortage-area/hpsa-find` (search by state, county, discipline) |
| 3 | Address lookup | `https://data.hrsa.gov/topics/health-workforce/shortage-areas/by-address` (check if a specific address is in HPSA) |
| 4 | GIS / API access | ArcGIS REST API: `https://gisportal.hrsa.gov/server/rest/services/Shortage` — supports JSON, GeoJSON queries |
| 5 | Area Health Resources Files | `https://data.hrsa.gov/data/download` → AHRF (county-level resource file, updated annually) |

**GIS API Query Example:**
```
GET https://gisportal.hrsa.gov/server/rest/services/Shortage/HealthProfessionalShortageAreas_FS/MapServer/10/query
?where=HPSA_STATUS='Designated'
&outFields=*
&f=json
&returnGeometry=true
```

**Key Fields from HPSA Download:**

| Field | Description |
|-------|-------------|
| `HPSA_Name` | Designation name |
| `HPSA_Score` | Shortage severity (1-26, higher = worse) |
| `HPSA_Type` | Geographic, Population, or Facility |
| `Discipline` | Primary Care, Dental, or Mental Health |
| `Designation_Date` | When designation was established |
| `HPSA_Status` | Designated, Proposed for Withdrawal, etc. |
| `County_Name` / `State_Abbr` | Location identifiers |
| `HPSA_FTE` | Full-time equivalent practitioners |
| `HPSA_Shortage` | Number of additional practitioners needed |

**Linkage to Claims:**
```
Member Address → Address lookup via HRSA API → HPSA designation + score
Member County  → HPSA bulk download → match on County FIPS
Provider NPI   → Cross-reference with HPSA facility designations
```

---

##### SOURCE 7: LexisNexis Socioeconomic Health Attributes (COMMERCIAL — Paid License)

**What it is:** The only **individual-level** SDOH data product (all other sources above are area-level). LexisNexis aggregates consumer data, public records, and behavioral data to create clinically validated, HIPAA-compliant individual socioeconomic attributes and risk scores. Used by major health plans including UnitedHealthcare.

**Why It Matters:** Area-level data (ZIP/tract) assumes everyone in a neighborhood is similar. LexisNexis provides **person-level** attributes — far more precise for member-level risk prediction.

**Coverage:**
- Individual-level (matched by member name + address + DOB)
- 300+ socioeconomic health attributes
- Pre-built risk scores (readmission risk, high-cost risk)
- All 50 states

**How to Get It:**

| Step | Action | Details |
|------|--------|---------|
| 1 | Contact LexisNexis Health | `https://risk.lexisnexis.com/healthcare/social-determinants-of-health` |
| 2 | Request demo/evaluation | Ask for Socioeconomic Health Attributes (SHA) product |
| 3 | Data delivery options | **Batch file** (send member roster, receive back SDOH attributes) or **Real-time API** (REST API, per-query) |
| 4 | BAA required | Business Associate Agreement for HIPAA compliance |
| 5 | Pricing model | Per-member-per-month (PMPM) or per-query, varies by volume |
| 6 | Integration | Flat file (CSV/pipe-delimited), SFTP delivery, or REST API into data lake |

**Key Attributes / Scores:**

| Attribute Category | Examples |
|-------------------|----------|
| **Income Attributes** | Estimated household income, income stability, years of income history |
| **Housing Attributes** | Home ownership, housing type, housing stability, recent moves |
| **Education** | Educational attainment level |
| **Employment** | Occupation type, employment stability |
| **Financial Stress** | Bankruptcy history, liens, judgments, financial instability indicators |
| **Neighborhood** | Crime index, walkability, transportation access |
| **Social Isolation** | Single-person household, limited social connections |
| **Pre-Built Scores** | Socioeconomic Health Score (composite), Readmission Risk Score, Medication Adherence Likelihood |

**Validation:** LexisNexis reports that adding individual SHA data to clinical + claims models improved high-cost utilizer prediction by 8-15% AUC lift in published studies with Clarify Health.

**Cost Estimate:** Typically $0.10 - $0.50 PMPM depending on volume and attribute depth. For a 10M member plan, budget ~$1M-5M/year.

**NCQA/CMS Alignment:** NCQA introduced SDOH screening measure for health plans; CMS is discussing inclusion in Medicare Star Ratings. Early investment in SDOH data creates competitive advantage.

---

##### SOURCE 8: Other Supplementary SDOH Sources (FREE)

| Source | URL | Data | Format |
|--------|-----|------|--------|
| **EPA Environmental Justice Screening (EJScreen)** | `https://www.epa.gov/ejscreen` | Air toxics, lead paint, proximity to hazardous waste | CSV, Shapefile, API |
| **USDA Rural-Urban Commuting Area (RUCA)** | `https://www.ers.usda.gov/data-products/rural-urban-commuting-area-codes/` | Rural-urban classification by Census tract/ZIP | Excel download |
| **CDC PLACES** | `https://www.cdc.gov/places/` | County/tract-level health estimates (smoking, obesity, diabetes prevalence) | CSV, API |
| **County Health Rankings (Robert Wood Johnson)** | `https://www.countyhealthrankings.org/` | Composite health factors & outcomes by county | Excel download |
| **HUD Location Affordability Index** | `https://www.huduser.gov/portal/datasets/location-affordability-index.html` | Housing + transportation cost burden by tract | CSV |
| **National Walkability Index** | `https://catalog.data.gov/dataset/walkability-index1` | EPA walkability score by Census Block Group | GIS, CSV |
| **FCC Broadband Map** | `https://broadbandmap.fcc.gov/` | Internet access by address/Census block | API, bulk download |

---

##### SDOH Data Integration Architecture

```
MEMBER ROSTER                           SDOH DATA LAYER
(from enrollment)                       (in data lake)
 ┌───────────────┐                     ┌──────────────────────────┐
 │ Member ID     │                     │  AREA-LEVEL SDOH         │
 │ Name          │──── Geocode ──────►│  ┌─ AHRQ (ZIP/County)    │
 │ Address       │     (Smarty,        │  ├─ ADI (Block Group)    │
 │ ZIP Code      │      Google,        │  ├─ SVI (Census Tract)   │
 │ DOB           │      Census)        │  ├─ ACS (ZIP/Tract)      │
 │ County FIPS   │                     │  ├─ Food Atlas (Tract)   │
 └───────────────┘                     │  ├─ HPSA (County/Area)   │
        │                              │  ├─ CDC PLACES (Tract)   │
        │                              │  └─ RUCA (ZIP/Tract)     │
        │                              └──────────────────────────┘
        │                                          │
        │                                          ▼
        │                              ┌──────────────────────────┐
        │                              │  MEMBER SDOH FEATURE     │
        │──── Match (Name+DOB+Addr) ──►│  VECTOR                  │
        │     via LexisNexis API       │  ┌─ ADI_NATRANK          │
        │                              │  ├─ SVI_OVERALL          │
        │                              │  ├─ MEDIAN_HH_INCOME     │
        │                              │  ├─ PCT_POVERTY          │
        │                              │  ├─ FOOD_DESERT_FLAG     │
        │                              │  ├─ HPSA_SCORE           │
        │                              │  ├─ LEXIS_SHA_SCORE      │
        │                              │  ├─ UNEMPLOYMENT_RATE    │
        │                              │  ├─ PCT_NO_INSURANCE     │
        │                              │  └─ BROADBAND_ACCESS     │
        │                              └──────────────────────────┘
        │                                          │
        ▼                                          ▼
 ┌─────────────────────────────────────────────────────────────┐
 │              ML FEATURE STORE                                │
 │   member_id | risk_score | pmpm_12mo | adi_rank | svi | ... │
 │   Used by: UC-SPEND-03, UC-SPEND-06, UC-PREM-01, UC-PREM-02│
 └─────────────────────────────────────────────────────────────┘
```

##### Recommended Priority Order for SDOH Data Acquisition

| Priority | Source | Cost | Effort | Predictive Value | Timeline |
|----------|--------|------|--------|-----------------|----------|
| **1** | CDC SVI | Free | Low (CSV download, tract-level join) | High (16-variable composite) | Week 1 |
| **2** | ACS via Census API | Free | Medium (API integration, variable selection) | Very High (granular income, education, insurance) | Weeks 1-2 |
| **3** | ADI (Neighborhood Atlas) | Free | Low-Medium (registration, geocoding for block group) | Very High (validated, published in NEJM) | Weeks 1-2 |
| **4** | AHRQ SDOH Database | Free | Low (pre-consolidated, CSV download) | High (44 sources combined) | Week 1 |
| **5** | USDA Food Atlas | Free | Low (CSV download, tract join) | Medium-High (food desert flag) | Week 1 |
| **6** | HRSA HPSA | Free | Medium (GIS API or bulk download) | Medium-High (provider access) | Weeks 2-3 |
| **7** | CDC PLACES | Free | Low (CSV download) | Medium (health behavior prevalence) | Week 2 |
| **8** | LexisNexis SHA | $1-5M/year | High (vendor contract, BAA, API integration) | Very High (individual-level, 8-15% AUC lift) | Months 2-4 |

**Recommendation:** Start with Sources 1-5 (all free, can be operational in 1-2 weeks) for immediate predictive lift. Add LexisNexis individual-level data in Phase 2 for maximum accuracy on high-cost member prediction.

### 4.2 Pharmacy & Drug Data — HIGH PRIORITY

Pharmacy accounts for ~16% of commercial plan premiums. Missing pharmacy data is a major gap.

| Data Source | Key Elements | Why Needed |
|------------|-------------|------------|
| **Pharmacy Claims (NCPDP D.0)** | NDC, days supply, quantity, ingredient cost, dispensing fee, copay | Drug cost trending, specialty drug prediction |
| **Pharmacy Benefit Manager (PBM) Data** | Rebates, formulary tier, prior auth, step therapy | Net drug cost calculation |
| **Specialty Drug Pipeline** | FDA approval pipeline, gene therapy launches | Future high-cost drug exposure |
| **Biosimilar Adoption Rates** | Biosimilar vs. reference biologic utilization | Drug savings opportunity |
| **Rebate Data** | Manufacturer rebates by NDC, class | True net cost calculation |
| **Formulary Changes** | Tier changes, new additions, removals | Utilization shift prediction |

### 4.3 Clinical / Electronic Health Record (EHR) Data

| Data Source | Key Elements | Why Needed |
|------------|-------------|------------|
| **Lab Results** | HbA1c, LDL, eGFR, BMI, blood pressure | Disease progression signals (pre-claims) |
| **Vital Signs** | BP, BMI, heart rate trends | Early deterioration detection |
| **Problem Lists** | Active diagnoses beyond claims | Complete condition picture |
| **Medication Orders** | Prescribed vs. filled gap | Adherence prediction |
| **Care Plans** | Documented treatment plans | Expected utilization signals |
| **ADT Feeds** | Real-time admit/discharge/transfer | Inpatient census, IBNR improvement |

### 4.4 External / Macro-Economic Data

| Data Source | Key Elements | Why Needed |
|------------|-------------|------------|
| **CPI-Medical** | Medical care inflation index (Bureau of Labor Statistics) | Medical trend factor |
| **PwC Medical Cost Trend** | Annual projected medical cost trend (7% for 2026) | Benchmark trend rate |
| **CMS National Health Expenditure** | National spending projections by category | Macro trend calibration |
| **Bureau of Labor Statistics** | Wage inflation, employment rates | Employer group membership churn |
| **Interest Rates / Treasury Yield** | Federal funds rate, yield curve | Investment income on reserves |
| **State Regulatory Filings** | Rate review, MLR filings | Competitive intelligence |

### 4.5 Utilization Management / Care Management Data

| Data Source | Key Elements | Why Needed |
|------------|-------------|------------|
| **Prior Authorization Logs** | Requested, approved, denied, pended by service type | Leading indicator of upcoming spend |
| **Case Management Records** | High-cost case flags, care plans, interventions | Impact of CM on cost trajectory |
| **Disease Management Enrollment** | DM program participation, engagement scores | Cost reduction attribution |
| **Transplant / High-Cost Case Registry** | Known transplant candidates, gene therapy candidates | Catastrophic cost forecasting |
| **Concurrent Review Data** | LOS management, continued stay reviews | Inpatient cost management effectiveness |

### 4.6 Provider Performance & Network Data

| Data Source | Key Elements | Why Needed |
|------------|-------------|------------|
| **HEDIS Measures** | Preventive care rates, chronic care quality | Quality-adjusted cost prediction |
| **Star Ratings** | MA plan quality scores | MA bonus revenue impact |
| **Provider Efficiency Scores** | Cost per episode, readmission rates | Network cost management |
| **Network Disruption Alerts** | Provider terminations, new contracts | Unit cost shift signals |
| **Telehealth Utilization** | Virtual visit rates by specialty | Care delivery cost shift |

### 4.7 Reinsurance / Stop-Loss Data

| Data Source | Key Elements | Why Needed |
|------------|-------------|------------|
| **Specific Stop-Loss** | Individual claimant attachment point, claims approaching threshold | Catastrophic cost cap impact |
| **Aggregate Stop-Loss** | Plan-level attachment point | Plan-level risk corridor |
| **Reinsurance Recoveries** | Amounts recovered from reinsurer | Net cost calculation |
| **Large Claim Inventory** | Known open high-cost cases | IBNR for catastrophic cases |

### 4.8 Weather, Epidemic & Environmental Data

| Data Source | Key Elements | Why Needed |
|------------|-------------|------------|
| **CDC FluView** | Weekly influenza surveillance | Seasonal cost spike prediction |
| **Epidemic/Pandemic Indicators** | COVID, RSV, flu hospitalization rates | Acute utilization surge |
| **Air Quality Index (AQI)** | EPA air quality by region | Respiratory cost correlation |
| **Wildfire / Natural Disaster Feeds** | FEMA, NOAA alerts | Catastrophic event cost spikes |
| **Heat Index / Extreme Weather** | Temperature extremes | ER utilization surges |

---

## 5. Use Cases — Quarterly Total Medical Spend Prediction

### UC-SPEND-01: Population-Level Quarterly Spend Forecasting

**Objective:** Predict total medical expenditure (PMPM x member months) for each upcoming quarter at plan, LOB, and geography level.

**Approach:**
- Time-series models (ARIMA, Prophet, LSTM) on historical quarterly PMPM trends
- Cross-sectional enrichment with risk-score shifts, membership churn, and provider rate changes
- Separate models by LOB: Commercial (Fully Insured, ASO), Medicare Advantage, Medicaid Managed Care, Exchange

**Input Features:**
- Historical PMPM by month/quarter (12-36 month lookback)
- Member months by plan type, age-sex band, rating area
- Average HCC risk score by plan cohort
- Seasonal indices (Q1 flu season, Q2 deductible resets, Q4 procedure surge)
- Medical cost trend factor (PwC/Milliman benchmarks)
- Provider rate escalation schedule
- New specialty drug launches in pipeline
- Benefit design changes (deductible, OOP max changes)
- Membership growth/churn projections

**Output:**
- Quarterly total medical spend (point estimate + 80%/95% prediction intervals)
- Breakdown by: inpatient, outpatient, professional, pharmacy, behavioral health, other
- Variance from budget/target with root-cause attribution

**Target Accuracy:** MAPE < 2% at LOB level, < 5% at sub-plan level

---

### UC-SPEND-02: Service-Category Spend Decomposition

**Objective:** Predict spend by major service categories to identify which categories are driving total spend movement.

**Service Categories:**
| Category | Key Drivers |
|----------|------------|
| Inpatient Medical | Admission rate, ALOS, case mix (DRG), per-diem rates |
| Inpatient Surgical | Procedure volume, implant costs, OR time |
| Outpatient Surgery (ASC) | Shift from IP to OP, ASC rates |
| Emergency Department | ED visit rate, acuity mix, observation hours |
| Professional Services | Visit rates by specialty, E&M level distribution |
| Radiology / Imaging | Advanced imaging rates (MRI, CT, PET), unit costs |
| Laboratory | Test utilization rates, reference lab costs |
| Pharmacy (Rx) | Specialty vs. traditional, brand vs. generic, biosimilar adoption |
| Behavioral Health | BH visit rates, inpatient BH days, MAT programs |
| Skilled Nursing / Rehab | SNF days, home health visits, rehab sessions |
| Durable Medical Equipment | DME utilization, CGM/insulin pump costs |
| Telehealth | Virtual visit substitution rate, cost differential |

**Approach:**
- Hierarchical forecasting: category-level forecasts constrained to reconcile to total
- Gradient Boosted Trees (XGBoost/LightGBM) for category-level PMPM
- Transfer learning from national benchmarks to small-population segments

---

### UC-SPEND-03: High-Cost Claimant (HCC) Prediction

**Objective:** Identify members likely to exceed $50K, $100K, $250K+ in the next quarter.

**Key Insight:** 2.2% of claimants drive 23% of total reimbursements. Predicting who transitions into high-cost status is the single highest-value use case.

**Input Features:**
- Prior 12-month total allowed, paid, and member cost-sharing
- Active chronic conditions (diabetes, CHF, ESRD, cancer, transplant)
- Recent acute events (ER visits, hospitalizations, ICU days)
- Specialty drug utilization (oncology, autoimmune, rare disease)
- Prior authorization requests for high-cost services
- Lab values (when available): HbA1c, creatinine/eGFR, tumor markers
- Care management enrollment and engagement
- SDOH factors (ADI, food access, housing instability)

**Model Architecture:**
- Two-stage model:
  - Stage 1: Binary classifier (will member exceed threshold? — XGBoost, ~76% recall for top decile)
  - Stage 2: Regression on predicted high-cost members (expected spend — LightGBM or neural net)
- Calibrated probability outputs for actuarial reserving

**Output:**
- Ranked member list with predicted spend and confidence intervals
- Top contributing features per member (SHAP explanations)
- Aggregate high-cost pool estimate per quarter

---

### UC-SPEND-04: IBNR (Incurred But Not Reported) Estimation

**Objective:** Predict claims that have been incurred but not yet reported/adjudicated, for accurate quarterly financial close.

**Why Critical:** At any quarter-end, 15-25% of incurred claims haven't been received or adjudicated. Underestimating IBNR = understated liabilities; overestimating = excess reserves.

**Input Features:**
- Claim lag triangles by service category, provider type, geography
- Prior authorization approvals not yet matched to claims
- ADT (admit/discharge/transfer) feeds for known inpatient stays
- Historical completion factors by incurred month
- Day-of-week and holiday effects on claim submission patterns
- Provider billing cycle patterns (monthly vs. weekly submitters)
- Call center inquiries about claim status

**Approach:**
- Chain Ladder method (traditional actuarial) as baseline
- ML-enhanced: Gradient boosted completion factor models
- Real-time adjustment using ADT feeds and auth data as leading indicators

**Output:**
- IBNR estimate by service category, LOB, and incurred month
- Completion factor curves with uncertainty bands
- Weekly IBNR refresh during quarter-close period

---

### UC-SPEND-05: Provider-Level Cost Anomaly Detection

**Objective:** Detect providers whose cost patterns deviate significantly from peers, indicating potential overutilization, upcoding, or emerging cost trends.

**Input Features:**
- Provider-level PMPM for attributed members
- Procedure code frequency distribution vs. specialty peers
- E&M level distribution (upcoding detection)
- Referral out-rate and referral cost chain
- Modifier usage patterns (modifier 25, 59 abuse)
- Average units per claim line
- Denial/adjustment rate by provider
- Patient panel acuity (risk-adjusted comparison)

**Approach:**
- Isolation Forest / Local Outlier Factor for multivariate anomaly detection
- Peer benchmarking with risk adjustment
- Time-series anomaly detection for trending shifts

**Output:**
- Provider anomaly score and rank
- Specific anomalous dimensions (volume, intensity, coding, referral pattern)
- Estimated financial impact of anomalous behavior
- Drill-down to specific claims driving the anomaly

---

### UC-SPEND-06: Geographic Cost Variation Modeling

**Objective:** Model and predict regional medical cost variation to improve geographic rating factors and identify emerging cost hot spots.

**Input Features:**
- ZIP/county-level PMPM history
- Provider concentration and competition (HHI index)
- SDOH indices by geography (ADI, SVI, food access)
- COL / CPI-Medical by MSA
- HPSA designations
- Telehealth penetration rate
- State regulatory environment (mandated benefits, CON laws)
- Natural disaster / epidemic incidence

**Output:**
- Geographic cost factors by rating area
- Emerging hot spot alerts (regions accelerating above trend)
- Root-cause analysis per geography

---

### UC-SPEND-07: Pharmacy Spend Forecasting

**Objective:** Predict quarterly pharmacy expenditure including specialty drug impact, biosimilar adoption, and pipeline drug launches.

**Input Features:**
- Historical pharmacy PMPM by therapeutic class
- Specialty drug utilization trending (oncology, autoimmune, rare disease)
- FDA drug approval pipeline (next 12 months)
- Biosimilar availability and adoption rates
- Formulary changes and tier movement
- PBM rebate projections
- Step therapy / prior auth program changes
- Gene and cell therapy candidate registry

**Model Considerations:**
- Zero-inflated models for rare specialty drugs
- Scenario modeling for pipeline drug launches (probability-weighted)
- Separate specialty and traditional pharmacy models

---

### UC-SPEND-08: Seasonal & Event-Driven Spend Spikes

**Objective:** Predict cost spikes driven by seasonal patterns, epidemics, benefit design cycles, and catastrophic events.

**Seasonal Patterns:**
| Quarter | Known Drivers |
|---------|--------------|
| Q1 (Jan-Mar) | Deductible reset → utilization surge; flu/RSV season |
| Q2 (Apr-Jun) | Elective procedure scheduling; allergy season |
| Q3 (Jul-Sep) | Summer injuries; heat-related ER visits; new plan year (some groups) |
| Q4 (Oct-Dec) | End-of-year deductible spend-down; holiday ER visits; open enrollment effects |

**Event-Driven:**
- Epidemic surges (COVID variants, flu outbreaks)
- Natural disasters (hurricanes, wildfires, flooding)
- New drug launches (e.g., obesity drugs, gene therapies)
- Regulatory changes (prior auth rule changes, surprise billing)

---

## 6. Use Cases — Premium / Price Planning for Members

### UC-PREM-01: Experience-Based Group Premium Rating

**Objective:** Set renewal premiums for employer groups using credible claims experience blended with manual rates.

**Rating Formula:**
```
Renewal Premium = [Credibility × Experience Rate] + [(1 - Credibility) × Manual Rate]
                  × Trend Factor × Benefit Relativity × Geographic Factor
                  × Admin & Profit Load × Regulatory Adjustments
```

**Input Features:**
- Group's own claims experience (12-24 months)
- Group demographic profile (age-sex factors)
- Group HCC risk score
- Industry SIC code and associated morbidity factors
- Plan design: deductible, copay, coinsurance, OOP max
- Network selection (narrow vs. broad network)
- Group size (credibility determination)
- Medical trend projection
- Provider rate escalation terms
- Pharmacy trend projection
- Admin cost allocation
- Target loss ratio / profit margin
- Historical group retention and lapse data

**ML Enhancement:**
- ML models predict group-specific trend (not just book-of-business average)
- Churn/lapse prediction to adjust for adverse selection at renewal
- Claim shock probability to inform stop-loss pricing
- Competitor pricing intelligence from rate filings

---

### UC-PREM-02: Individual Market (ACA Exchange) Rate Filing

**Objective:** Develop rates for ACA-compliant individual market products meeting metal level AV requirements and single risk pool rules.

**Regulatory Constraints:**
- Modified community rating (age 3:1, tobacco 1.5:1, geography, family size only)
- AV requirements: Bronze 60%, Silver 70%, Gold 80%, Platinum 90%
- MLR minimum: 80%
- Risk adjustment transfers (HHS-HCC model, V08 for 2025)
- Risk corridor considerations

**Input Features:**
- Single risk pool experience (individual + small group in some states)
- Projected membership by metal level and CSR variant
- Risk adjustment transfer estimate (net payer or receiver)
- Induced utilization by metal level (moral hazard adjustment)
- Morbidity shift analysis (risk score trend)
- AV Calculator outputs for plan designs
- Competitive landscape (competitor rate filings, market share)
- Special Enrollment Period (SEP) risk profile

**ML Enhancement:**
- Risk adjustment prediction (predict net RA transfer at enrollment)
- Adverse selection model (predict member risk by plan choice)
- Price elasticity model (how rate change affects enrollment mix)
- Morbidity spiral detection (early warning of adverse selection death spiral)

---

### UC-PREM-03: Medicare Advantage Bid Pricing

**Objective:** Develop MA plan bids (Part C and D) that optimize Star Rating bonuses, risk adjustment revenue, and supplemental benefit design.

**Key Components:**
- Projected FFS cost (base rate from CMS)
- Risk score projection (CMS-HCC V28 transition)
- Medical cost projection (claims experience + trend)
- Part D drug cost projection
- Supplemental benefit design (dental, vision, OTC, fitness)
- Admin cost and profit margin
- Star Rating bonus qualification (4+ stars = 5% bonus)

**ML Applications:**
- Risk score optimization: identify HCC coding gaps to close
- Star Rating prediction: which measures to invest in for rating improvement
- Benefit design optimization: which supplemental benefits drive enrollment vs. cost
- Network adequacy optimization: balance access requirements with unit cost

---

### UC-PREM-04: Member-Level Price Sensitivity & Plan Selection

**Objective:** Predict which plan/tier each member will choose at open enrollment and how price changes affect selection.

**Input Features:**
- Current plan selection and tenure
- Historical plan switching behavior
- Member demographics (age, family size, geography)
- Utilization pattern (high utilizer → Gold/Platinum preference)
- Price difference between metal tiers
- Employer contribution structure
- HSA/HRA availability
- Life events (marriage, birth, job change)
- Competitor plan availability

**Output:**
- Predicted plan distribution at various price points
- Revenue impact of price changes
- Adverse selection risk by pricing scenario
- Optimal price point balancing volume and margin

---

### UC-PREM-05: Actuarial Risk Score Prediction (Prospective)

**Objective:** Predict next-year risk scores for premium rating and risk adjustment revenue estimation.

**Input Features:**
- Current-year HCC risk scores
- Diagnosis code history (24-month lookback)
- Pharmacy-based risk indicators (RxHCC)
- Lab-inferred conditions (when available)
- Coding intensity trends (risk score year-over-year)
- V28 HCC model transition impact
- Provider coding pattern (coder quality by provider)

**Output:**
- Projected risk score by member, group, LOB
- HCC gap closure opportunity (revenue recovery)
- V28 transition impact quantification
- Risk-adjusted PMPM for premium calculations

---

### UC-PREM-06: Network Design & Tiered Pricing

**Objective:** Optimize network composition and tiered pricing to balance cost, access, and member satisfaction.

**Input Features:**
- Provider unit costs (allowed PMPM by provider)
- Provider quality scores (readmission, outcomes, HEDIS)
- Member-provider utilization patterns
- Geographic access standards (time/distance)
- Provider negotiation leverage (market share, substitutability)
- Referral pattern analysis (which PCPs refer to which specialists)
- Steerage effectiveness (how much utilization shifts to preferred tier)

**Output:**
- Optimal network configuration (preferred/standard/out-of-network)
- Tier assignment per provider based on cost-quality score
- Premium differential by network tier
- Projected savings from narrow network vs. broad network
- Member disruption analysis (how many members affected by network changes)

---

### UC-PREM-07: Stop-Loss / Reinsurance Pricing

**Objective:** Price specific and aggregate stop-loss coverage for self-funded groups, and evaluate reinsurance needs for insured products.

**Input Features:**
- Historical large claim frequency and severity distributions
- Group demographic and risk profile
- Known high-cost case inventory (transplant candidates, NICU, cancer)
- Specialty drug pipeline exposure
- Trend factors for large claims (often higher than overall trend)
- Attachment point selection (specific: $100K-$500K; aggregate: 125% of expected)

**ML Enhancement:**
- Large claim probability prediction by member
- Severity distribution fitting (Pareto, log-normal) with ML-refined tails
- Monte Carlo simulation for aggregate loss distribution

---

## 7. Early Warning Signal Framework

### 7.1 Overview

Early warning signals must be detected **30-90 days before** costs materialize in financial statements. The framework operates across three time horizons:

| Horizon | Lead Time | Signal Type | Action Window |
|---------|-----------|-------------|---------------|
| **Immediate** | 0-30 days | Real-time operational alerts | Tactical (UM, CM) |
| **Near-Term** | 30-60 days | Trend acceleration signals | Operational (network, benefits) |
| **Strategic** | 60-90+ days | Structural shift detection | Strategic (pricing, reserves) |

### 7.2 Immediate Signals (0-30 Days)

| Signal | Data Source | Detection Method | Threshold |
|--------|-----------|-----------------|-----------|
| **ER Visit Spike** | Claims/ADT feed | 7-day rolling avg vs. seasonal baseline | >15% deviation |
| **Inpatient Census Surge** | ADT feeds, auth data | Daily census vs. expected | >10% sustained 5+ days |
| **Prior Auth Volume Spike** | UM system | Weekly auth requests by service type | >20% above trailing 4-week avg |
| **High-Cost Rx Starts** | Pharmacy claims | New specialty drug starts per week | Any gene therapy; >10% increase in specialty starts |
| **Provider Billing Anomaly** | Claims | Per-provider daily charge submission | >2 std dev from provider's norm |
| **Call Center Surge** | Call center | Daily call volume + NLP topic clustering | New topic cluster emerging; >25% volume increase |
| **Claim Denial Spike** | Adjudication | Denial rate by category | >5 percentage-point increase |

### 7.3 Near-Term Signals (30-60 Days)

| Signal | Data Source | Detection Method | Threshold |
|--------|-----------|-----------------|-----------|
| **PMPM Trend Acceleration** | Claims (paid lag adjusted) | Month-over-month PMPM change vs. trend | >1% above projected trend |
| **Utilization Rate Shift** | Claims | Admits/1000, visits/1000 by category | >5% deviation from seasonal expectation |
| **Risk Score Drift** | HCC scoring engine | Average risk score shift by cohort | >2% quarterly risk score increase |
| **New Member Risk Profile** | Enrollment + risk scoring | Average risk score of new enrollees vs. existing | New members >10% riskier than existing book |
| **Network Leakage Increase** | Claims (network status) | OON claims as % of total | >2 percentage-point increase |
| **Provider Rate Escalation** | Contract system | Upcoming rate effective dates, terms | Any rate increase >trend assumption |
| **Flu/RSV/COVID Surge** | CDC surveillance + claims | Regional hospitalization rates | CDC alert level + claims confirmation |
| **Large Claim Pipeline** | Case management | Active large cases approaching thresholds | Aggregate large claims >budget |
| **Appeals & Grievance Uptick** | Compliance system | Monthly appeal/grievance volume | >20% increase signals coverage adequacy issue |

### 7.4 Strategic Signals (60-90+ Days)

| Signal | Data Source | Detection Method | Threshold |
|--------|-----------|-----------------|-----------|
| **MLR Trajectory Deviation** | Financial reporting | Rolling 12-month MLR vs. target | Projected MLR > target by >1% |
| **Adverse Selection in ACA Plans** | Enrollment + risk scoring | Metal-level risk score distribution | Silver/Gold risk scores rising vs. pricing assumption |
| **Employer Group Composition Shift** | Enrollment | Large group adds/terms, industry mix change | Any group >5% of book changing |
| **Regulatory / Policy Change** | CMS/state DOI | Rule change impact analysis | V28 HCC transition, surprise billing, PA rule changes |
| **Competitor Market Action** | Public rate filings | Competitor rate changes, market entry/exit | Competitor rate decrease >5% (adverse selection risk) |
| **Drug Pipeline Impact** | FDA, ClinicalTrials.gov | New approval with >$100K annual cost | Any approval with >1000 potential UHC eligible members |
| **Provider Market Consolidation** | Public filings, news | Hospital M&A, practice acquisitions | Any consolidation reducing network leverage |
| **Demographic Shift** | Census, BLS, enrollment | Aging of member base, geographic migration | Average age increase >0.3 years/quarter |
| **Coding Intensity Shift** | HCC scoring | Risk-adjusted cost vs. raw cost divergence | Coding intensity increasing without cost increase |

### 7.5 Early Warning Signal Architecture

```
 DATA SOURCES                    SIGNAL ENGINE                     ACTION LAYER
 ============                    =============                     ============

 Claims (daily)  ───┐
 ADT Feeds       ───┤
 Auth/UM Data    ───┤        ┌──────────────────┐
 Pharmacy Claims ───┼───────►│  Real-Time Stream │──► Immediate Alerts
 Call Center     ───┤        │  Processing       │    (UM/CM teams)
 Provider Data   ───┘        │  (Kafka/Flink)    │
                             └──────────────────┘
                                     │
                                     ▼
 Enrollment      ───┐        ┌──────────────────┐
 Risk Scores     ───┤        │  Batch Analytics  │──► Weekly Trend
 SDOH Data       ───┼───────►│  Engine           │    Reports
 Financial Data  ───┤        │  (Spark/Databricks│    (Actuarial/Finance)
 External Data   ───┘        │   + ML Models)    │
                             └──────────────────┘
                                     │
                                     ▼
 Regulatory      ───┐        ┌──────────────────┐
 Competitor Intel───┤        │  Strategic Signal │──► Quarterly
 Drug Pipeline   ───┼───────►│  Analysis         │    Strategy Reviews
 Market Data     ───┤        │  (Agentic AI +    │    (C-suite, Actuarial)
 Macro-Economic  ───┘        │   LLM Analysis)   │
                             └──────────────────┘

                                     │
                                     ▼
                             ┌──────────────────┐
                             │  UNIFIED SIGNAL   │
                             │  DASHBOARD        │
                             │                   │
                             │  - Signal severity │
                             │  - Financial impact│
                             │  - Recommended     │
                             │    action          │
                             │  - Owner/assignee  │
                             └──────────────────┘
```

### 7.6 Signal Scoring & Prioritization

Each signal is scored on three dimensions:

| Dimension | Weight | Scale | Description |
|-----------|--------|-------|-------------|
| **Financial Impact** | 40% | 1-5 | Estimated $ impact on quarterly spend |
| **Confidence** | 30% | 1-5 | Statistical confidence of signal (p-value, sample size) |
| **Actionability** | 30% | 1-5 | Can intervention change outcome within the quarter? |

**Composite Signal Score** = 0.4 × Impact + 0.3 × Confidence + 0.3 × Actionability

| Score Range | Severity | Response |
|-------------|----------|----------|
| 4.0 - 5.0 | **CRITICAL** | Immediate executive notification; emergency action plan |
| 3.0 - 3.9 | **HIGH** | Within 48 hours; assigned owner, action plan required |
| 2.0 - 2.9 | **MEDIUM** | Weekly review; monitor for escalation |
| 1.0 - 1.9 | **LOW** | Monthly review; informational only |

---

## 8. Architecture & Pipeline Overview

### 8.1 Data Pipeline

```
 ┌─────────────────────────────────────────────────────────────────┐
 │                        DATA INGESTION                           │
 ├─────────────────────────────────────────────────────────────────┤
 │  Claims (837P/I, 835)  │  Enrollment (834)  │  Provider (274)  │
 │  Pharmacy (NCPDP)      │  Auth/UM           │  Call Center     │
 │  Lab/EHR (HL7/FHIR)   │  Financial/GL      │  External APIs   │
 └───────────────────────────────┬─────────────────────────────────┘
                                 │
                                 ▼
 ┌─────────────────────────────────────────────────────────────────┐
 │                     DATA LAKE (Bronze/Silver/Gold)              │
 ├─────────────────────────────────────────────────────────────────┤
 │  Bronze: Raw data (as-is, append-only, full history)           │
 │  Silver: Cleansed, standardized, deduplicated, linked          │
 │  Gold: Business-ready aggregates (PMPM, utilization rates,     │
 │        risk scores, provider profiles, member longitudinal)    │
 └───────────────────────────────┬─────────────────────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
           ┌──────────┐  ┌──────────┐  ┌──────────┐
           │  Feature  │  │  ML Model│  │  Agentic │
           │  Store    │  │  Training│  │  AI      │
           │           │  │  & Serve │  │  Orchestr│
           └──────────┘  └──────────┘  └──────────┘
                    │            │            │
                    └────────────┼────────────┘
                                 ▼
           ┌─────────────────────────────────────┐
           │        OUTPUT / ACTION LAYER         │
           ├─────────────────────────────────────┤
           │  Quarterly Spend Forecasts           │
           │  Premium Rate Recommendations        │
           │  Early Warning Signal Dashboard      │
           │  Provider Anomaly Alerts             │
           │  Actuarial Reserve Adjustments        │
           │  Executive Reporting                  │
           └─────────────────────────────────────┘
```

### 8.2 Key Feature Store Entities

| Entity | Granularity | Key Features | Refresh |
|--------|------------|-------------|---------|
| **Member** | Member-month | Age, sex, risk score, PMPM (allowed/paid), chronic condition flags, utilization counts, SDOH index | Monthly |
| **Provider** | Provider-month | Panel size, PMPM, cost efficiency score, quality score, specialty, denial rate | Monthly |
| **Claim** | Claim-line | Service category, POS, CPT, DRG, ICD-10, allowed, paid, COB, lag days | Daily |
| **Group** | Group-month | Size, industry, demographics, experience PMPM, risk score, retention probability | Monthly |
| **Geography** | ZIP-month | PMPM, provider density, SDOH index, competitor penetration | Monthly |
| **Plan** | Plan-month | Enrollment, AV, PMPM by category, MLR, risk score, trend rate | Monthly |

---

## 9. Model Selection & Evaluation

### 9.1 Model Comparison Matrix

| Use Case | Recommended Model | Baseline | Key Metric | Expected Performance |
|----------|------------------|----------|------------|---------------------|
| Population Spend Forecast | Ensemble (XGBoost + Prophet) | Actuarial trend model | MAPE | <2% at LOB level |
| Service Category Forecast | Hierarchical LightGBM | Historical average + trend | MAPE, reconciliation error | <5% per category |
| High-Cost Member | Two-stage XGBoost | Historical top-decile flag | Recall@10%, Precision@10% | >70% recall top decile |
| IBNR Estimation | ML-enhanced Chain Ladder | Traditional Chain Ladder | Weighted Avg Dev% | <3% deviation at 12-month |
| Provider Anomaly | Isolation Forest + Peer Benchmark | Rule-based thresholds | F1-score, FPR | >80% precision at 20% recall |
| Premium Rating | GLM + GBM hybrid | Traditional GLM | Actual-to-Expected ratio | A/E between 0.97-1.03 |
| Risk Score Prediction | GBM with Rx features | Prior year risk score | R-squared, MAE | R² >0.75 |
| Plan Selection | Multinomial logistic + GBM | Historical distribution | Accuracy, log-loss | >70% accuracy |

### 9.2 Model Governance Requirements

| Requirement | Description |
|-------------|-------------|
| **Explainability** | SHAP/LIME explanations for all member-level predictions; aggregate feature importance for population models |
| **Fairness Audit** | Disparate impact testing across race, ethnicity, gender, disability, geography |
| **Regulatory Compliance** | Actuarial certification for rate-setting models; CMS audit trail for MA/Medicaid models |
| **Model Monitoring** | Drift detection (PSI for features, KS test for predictions); automated retraining triggers |
| **Backtesting** | Walk-forward validation on 8+ quarters of holdout data |
| **Champion-Challenger** | Parallel running of new model vs. incumbent for 2 quarters before promotion |

---

## 10. Implementation Roadmap

### Phase 1: Foundation (Months 1-3)

| Task | Deliverable |
|------|------------|
| Data inventory & quality assessment | Data catalog, quality scorecard |
| Feature store design & initial population | Core member, provider, claim features |
| Baseline models (actuarial trend, simple ML) | Initial PMPM forecasts, HCC predictions |
| IBNR ML-enhancement pilot | ML-enhanced completion factors |
| Early warning signal v1 (rule-based) | Basic threshold alerts for ER, auth, claims |

### Phase 2: Core ML (Months 4-6)

| Task | Deliverable |
|------|------------|
| Population spend forecasting (UC-SPEND-01, 02) | Quarterly forecast by LOB and category |
| High-cost member prediction (UC-SPEND-03) | Top-decile identification with SHAP explanations |
| Premium rating ML-enhancement (UC-PREM-01) | Group-specific trend prediction |
| SDOH data integration | ZIP-level SDOH features in feature store |
| Pharmacy spend model (UC-SPEND-07) | Specialty drug impact forecasting |

### Phase 3: Advanced Analytics (Months 7-9)

| Task | Deliverable |
|------|------------|
| Provider anomaly detection (UC-SPEND-05) | Provider scorecards with anomaly flags |
| Geographic cost variation (UC-SPEND-06) | Rating area factor updates |
| Plan selection prediction (UC-PREM-04) | Enrollment mix forecasting |
| Risk score prediction (UC-PREM-05) | Prospective HCC risk scoring |
| Early warning signal v2 (ML-based) | Automated signal detection with scoring |

### Phase 4: Agentic AI & Optimization (Months 10-12)

| Task | Deliverable |
|------|------------|
| Agentic AI orchestration | Autonomous signal detection, investigation, recommendation |
| Network design optimization (UC-PREM-06) | Optimal tiered network recommendations |
| Stop-loss pricing (UC-PREM-07) | Large claim frequency/severity models |
| MA bid optimization (UC-PREM-03) | Star Rating + benefit design optimization |
| Full early warning dashboard | Unified signal platform with severity scoring |
| Model governance framework | MLOps pipeline, monitoring, fairness audits |

---

## Appendix A: Key Metrics & KPIs

| Metric | Definition | Target |
|--------|-----------|--------|
| PMPM (Per Member Per Month) | Total allowed claims / member months | Forecast within ±2% |
| MLR (Medical Loss Ratio) | Medical costs / premium revenue | 80-85% (LOB-dependent) |
| IBNR Accuracy | Actual vs. estimated IBNR at 6-month runout | Within ±3% |
| High-Cost Capture Rate | % of actual top-decile identified prospectively | >70% |
| Premium Adequacy (A/E) | Actual claims / expected claims at premium-set | 0.97 - 1.03 |
| Forecast MAPE | Mean Absolute Percentage Error of quarterly forecast | <2% LOB, <5% sub-plan |
| Signal Lead Time | Days between signal detection and cost materialization | >45 days average |
| Signal Precision | % of triggered signals that were valid | >75% |
| Model Drift | PSI score for feature and prediction drift | PSI <0.1 (stable) |

## Appendix B: Regulatory Considerations

| Regulation | Impact | Data Requirement |
|-----------|--------|-----------------|
| ACA MLR (80/85% rule) | Must spend 80-85% of premiums on medical care | Accurate cost and premium allocation |
| ACA Rate Review | Rate increases >15% trigger federal review | Actuarial justification for trend assumptions |
| CMS Risk Adjustment | HHS-HCC V08 for 2025; net-zero transfers | Accurate diagnosis coding and risk scoring |
| CMS V28 HCC Transition | New risk model reducing some condition payments | Re-calibrated risk scores |
| State CON Laws | Certificate of Need limits facility supply | Provider access and cost modeling |
| No Surprises Act | Limits surprise out-of-network billing | OON cost reduction, IDR process costs |
| Mental Health Parity | Behavioral health benefits must be equivalent | BH cost trending, access measurement |
| Transparency Rules | Price transparency, machine-readable files | Negotiated rate data management |
| HIPAA | PHI protection in all analytics | De-identification, minimum necessary, BAAs |

---

*Document Version: 1.0 | Created: February 24, 2026 | Classification: Internal — Confidential*
*For UnitedHealthcare Actuarial, Finance, Data Science, and Product teams*
