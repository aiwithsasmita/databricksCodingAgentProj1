"""
CMS Physician Fee Schedule Scraper & Lookup

Downloads official CMS PFS data (indicators + localities) for 2023, 2024, 2025
from pfs.data.cms.gov DKAN API. Computes state-level fee schedules by applying
Geographic Practice Cost Index (GPCI) adjustments to national RVU-based payments.

Data is at the YEAR level (CMS publishes one fee schedule per calendar year,
sometimes with mid-year revisions — we use the latest revision for each year).

Usage:
    from cms_pfs_scraper import CMSFeeSchedule

    pfs = CMSFeeSchedule()           # downloads & caches on first use
    pfs.download_all()                # force re-download

    # Single lookup
    result = pfs.lookup("99213", year=2024, state="FL")

    # Batch lookup from dict
    query = {
        "99213": {"years": [2023, 2024, 2025], "states": ["FL", "CA", "TX"]},
        "27447": {"years": [2024], "states": ["NY"]},
    }
    df = pfs.batch_lookup(query)
    df.to_csv("my_fee_schedule.csv", index=False)
"""

import os
import json
import pandas as pd
import requests
from io import StringIO
from pathlib import Path
from typing import Optional

DATA_DIR = Path(__file__).parent / "data"

# ── CMS PFS data URLs (from pfs.data.cms.gov DKAN catalog) ──────────
# Indicators: CPT-level RVUs, conversion factor, national totals
# Localities: GPCI adjustments per locality (maps to states)
PFS_SOURCES = {
    2023: {
        "indicators": "https://pfs.data.cms.gov/sites/default/files/data/indicators2023-09-28.csv",
        "localities": "https://pfs.data.cms.gov/sites/default/files/data/localities2023-06-20.csv",
        "conv_factor": 33.8872,
    },
    2024: {
        "indicators": "https://pfs.data.cms.gov/sites/default/files/data/indicators2024B-09-18-2024.csv",
        "localities": "https://pfs.data.cms.gov/sites/default/files/data/localities2024B.csv",
        "conv_factor": 33.2875,
    },
    2025: {
        "indicators": "https://pfs.data.cms.gov/sites/default/files/data/indicators2025-09-23-2025.csv",
        "localities": "https://pfs.data.cms.gov/sites/default/files/data/localities2025.csv",
        "conv_factor": 32.3465,
    },
}

# ── Locality-to-State mapping ────────────────────────────────────────
# CMS uses locality codes, not state abbreviations. Each state has one
# or more localities. We map the "rest of state" locality to each state
# abbreviation. For states with multiple localities (e.g., CA, TX, NY),
# we pick the largest/most representative one.
# Source: CMS PFS Locality Configuration document
STATE_LOCALITY_MAP = {
    "AL": "01",   "AK": "02",   "AZ": "03",   "AR": "04",   "CA": "18",
    "CO": "06",   "CT": "07",   "DE": "08",   "DC": "09",   "FL": "10",
    "GA": "11",   "HI": "12",   "ID": "13",   "IL": "16",   "IN": "15",
    "IA": "14",   "KS": "17",   "KY": "19",   "LA": "20",   "ME": "21",
    "MD": "22",   "MA": "23",   "MI": "24",   "MN": "25",   "MS": "26",
    "MO": "27",   "MT": "28",   "NE": "29",   "NV": "30",   "NH": "31",
    "NJ": "32",   "NM": "33",   "NY": "36",   "NC": "37",   "ND": "38",
    "OH": "39",   "OK": "40",   "OR": "41",   "PA": "42",   "RI": "44",
    "SC": "45",   "SD": "46",   "TN": "47",   "TX": "48",   "UT": "49",
    "VT": "50",   "VA": "51",   "WA": "53",   "WV": "54",   "WI": "55",
    "WY": "56",   "PR": "72",   "VI": "78",   "GU": "66",   "AS": "60",
}


