"""
UCHI Cost Decomposition Engine
Decomposes total cost change into Utilization, Unit Cost, Mix, and Intensity.
"""

import pandas as pd
import numpy as np


def compute_period_metrics(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    """Aggregate claims to period-level metrics for a given grouping."""
    agg = df.groupby(group_cols).agg(
        total_allowed=("allowed_amount", "sum"),
        total_paid=("paid_amount", "sum"),
        total_units=("total_units", "sum"),
        member_months=("member_months", "first"),
        avg_rvu=("rvu_total", "mean"),
    ).reset_index()

    agg["utilization_per_1000"] = agg["total_units"] / agg["member_months"] * 1000
    agg["unit_cost"] = np.where(agg["total_units"] > 0,
                                agg["total_allowed"] / agg["total_units"], 0)
    agg["pmpm"] = agg["total_allowed"] / agg["member_months"]
    return agg


def uchi_decomposition_by_category(df: pd.DataFrame,
                                    period_col: str = "year",
                                    base_period=2024,
                                    current_period=2025) -> pd.DataFrame:
    """
    Decompose YoY cost change by category into U, C, H (mix), I (intensity).

    Returns one row per category with:
      - total_change: absolute $ PMPM change
      - utilization_effect: portion due to volume change
      - unit_cost_effect: portion due to price change
      - mix_effect: portion due to category share shift
      - intensity_effect: portion due to code complexity shift
    """
    base = df[df[period_col] == base_period]
    curr = df[df[period_col] == current_period]

    base_cat = base.groupby("category").agg(
        allowed=("allowed_amount", "sum"),
        units=("total_units", "sum"),
        mm=("member_months", "first"),
        avg_rvu=("rvu_total", "mean"),
    ).reset_index()

    curr_cat = curr.groupby("category").agg(
        allowed=("allowed_amount", "sum"),
        units=("total_units", "sum"),
        mm=("member_months", "first"),
        avg_rvu=("rvu_total", "mean"),
    ).reset_index()

    merged = base_cat.merge(curr_cat, on="category", suffixes=("_b", "_c"))

    total_allowed_b = merged["allowed_b"].sum()
    total_allowed_c = merged["allowed_c"].sum()
    total_mm_b = merged["mm_b"].iloc[0]
    total_mm_c = merged["mm_c"].iloc[0]

    merged["pmpm_b"] = merged["allowed_b"] / total_mm_b
    merged["pmpm_c"] = merged["allowed_c"] / total_mm_c
    merged["util_b"] = merged["units_b"] / total_mm_b * 1000
    merged["util_c"] = merged["units_c"] / total_mm_c * 1000
    merged["uc_b"] = np.where(merged["units_b"] > 0, merged["allowed_b"] / merged["units_b"], 0)
    merged["uc_c"] = np.where(merged["units_c"] > 0, merged["allowed_c"] / merged["units_c"], 0)
    merged["mix_b"] = merged["allowed_b"] / total_allowed_b
    merged["mix_c"] = merged["allowed_c"] / total_allowed_c

    merged["total_change"] = merged["pmpm_c"] - merged["pmpm_b"]
    merged["utilization_effect"] = (merged["util_c"] - merged["util_b"]) / 1000 * merged["uc_b"]
    merged["unit_cost_effect"] = merged["util_b"] / 1000 * (merged["uc_c"] - merged["uc_b"])
    merged["mix_effect"] = (merged["mix_c"] - merged["mix_b"]) * (total_allowed_b / total_mm_b)
    merged["intensity_effect"] = (merged["avg_rvu_c"] - merged["avg_rvu_b"]) * merged["uc_b"] * merged["util_b"] / 1000

    merged["utilization_pct"] = np.where(
        merged["pmpm_b"] > 0,
        (merged["util_c"] / merged["util_b"] - 1) * 100, 0
    )
    merged["unit_cost_pct"] = np.where(
        merged["uc_b"] > 0,
        (merged["uc_c"] / merged["uc_b"] - 1) * 100, 0
    )
    merged["intensity_pct"] = np.where(
        merged["avg_rvu_b"] > 0,
        (merged["avg_rvu_c"] / merged["avg_rvu_b"] - 1) * 100, 0
    )

    return merged


def cpt_level_yoy(df: pd.DataFrame, base_year=2024, curr_year=2025,
                   group_cols=None) -> pd.DataFrame:
    """
    Compute YoY changes at the CPT level, optionally grouped by state/plan.

    Returns each CPT with base/current utilization, cost, and % changes.
    """
    if group_cols is None:
        group_cols = []

    key = ["cpt_code", "category", "subcategory"] + group_cols

    base = df[df["year"] == base_year].groupby(key).agg(
        allowed=("allowed_amount", "sum"),
        units=("total_units", "sum"),
        mm=("member_months", "first"),
        avg_rvu=("rvu_total", "mean"),
        national_benchmark=("national_benchmark", "first"),
        description=("cpt_description", "first"),
    ).reset_index()

    curr = df[df["year"] == curr_year].groupby(key).agg(
        allowed=("allowed_amount", "sum"),
        units=("total_units", "sum"),
        mm=("member_months", "first"),
        avg_rvu=("rvu_total", "mean"),
    ).reset_index()

    m = base.merge(curr, on=key[:3] + group_cols, suffixes=("_b", "_c"), how="outer")
    for col in ["allowed_b", "allowed_c", "units_b", "units_c"]:
        m[col] = m[col].fillna(0)
    m["mm_b"] = m["mm_b"].fillna(m["mm_c"])
    m["mm_c"] = m["mm_c"].fillna(m["mm_b"])

    m["util_b"] = m["units_b"] / m["mm_b"].clip(lower=1) * 1000
    m["util_c"] = m["units_c"] / m["mm_c"].clip(lower=1) * 1000
    m["uc_b"] = np.where(m["units_b"] > 0, m["allowed_b"] / m["units_b"], 0)
    m["uc_c"] = np.where(m["units_c"] > 0, m["allowed_c"] / m["units_c"], 0)
    m["pmpm_b"] = m["allowed_b"] / m["mm_b"].clip(lower=1)
    m["pmpm_c"] = m["allowed_c"] / m["mm_c"].clip(lower=1)

    m["allowed_change"] = m["allowed_c"] - m["allowed_b"]
    m["allowed_change_pct"] = np.where(m["allowed_b"] > 0,
                                        m["allowed_change"] / m["allowed_b"] * 100, 0)
    m["util_change_pct"] = np.where(m["util_b"] > 0,
                                     (m["util_c"] / m["util_b"] - 1) * 100, 0)
    m["uc_change_pct"] = np.where(m["uc_b"] > 0,
                                   (m["uc_c"] / m["uc_b"] - 1) * 100, 0)

    m["benchmark_deviation_pct"] = np.where(
        m["national_benchmark"].fillna(0) > 0,
        (m["uc_c"] / m["national_benchmark"] - 1) * 100, 0
    )

    return m.sort_values("allowed_change", ascending=False)


def cost_waterfall(df: pd.DataFrame, top_n=15, base_year=2024, curr_year=2025) -> pd.DataFrame:
    """
    Top N CPTs contributing to absolute cost increase, for waterfall chart.
    """
    yoy = cpt_level_yoy(df, base_year, curr_year)
    top = yoy.nlargest(top_n, "allowed_change")[
        ["cpt_code", "description", "category", "allowed_change", "allowed_change_pct",
         "util_change_pct", "uc_change_pct"]
    ].reset_index(drop=True)
    return top
