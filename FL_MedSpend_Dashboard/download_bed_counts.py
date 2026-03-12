"""
Download hospital bed count data from CMS (Centers for Medicare & Medicaid Services).

Source: CMS Provider of Services (POS) File — Q4 2025
  Contains 423 columns per facility including bed counts by type,
  accreditation, ownership, staffing, and services.

Run:
    python download_bed_counts.py

Output:
    data/florida_hospital_beds.csv  — clean Florida hospital bed data
"""

import sys
import pandas as pd
import requests
from io import StringIO
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "data"

# -----------------------------------------------------------------------
# CMS Provider of Services (POS) File — Hospital & Other Facilities
# Updated quarterly.  Direct CSV from data.cms.gov / catalog.data.gov
# -----------------------------------------------------------------------
POS_URLS = [
    # Q4 2025 (latest as of Mar 2026)
    "https://data.cms.gov/sites/default/files/2026-01/"
    "c500f848-83b3-4f29-a677-562243a2f23b/Hospital_and_other.DATA.Q4_2025.csv",
    # Q3 2025 (fallback)
    "https://data.cms.gov/sites/default/files/2025-12/"
    "bba35b60-e5ba-4660-8d0a-c9703192eca3/Hospital_and_other.DATA.Q3_2025.csv",
    # Q2 2025 (fallback)
    "https://data.cms.gov/sites/default/files/2025-08/"
    "ab6b6f06-c7e6-49f1-a93d-c4564dfa394f/Hospital_and_Other_data_Q2_2025.csv",
]

COLUMNS_TO_KEEP = [
    "PRVDR_NUM",               # CMS Certification Number
    "FAC_NAME",                # Facility name
    "ST_ADR",                  # Street address
    "CITY_NAME",               # City
    "STATE_CD",                # State code (2-letter)
    "ZIP_CD",                  # Zip code
    "FIPS_CNTY_CD",            # FIPS county code
    "SSA_CNTY_CD",             # SSA county code
    "PHNE_NUM",                # Phone number
    "GNRL_FAC_TYPE_CD",        # General facility type code
    "GNRL_CNTL_TYPE_CD",       # Ownership/control type code
    "PRVDR_CTGRY_CD",          # Provider category code
    "PRVDR_CTGRY_SBTYP_CD",    # Provider category subtype
    "CRTFCTN_DT",              # Certification date
    "ORGNL_PRTCPTN_DT",       # Original participation date
    "ACRDTN_TYP",              # Accreditation type
    "BED_CNT",                 # Total bed count
    "CRTFD_BED_CNT",           # Certified bed count
    "PSYCH_UNIT_BED_CNT",      # Psychiatric unit beds
    "REHAB_UNIT_BED_CNT",      # Rehab unit beds
    "REHAB_BED_CNT",           # Rehab beds
    "HOSPC_BED_CNT",           # Hospice beds
    "DLYS_BED_CNT",            # Dialysis beds
    "AIDS_BED_CNT",            # AIDS beds
    "ALZHMR_BED_CNT",          # Alzheimer beds
    "VNTLTR_BED_CNT",          # Ventilator beds
    "HEAD_TRMA_BED_CNT",       # Head trauma beds
    "DSBL_CHLDRN_BED_CNT",     # Disabled children beds
    "MDCR_SNF_BED_CNT",        # Medicare SNF beds
    "MDCR_MDCD_SNF_BED_CNT",   # Medicare/Medicaid SNF beds
    "MDCD_NF_BED_CNT",         # Medicaid NF beds
    "ICFIID_BED_CNT",          # ICF/IID beds
    "MLT_FAC_ORG_NAME",        # Multi-facility org name (system name)
    "CBSA_URBN_RRL_IND",       # Urban/rural indicator
    "CBSA_CD",                 # Core-based statistical area code
]

