# CMS Physician Fee Schedule Scraper

Download and query official **Medicare Physician Fee Schedule (PFS)** data from CMS for 2023, 2024, and 2025. Returns CPT-level payment amounts adjusted by state using Geographic Practice Cost Index (GPCI).

## Data Source

All data is scraped from the **official CMS (Centers for Medicare & Medicaid Services)** public data portal:

| Source | URL | What It Contains |
|--------|-----|------------------|
| PFS Data Portal | https://pfs.data.cms.gov | DKAN-based open data catalog |
| DKAN Catalog API | https://pfs.data.cms.gov/api/1/metastore/schemas/dataset/items | Dataset discovery endpoint |
| Indicators CSV | `pfs.data.cms.gov/sites/default/files/data/indicators{YEAR}.csv` | CPT-level RVUs, conversion factor, payment indicators |
| Localities CSV | `pfs.data.cms.gov/sites/default/files/data/localities{YEAR}.csv` | GPCI adjustments per geographic locality |

### Specific Files Downloaded

| Year | Indicators File | Localities File | Conversion Factor |
|------|----------------|-----------------|-------------------|
| 2023 | `indicators2023-09-28.csv` (18,178 CPTs) | `localities2023-06-20.csv` (113 localities) | $33.8872 |
| 2024 | `indicators2024B-09-18-2024.csv` (18,696 CPTs) | `localities2024B.csv` (110 localities) | $33.2875 |
| 2025 | `indicators2025-09-23-2025.csv` (19,090 CPTs) | `localities2025.csv` (110 localities) | $32.3465 |

> **Note on 2024:** CMS published two fee schedule revisions in 2024 (A and B). We use **2024B** (effective March 9 - December 31, 2024) which reflects the updated conversion factor of $33.2875 per the Consolidated Appropriations Act.

### Data Frequency

The CMS Physician Fee Schedule is published at the **calendar year level** (not monthly). CMS issues one fee schedule per year via the annual PFS Final Rule, with occasional mid-year revisions.

---

## How Medicare Payment Is Calculated

### The Formula

```
Medicare Payment = (Work RVU x Work GPCI + PE RVU x PE GPCI + MP RVU x MP GPCI) x Conversion Factor
```

### Key Terms

| Term | Full Name | Meaning |
|------|-----------|---------|
| **CPT / HCPCS** | Current Procedural Terminology / Healthcare Common Procedure Coding System | 5-character code identifying a medical service (e.g., 99213 = office visit) |
| **RVU** | Relative Value Unit | A measure of the resources required to provide a service. Higher RVU = more complex/expensive. Three components: Work, Practice Expense, Malpractice |
| **Work RVU** | — | Physician time, skill, and intensity required |
| **PE RVU** | Practice Expense RVU | Overhead costs (staff, equipment, supplies). Has two variants: **Facility** (hospital setting, lower PE) and **Non-Facility** (office setting, higher PE because the physician bears the overhead) |
| **MP RVU** | Malpractice RVU | Professional liability insurance cost component |
| **Total RVU** | — | Work + PE + MP. Two values: Facility Total and Non-Facility Total |
| **GPCI** | Geographic Practice Cost Index | Adjusts RVUs for local cost differences. Each CMS locality has three GPCIs (Work, PE, MP). A GPCI > 1.0 means costs are above national average |
| **Conversion Factor (CF)** | — | Dollar amount per RVU. Set annually by CMS Final Rule. Converts RVUs to dollars |
| **Facility** | — | Services performed in a hospital, ASC, or SNF. Lower PE because the facility bears the overhead |
| **Non-Facility** | — | Services performed in a physician office. Higher PE because the physician bears the overhead |
| **Locality** | — | CMS geographic area (109 total). Each state has one "rest of state" locality plus optional metro-specific localities (e.g., Manhattan, San Francisco) |
| **Modifier** | — | 2-character code modifying a CPT. Common: **26** (professional component only), **TC** (technical component only), **Global** (both combined) |

### Example Calculation

CPT **99213** (Office visit, established patient, low complexity) in **Florida**, 2024:

| Component | RVU | GPCI (FL) | Adjusted |
|-----------|-----|-----------|----------|
| Work | 1.30 | 1.000 | 1.300 |
| PE (Non-Facility) | 1.33 | 0.940 | 1.250 |
| Malpractice | 0.10 | 1.467 | 0.147 |
| **Total** | **2.73** | — | **2.697** |

Payment = 2.697 x $33.2875 = **$89.77**

---

## Output Columns

Each lookup returns a dictionary (or DataFrame row) with these 23 fields:

| Column | Type | Description |
|--------|------|-------------|
| `cpt_code` | str | CPT/HCPCS code queried |
| `year` | int | Calendar year (2023, 2024, or 2025) |
| `state` | str | State abbreviation or "National" |
| `description` | str | Short CMS description of the service |
| `modifier` | str | CPT modifier (26, TC) or "Global" |
| `status` | str | CMS status indicator (A=Active, R=Restricted, I=Invalid, etc.) |
| `rvu_work` | float | Work RVU |
| `rvu_pe_nonfacility` | float | Practice Expense RVU for office setting |
| `rvu_pe_facility` | float | Practice Expense RVU for hospital setting |
| `rvu_mp` | float | Malpractice RVU |
| `rvu_total_nonfacility` | float | Total RVU for office (Work + PE NonFac + MP) |
| `rvu_total_facility` | float | Total RVU for hospital (Work + PE Fac + MP) |
| `conversion_factor` | float | CMS conversion factor for that year |
| `global_period` | str | Global surgery period (000, 010, 090, XXX) |
| `national_payment_nonfacility` | float | National payment in office setting ($) |
| `national_payment_facility` | float | National payment in hospital setting ($) |
| `state_payment_nonfacility` | float | GPCI-adjusted payment in office setting ($) |
| `state_payment_facility` | float | GPCI-adjusted payment in hospital setting ($) |
| `gpci_work` | float | Work GPCI for the state |
| `gpci_pe` | float | Practice Expense GPCI for the state |
| `gpci_mp` | float | Malpractice GPCI for the state |
| `locality` | str | CMS locality code used |
| `locality_description` | str | CMS locality description (e.g., "REST OF FLORIDA") |