class CMSFeeSchedule:
    """Download and query CMS Physician Fee Schedule data."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._indicators = {}
        self._localities = {}
        self._locality_state_map = {}

    # ── Download ─────────────────────────────────────────────────────

    def download_all(self, years: list[int] = None):
        """Download indicators and localities CSVs for specified years."""
        if years is None:
            years = list(PFS_SOURCES.keys())

        for year in years:
            if year not in PFS_SOURCES:
                print(f"  [SKIP] Year {year} not available (have {list(PFS_SOURCES.keys())})")
                continue
            self._download_year(year)

        self._build_locality_state_map()

    def _download_year(self, year: int):
        src = PFS_SOURCES[year]

        for ftype in ["indicators", "localities"]:
            cache_path = self.data_dir / f"pfs_{ftype}_{year}.csv"
            url = src[ftype]

            if cache_path.exists():
                print(f"  [CACHE] {cache_path.name} already exists")
                df = pd.read_csv(cache_path, low_memory=False)
            else:
                print(f"  [DOWNLOAD] {ftype} {year} from CMS ...")
                resp = requests.get(url, timeout=120)
                resp.raise_for_status()
                df = pd.read_csv(StringIO(resp.text), low_memory=False)
                df.to_csv(cache_path, index=False)
                print(f"    -> Saved {cache_path.name} ({len(df):,} rows)")

            if ftype == "indicators":
                self._indicators[year] = df
            else:
                self._localities[year] = df

    def _ensure_loaded(self, year: int):
        if year not in self._indicators:
            self._download_year(year)
            self._build_locality_state_map()

    def _build_locality_state_map(self):
        """Build a mapping from (year, state) -> best-matching locality row."""
        for year, loc_df in self._localities.items():
            loc_df = loc_df.copy()
            loc_col = "locality"
            desc_col = "loc_description"

            if loc_col not in loc_df.columns:
                continue

            loc_df[loc_col] = loc_df[loc_col].astype(str).str.strip()
            loc_df[desc_col] = loc_df[desc_col].astype(str).str.upper()

            for state_abbr, state_code in STATE_LOCALITY_MAP.items():
                matches = loc_df[loc_df[desc_col].str.contains(f"REST OF {state_abbr}", na=False)]
                if matches.empty:
                    matches = loc_df[loc_df[loc_col].str.startswith(state_code)]
                if matches.empty:
                    matches = loc_df[loc_df[desc_col].str.contains(state_abbr, na=False)]
                if not matches.empty:
                    self._locality_state_map[(year, state_abbr)] = matches.iloc[-1]

    # ── Lookup ───────────────────────────────────────────────────────

    def lookup(self, cpt_code: str, year: int = 2024,
               state: str = None, modifier: str = None) -> dict:
        """
        Look up fee schedule for a single CPT code.

        Args:
            cpt_code: CPT/HCPCS code (e.g., "99213")
            year: Calendar year (2023, 2024, or 2025)
            state: State abbreviation (e.g., "FL"). None = national.
            modifier: CPT modifier (e.g., "26", "TC"). None = global.

        Returns:
            dict with rvu_work, rvu_pe, rvu_mp, rvu_total, conv_factor,
            national_payment_facility, national_payment_nonfacility,
            state_payment_facility, state_payment_nonfacility, gpci_*
        """
        self._ensure_loaded(year)
        ind = self._indicators[year]
        conv_factor = PFS_SOURCES[year]["conv_factor"]

        mask = ind["hcpc"].astype(str).str.strip() == str(cpt_code).strip()
        if modifier:
            mask &= ind["modifier"].astype(str).str.strip() == str(modifier).strip()
        else:
            mask &= ind["modifier"].isna() | (ind["modifier"].astype(str).str.strip() == "")

        rows = ind[mask]
        if rows.empty:
            if modifier:
                mask_any = ind["hcpc"].astype(str).str.strip() == str(cpt_code).strip()
                rows = ind[mask_any]
            if rows.empty:
                return {"error": f"CPT {cpt_code} not found in {year} PFS"}

        row = rows.iloc[0]
        def _best(row, *cols):
            """Pick the first non-zero value from multiple column candidates."""
            for c in cols:
                v = _safe_float(row.get(c))
                if v != 0.0:
                    return v
            return 0.0

        result = {
            "cpt_code": cpt_code,
            "year": year,
            "description": str(row.get("sdesc", "")),
            "modifier": modifier or "Global",
            "status": str(row.get("proc_stat", "")),
            "rvu_work": _safe_float(row.get("rvu_work")),
            "rvu_pe_nonfacility": _best(row, "full_nfac_pe", "trans_nfac_pe", "nfac_pe"),
            "rvu_pe_facility": _best(row, "full_fac_pe", "trans_fac_pe", "fac_pe"),
            "rvu_mp": _safe_float(row.get("rvu_mp")),
            "rvu_total_nonfacility": _best(row, "full_nfac_total", "trans_nfac_total", "nfac_total"),
            "rvu_total_facility": _best(row, "full_fac_total", "trans_fac_total", "fac_total"),
            "conversion_factor": conv_factor,
            "global_period": str(row.get("global", "")),
        }

        rvu_nf = result["rvu_total_nonfacility"]
        rvu_f = result["rvu_total_facility"]
        result["national_payment_nonfacility"] = round(rvu_nf * conv_factor, 2)
        result["national_payment_facility"] = round(rvu_f * conv_factor, 2)

        if state:
            gpci = self._get_gpci(year, state)
            result["state"] = state
            result["gpci_work"] = gpci.get("gpci_work", 1.0)
            result["gpci_pe"] = gpci.get("gpci_pe", 1.0)
            result["gpci_mp"] = gpci.get("gpci_mp", 1.0)
            result["locality"] = gpci.get("locality", "")
            result["locality_description"] = gpci.get("loc_description", "")

            adj_nf = (
                result["rvu_work"] * gpci["gpci_work"] +
                result["rvu_pe_nonfacility"] * gpci["gpci_pe"] +
                result["rvu_mp"] * gpci["gpci_mp"]
            ) * conv_factor
            adj_f = (
                result["rvu_work"] * gpci["gpci_work"] +
                result["rvu_pe_facility"] * gpci["gpci_pe"] +
                result["rvu_mp"] * gpci["gpci_mp"]
            ) * conv_factor

            result["state_payment_nonfacility"] = round(adj_nf, 2)
            result["state_payment_facility"] = round(adj_f, 2)
        else:
            result["state"] = "National"

        return result

    def _get_gpci(self, year: int, state: str) -> dict:
        key = (year, state.upper())
        if key in self._locality_state_map:
            row = self._locality_state_map[key]
            return {
                "gpci_work": _safe_float(row.get("gpci_work", 1.0)),
                "gpci_pe": _safe_float(row.get("gpci_pe", 1.0)),
                "gpci_mp": _safe_float(row.get("gpci_mp", 1.0)),
                "locality": str(row.get("locality", "")),
                "loc_description": str(row.get("loc_description", "")),
            }
        return {"gpci_work": 1.0, "gpci_pe": 1.0, "gpci_mp": 1.0,
                "locality": "0", "loc_description": "NATIONAL (state not found)"}

    # ── Batch lookup ─────────────────────────────────────────────────

    def batch_lookup(self, query: dict) -> pd.DataFrame:
        """
        Batch lookup from a dictionary.

        Args:
            query: {
                "99213": {"years": [2023, 2024, 2025], "states": ["FL", "CA"]},
                "27447": {"years": [2024], "states": ["TX", "NY"]},
            }

        Returns:
            DataFrame with one row per (cpt_code, year, state) combination.
        """
        results = []
        total = sum(
            len(v.get("years", [2024])) * len(v.get("states", [None]))
            for v in query.values()
        )
        done = 0

        for cpt_code, params in query.items():
            years = params.get("years", [2024])
            states = params.get("states", [None])
            modifier = params.get("modifier", None)

            for year in years:
                for state in states:
                    r = self.lookup(cpt_code, year=year, state=state, modifier=modifier)
                    results.append(r)
                    done += 1

        df = pd.DataFrame(results)
        if "error" in df.columns:
            errors = df[df["error"].notna()]
            if len(errors) > 0:
                print(f"\n  WARNING: {len(errors)} lookups returned errors:")
                for _, e in errors.head(5).iterrows():
                    print(f"    {e['error']}")

        return df

    def get_all_cpts(self, year: int = 2024) -> pd.DataFrame:
        """Get all CPT codes available in a given year's PFS."""
        self._ensure_loaded(year)
        ind = self._indicators[year]
        return ind[["hcpc", "sdesc", "rvu_work", "nfac_total", "fac_total"]].drop_duplicates("hcpc")