FRIENDLY_NAMES = {
    "PRVDR_NUM": "cms_provider_id",
    "FAC_NAME": "facility_name",
    "ST_ADR": "address",
    "CITY_NAME": "city",
    "STATE_CD": "state",
    "ZIP_CD": "zip_code",
    "FIPS_CNTY_CD": "fips_county",
    "SSA_CNTY_CD": "ssa_county",
    "PHNE_NUM": "phone",
    "GNRL_FAC_TYPE_CD": "facility_type_code",
    "GNRL_CNTL_TYPE_CD": "ownership_code",
    "PRVDR_CTGRY_CD": "provider_category",
    "PRVDR_CTGRY_SBTYP_CD": "provider_subtype",
    "CRTFCTN_DT": "certification_date",
    "ORGNL_PRTCPTN_DT": "participation_date",
    "ACRDTN_TYP": "accreditation_type",
    "BED_CNT": "total_beds",
    "CRTFD_BED_CNT": "certified_beds",
    "PSYCH_UNIT_BED_CNT": "psych_beds",
    "REHAB_UNIT_BED_CNT": "rehab_unit_beds",
    "REHAB_BED_CNT": "rehab_beds",
    "HOSPC_BED_CNT": "hospice_beds",
    "DLYS_BED_CNT": "dialysis_beds",
    "AIDS_BED_CNT": "aids_beds",
    "ALZHMR_BED_CNT": "alzheimer_beds",
    "VNTLTR_BED_CNT": "ventilator_beds",
    "HEAD_TRMA_BED_CNT": "head_trauma_beds",
    "DSBL_CHLDRN_BED_CNT": "disabled_children_beds",
    "MDCR_SNF_BED_CNT": "medicare_snf_beds",
    "MDCR_MDCD_SNF_BED_CNT": "medicare_medicaid_snf_beds",
    "MDCD_NF_BED_CNT": "medicaid_nf_beds",
    "ICFIID_BED_CNT": "icf_iid_beds",
    "MLT_FAC_ORG_NAME": "health_system_name",
    "CBSA_URBN_RRL_IND": "urban_rural",
    "CBSA_CD": "cbsa_code",
}

OWNERSHIP_LABELS = {
    "01": "Non-profit - Church",
    "02": "Non-profit - Private",
    "03": "Non-profit - Other",
    "04": "For-profit - Individual",
    "05": "For-profit - Partnership",
    "06": "For-profit - Corporation",
    "07": "For-profit - LLC",
    "08": "For-profit - Subchapter S Corp",
    "09": "For-profit - Other",
    "10": "Government - State",
    "11": "Government - County",
    "12": "Government - City",
    "13": "Government - Hospital District",
}

FACILITY_TYPE_LABELS = {
    "1": "Hospital",
    "2": "Skilled Nursing Facility",
    "3": "Home Health Agency",
    "4": "Other",
}

ACCREDITATION_LABELS = {
    "1": "Joint Commission (JC)",
    "2": "American Osteopathic Assoc (AOA)",
    "4": "DNV Healthcare",
    "5": "CIHQ",
    "6": "HFAP",
}


def download_pos_file() -> pd.DataFrame:
    """Download the CMS POS file, trying multiple quarterly URLs."""
    print("=" * 65)
    print("  CMS Hospital Bed Count Downloader — Florida")
    print("=" * 65)
    print()

    for i, url in enumerate(POS_URLS):
        label = url.split("/")[-1]
        print(f"[{i+1}/{len(POS_URLS)}] Trying {label}...")
        try:
            resp = requests.get(url, timeout=180)
            resp.raise_for_status()
            print(f"  -> Downloaded ({len(resp.content) / 1e6:.1f} MB)")
            df = pd.read_csv(StringIO(resp.text), low_memory=False, dtype=str)
            print(f"  -> {len(df):,} facility records nationwide, {len(df.columns)} columns")
            return df
        except requests.exceptions.RequestException as e:
            print(f"  -> Failed: {e}")
            continue

    print("\nERROR: All download URLs failed.")
    print("Manual download: visit https://data.cms.gov and search 'Provider of Services'")
    sys.exit(1)