---

## Installation

```bash
pip install pandas requests
```

Or:

```bash
pip install -r requirements.txt
```

## Quick Start

### Command Line

```bash
python cms_pfs_scraper.py
```

This downloads all 2023-2025 data from CMS, runs sample lookups, and saves results to `data/sample_fee_schedule.csv`.

### Python API

```python
from cms_pfs_scraper import CMSFeeSchedule

pfs = CMSFeeSchedule()
pfs.download_all()  # downloads and caches CSV files in data/
```

#### Single Lookup

```python
result = pfs.lookup("99213", year=2024, state="FL")
print(result)
# {
#   'cpt_code': '99213',
#   'year': 2024,
#   'state': 'FL',
#   'description': 'Office o/p est low 20 min',
#   'rvu_work': 1.3,
#   'rvu_total_nonfacility': 2.73,
#   'national_payment_nonfacility': 90.87,
#   'state_payment_nonfacility': 89.77,
#   'gpci_work': 1.0,
#   'gpci_pe': 0.94,
#   ...
# }
```

#### Batch Lookup (Dictionary Format)

Pass a dictionary where keys are CPT codes and values specify years and states:

```python
query = {
    "99213": {"years": [2023, 2024, 2025], "states": ["FL", "CA", "TX", "NY"]},
    "99214": {"years": [2024, 2025], "states": ["FL", "NY"]},
    "27447": {"years": [2024], "states": ["FL", "CA", "TX"]},
    "45380": {"years": [2024, 2025], "states": ["FL"]},
}

df = pfs.batch_lookup(query)
df.to_csv("my_fee_schedule.csv", index=False)
print(df[["cpt_code", "year", "state", "national_payment_nonfacility", "state_payment_nonfacility"]])
```

#### With Modifier

```python
# Professional component only (modifier 26)
result = pfs.lookup("77067", year=2024, state="FL", modifier="26")
```

#### Get All Available CPTs

```python
all_cpts = pfs.get_all_cpts(year=2024)
print(f"Total CPTs in 2024 PFS: {len(all_cpts)}")
```

---

## Caching

Downloaded CSVs are cached in the `data/` directory:

```
data/
  pfs_indicators_2023.csv   (3.5 MB, 18,178 rows)
  pfs_indicators_2024.csv   (3.3 MB, 18,696 rows)
  pfs_indicators_2025.csv   (3.3 MB, 19,090 rows)
  pfs_localities_2023.csv   (7 KB, 113 localities)
  pfs_localities_2024.csv   (7 KB, 110 localities)
  pfs_localities_2025.csv   (7 KB, 110 localities)
```

On subsequent runs, the script reads from cache. Delete a CSV to force re-download.

---

## Data Verification

All scraped values were cross-checked against official CMS sources:

| Check | Result |
|-------|--------|
| Conversion Factors (2023/2024/2025) | Exact match to CMS Final Rule |
| Work RVU for 9 key CPTs | 9/9 match |
| GPCI National (1.0, 1.0, 1.0) | Exact match |
| GPCI Florida PE (0.940) | Exact match |
| 99213 FL 2024 Payment ($89.77) | Exact match to manual calculation |
| 27447 FL 2024 Payment ($1,316.36) | Verified correct |
| Data completeness (10K+ active CPTs/year) | Confirmed |

---

## Locality-to-State Mapping

CMS uses ~110 locality codes, not state abbreviations. States with multiple localities (e.g., California has San Francisco, Los Angeles, Rest of CA) are mapped to their "Rest of State" locality by default — this is the most representative rate for statewide analysis.

For metro-specific rates, use the `lookup()` method with the CMS locality code directly via the raw data files.

---

## Project Structure

```
CMS_FeeSchedule_Scraper/
  cms_pfs_scraper.py      # Main scraper and CMSFeeSchedule class
  requirements.txt        # Python dependencies
  README.md               # This file
  data/                   # Auto-created, cached CMS CSV downloads
    pfs_indicators_2023.csv
    pfs_indicators_2024.csv
    pfs_indicators_2025.csv
    pfs_localities_2023.csv
    pfs_localities_2024.csv
    pfs_localities_2025.csv
    sample_fee_schedule.csv
```

---

## References

- [CMS Physician Fee Schedule Overview](https://www.cms.gov/medicare/payment/fee-schedules/physician)
- [PFS Search Tool](https://www.cms.gov/medicare/physician-fee-schedule/search)
- [PFS Data Portal (DKAN)](https://pfs.data.cms.gov)
- [PFS Relative Value Files](https://www.cms.gov/Medicare/Medicare-Fee-for-Service-Payment/PhysicianFeeSched/PFS-Relative-Value-Files)
- [PFS Locality Configuration](https://www.cms.gov/medicare/payment/fee-schedules/physician/locality-configuration)
- [CY 2025 PFS Final Rule](https://www.cms.gov/newsroom/fact-sheets/calendar-year-cy-2025-medicare-physician-fee-schedule-final-rule)