def _safe_float(val, default=0.0) -> float:
    try:
        v = float(val)
        if pd.isna(v):
            return default
        return v
    except (ValueError, TypeError):
        return default


# ═══════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════

def main():
    print("=" * 65)
    print("  CMS Physician Fee Schedule Scraper")
    print("=" * 65)

    pfs = CMSFeeSchedule()
    pfs.download_all()

    print("\n" + "=" * 65)
    print("  Sample Lookups")
    print("=" * 65)

    sample_query = {
        "99213": {"years": [2023, 2024, 2025], "states": ["FL", "CA", "TX", "NY"]},
        "99214": {"years": [2023, 2024, 2025], "states": ["FL", "CA", "TX", "NY"]},
        "27447": {"years": [2024, 2025], "states": ["FL", "NY"]},
        "99285": {"years": [2024], "states": ["FL", "CA"]},
        "45380": {"years": [2024], "states": ["FL", "TX"]},
        "66984": {"years": [2024, 2025], "states": ["FL"]},
        "77067": {"years": [2024], "states": ["FL", "CA", "NY"]},
    }

    df = pfs.batch_lookup(sample_query)

    display_cols = [
        "cpt_code", "year", "state", "description",
        "rvu_work", "rvu_total_nonfacility", "conversion_factor",
        "national_payment_nonfacility", "national_payment_facility",
    ]
    state_cols = ["state_payment_nonfacility", "state_payment_facility",
                  "gpci_work", "gpci_pe", "gpci_mp"]
    show = [c for c in display_cols + state_cols if c in df.columns]

    out_path = pfs.data_dir / "sample_fee_schedule.csv"
    df.to_csv(out_path, index=False)
    print(f"\nSaved full results: {out_path}")

    print("\n  Sample results (non-facility payment):\n")
    for _, row in df.head(20).iterrows():
        if "error" in row and pd.notna(row.get("error")):
            continue
        nat = row.get("national_payment_nonfacility", 0)
        st_pay = row.get("state_payment_nonfacility", "")
        st = row.get("state", "")
        print(f"  CPT {row['cpt_code']}  {row['year']}  {st:>2s}  "
              f"Natl=${nat:>8.2f}  State=${st_pay if st_pay else 'N/A':>8}  "
              f"RVU={row.get('rvu_total_nonfacility',0):.2f}  "
              f"'{row.get('description','')[:40]}'")

    print(f"\n  Total rows: {len(df)}")
    print("  Done!")


if __name__ == "__main__":
    main()