def process_florida_hospitals(df: pd.DataFrame) -> pd.DataFrame:
    """Filter to Florida, select and rename columns, add labels."""
    print("\nProcessing Florida hospitals...")

    fl = df[df["STATE_CD"].str.strip() == "FL"].copy()
    print(f"  -> {len(fl):,} Florida facility records")

    available = [c for c in COLUMNS_TO_KEEP if c in fl.columns]
    missing = [c for c in COLUMNS_TO_KEEP if c not in fl.columns]
    if missing:
        print(f"  -> Note: {len(missing)} columns not in file: {missing}")

    fl = fl[available].copy()

    rename_map = {c: FRIENDLY_NAMES[c] for c in available if c in FRIENDLY_NAMES}
    fl = fl.rename(columns=rename_map)

    bed_cols = [c for c in fl.columns if c.endswith("_beds") or c == "total_beds"]
    for col in bed_cols:
        fl[col] = pd.to_numeric(fl[col], errors="coerce").fillna(0).astype(int)

    # Only keep records with at least 1 bed (filters out labs, clinics, etc.)
    hospitals = fl[fl["total_beds"] > 0].copy()
    clinics = fl[fl["total_beds"] == 0].copy()
    print(f"  -> {len(hospitals):,} facilities with beds (hospitals/SNFs/rehab)")
    print(f"  -> {len(clinics):,} facilities with 0 beds (clinics/labs — excluded)")

    if "ownership_code" in hospitals.columns:
        hospitals["ownership_type"] = hospitals["ownership_code"].map(OWNERSHIP_LABELS).fillna("Unknown")

    if "facility_type_code" in hospitals.columns:
        hospitals["facility_type"] = hospitals["facility_type_code"].map(FACILITY_TYPE_LABELS).fillna("Other")

    if "accreditation_type" in hospitals.columns:
        hospitals["accreditation"] = hospitals["accreditation_type"].map(ACCREDITATION_LABELS).fillna("None/Other")

    hospitals = hospitals.sort_values("total_beds", ascending=False).reset_index(drop=True)

    return hospitals


def save_results(df: pd.DataFrame):
    """Save to CSV and print summary."""
    OUTPUT_DIR.mkdir(exist_ok=True)

    out_path = OUTPUT_DIR / "florida_hospital_beds.csv"
    df.to_csv(out_path, index=False)
    print(f"\nSaved: {out_path}  ({len(df):,} rows)")

    print(f"\n{'='*65}")
    print("  TOP 25 FLORIDA HOSPITALS BY BED COUNT")
    print(f"{'='*65}")

    display_cols = ["facility_name", "city", "total_beds", "certified_beds"]
    for optional in ["psych_beds", "rehab_beds", "ownership_type", "facility_type", "accreditation"]:
        if optional in df.columns:
            display_cols.append(optional)

    top = df.head(25)
    for i, row in top.iterrows():
        print(f"\n  {i+1:>2}. {row['facility_name']}")
        print(f"      City: {row['city']}  |  Total Beds: {row['total_beds']}  |  Certified: {row['certified_beds']}")
        extras = []
        if "psych_beds" in row and row["psych_beds"] > 0:
            extras.append(f"Psych: {row['psych_beds']}")
        if "rehab_beds" in row and row["rehab_beds"] > 0:
            extras.append(f"Rehab: {row['rehab_beds']}")
        if "ownership_type" in row:
            extras.append(f"Ownership: {row['ownership_type']}")
        if "accreditation" in row:
            extras.append(f"Accreditation: {row['accreditation']}")
        if extras:
            print(f"      {' | '.join(extras)}")

    print(f"\n{'='*65}")
    print("  SUMMARY STATISTICS")
    print(f"{'='*65}")
    print(f"  Total facilities with beds: {len(df):,}")
    print(f"  Total beds in Florida:      {df['total_beds'].sum():,}")
    print(f"  Avg beds per facility:      {df['total_beds'].mean():.0f}")
    print(f"  Median beds:                {df['total_beds'].median():.0f}")
    print(f"  Max beds (single facility): {df['total_beds'].max():,}")

    if "facility_type" in df.columns:
        print(f"\n  By facility type:")
        for ftype, group in df.groupby("facility_type"):
            print(f"    {ftype}: {len(group):,} facilities, {group['total_beds'].sum():,} beds")

    if "ownership_type" in df.columns:
        print(f"\n  By ownership:")
        for otype, group in df.groupby("ownership_type"):
            print(f"    {otype}: {len(group):,} facilities, {group['total_beds'].sum():,} beds")

    print(f"\n  By city (top 10):")
    city_beds = df.groupby("city")["total_beds"].agg(["count", "sum"]).sort_values("sum", ascending=False)
    for city, row in city_beds.head(10).iterrows():
        print(f"    {city}: {int(row['count'])} facilities, {int(row['sum']):,} beds")


def main():
    raw = download_pos_file()
    hospitals = process_florida_hospitals(raw)
    save_results(hospitals)
    print("\nDone!")


if __name__ == "__main__":
    main()
