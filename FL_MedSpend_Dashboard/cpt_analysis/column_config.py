"""
Column Mapping Configuration for Real Data Integration.

When you're ready to plug in your real claims CSV:
  1. Set DATA_PATH to your CSV file path
  2. Map your column names to the expected names in COLUMN_MAP
  3. The data generator will auto-detect this config and use your data

If DATA_PATH is None, the app uses synthetic dummy data.
"""

DATA_PATH = None  # e.g. r"D:\data\claims_2025.csv"

# Map YOUR column names (left) to the EXPECTED names (right).
# Only include columns whose names differ from the expected.
COLUMN_MAP = {
    # "YOUR_COLUMN":        "expected_column",
    # "PROC_CD":            "cpt_code",
    # "PROC_DESC":          "cpt_description",
    # "SVC_CTGRY":          "category",
    # "SVC_SUBCTGRY":       "subcategory",
    # "ALWD_AMT":           "allowed_amount",
    # "PD_AMT":             "paid_amount",
    # "BILLED_AMT":         "billed_amount",
    # "MBR_CST_SHR":        "member_cost_share",
    # "SVC_UNITS":          "total_units",
    # "SVC_DT":             "month",
    # "ST_CD":              "state",
    # "PLAN_TYP":           "plan_type",
    # "MBR_MONTHS":         "member_months",
    # "UNIT_CST":           "unit_cost",
    # "UTIL_PER_1K":        "utilization_per_1000",
    # "RVU_WRK":            "rvu_work",
    # "RVU_TOT":            "rvu_total",
    # "NATL_BNCHMRK":       "national_benchmark",
    # "POS":                "place_of_service",
}

EXPECTED_COLUMNS = [
    "month", "year", "quarter", "state", "plan_type", "member_months",
    "cpt_code", "cpt_description", "category", "subcategory",
    "rvu_work", "rvu_total", "national_benchmark", "place_of_service",
    "total_units", "unit_cost", "allowed_amount", "billed_amount",
    "paid_amount", "member_cost_share", "utilization_per_1000", "pmpm",
]
