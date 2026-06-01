"""
Generate synthetic CPT-level claims data across 10 states, Medicare/Medicaid/Dual,
36 months (Jan 2023 – Dec 2025) with realistic utilization, cost, mix, and
intensity patterns including seasonality, trend, and state-level variation.
"""

import pandas as pd
import numpy as np

from .cpt_reference import get_cpt_reference, get_states_reference

np.random.seed(2024)

# ── State-level cost multipliers (geographic price variation) ─────────
STATE_COST_FACTOR = {
    "FL": 1.00, "CA": 1.22, "TX": 0.92, "NY": 1.30, "PA": 1.05,
    "IL": 1.02, "OH": 0.94, "GA": 0.91, "AZ": 0.97, "NJ": 1.18,
}

# ── Plan-type multipliers ────────────────────────────────────────────
PLAN_COST_FACTOR = {"Medicare": 1.00, "Medicaid": 0.72, "Dual": 1.15}
PLAN_UTIL_FACTOR = {"Medicare": 1.00, "Medicaid": 0.85, "Dual": 1.40}

# ── Category-level annual growth rates ───────────────────────────────
CATEGORY_GROWTH = {
    "E&M": 0.045,
    "Surgery": 0.035,
    "Radiology": 0.030,
    "Lab": 0.020,
    "Medicine": 0.055,
    "Anesthesia": 0.032,
    "DME/Supply": 0.025,
    "Behavioral Health": 0.085,
}

# ── CPT-level "hot" codes (injected trend acceleration for realism) ──
HOT_CPTS = {
    "G2211": 0.15,
    "99443": 0.12,
    "J9271": 0.10,
    "J1300": 0.12,
    "90837": 0.09,
    "67028": 0.08,
    "J2507": 0.07,
    "99490": 0.08,
    "81479": 0.11,
    "J2350": 0.09,
    "33361": 0.06,
    "92928": 0.05,
    "J0517": 0.10,
    "96413": 0.06,
}

PLACE_OF_SERVICE = {
    "E&M": {"Office": 0.55, "Inpatient": 0.25, "ER": 0.10, "ASC": 0.0, "Telehealth": 0.10},
    "Surgery": {"Office": 0.05, "Inpatient": 0.50, "ER": 0.0, "ASC": 0.35, "Telehealth": 0.0, "Other": 0.10},
    "Radiology": {"Office": 0.35, "Inpatient": 0.30, "ER": 0.10, "ASC": 0.15, "Telehealth": 0.0, "Other": 0.10},
    "Lab": {"Office": 0.50, "Inpatient": 0.20, "ER": 0.10, "ASC": 0.0, "Telehealth": 0.0, "Other": 0.20},
    "Medicine": {"Office": 0.50, "Inpatient": 0.20, "ER": 0.05, "ASC": 0.10, "Telehealth": 0.05, "Other": 0.10},
    "Anesthesia": {"Office": 0.0, "Inpatient": 0.55, "ER": 0.05, "ASC": 0.35, "Telehealth": 0.0, "Other": 0.05},
    "DME/Supply": {"Office": 0.30, "Inpatient": 0.10, "ER": 0.0, "ASC": 0.0, "Telehealth": 0.0, "Other": 0.60},
    "Behavioral Health": {"Office": 0.50, "Inpatient": 0.15, "ER": 0.05, "ASC": 0.0, "Telehealth": 0.25, "Other": 0.05},
}


def _seasonal_factor(month: int) -> float:
    """Healthcare utilization seasonal curve: peaks in Q1 (flu) and dip in summer."""
    return 1.0 + 0.06 * np.cos(2 * np.pi * (month - 1) / 12)


def _pick_pos(category: str) -> str:
    pos_dist = PLACE_OF_SERVICE.get(category, {"Office": 0.6, "Inpatient": 0.2, "Other": 0.2})
    labels = list(pos_dist.keys())
    probs = np.array(list(pos_dist.values()))
    probs = probs / probs.sum()
    return np.random.choice(labels, p=probs)


def generate_cpt_claims() -> pd.DataFrame:
    """
    Generate monthly aggregated CPT-level claims data.

    Returns a DataFrame with one row per (month, state, plan_type, cpt_code)
    containing utilization, cost, and intensity metrics.
    """
    cpt_ref = get_cpt_reference()
    states = get_states_reference()
    months = pd.date_range("2023-01-01", "2025-12-31", freq="MS")
    plan_types = ["Medicare", "Medicaid", "Dual"]

    rows = []

    for month in months:
        month_idx = (month.year - 2023) * 12 + month.month - 1
        seasonal = _seasonal_factor(month.month)

        for _, state in states.iterrows():
            st = state["abbr"]
            st_cost = STATE_COST_FACTOR.get(st, 1.0)

            for plan in plan_types:
                if plan == "Medicare":
                    member_months = int(state["population"] * state["medicare_pct"] / 12)
                elif plan == "Medicaid":
                    member_months = int(state["population"] * state["medicaid_pct"] / 12)
                else:
                    member_months = int(state["population"] * min(state["medicare_pct"], state["medicaid_pct"]) * 0.15 / 12)

                member_months = max(1000, member_months)

                plan_cost = PLAN_COST_FACTOR[plan]
                plan_util = PLAN_UTIL_FACTOR[plan]

                for _, cpt in cpt_ref.iterrows():
                    base_util_rate = cpt["annual_utilization_per_1000"] / 12

                    cat_growth = CATEGORY_GROWTH.get(cpt["category"], 0.03)
                    hot_growth = HOT_CPTS.get(cpt["cpt_code"], 0.0)
                    total_annual_growth = cat_growth + hot_growth

                    growth_factor = (1 + total_annual_growth) ** (month_idx / 12)
                    noise = np.random.lognormal(0, 0.10)

                    util_rate = base_util_rate * plan_util * seasonal * growth_factor * noise
                    util_rate = max(0.001, util_rate)

                    total_units = max(1, int(util_rate * member_months / 1000))

                    base_cost = cpt["national_avg_allowed"]
                    if base_cost <= 0:
                        base_cost = max(3, cpt["rvu_total"] * 36.0)

                    unit_cost_noise = np.random.lognormal(0, 0.06)
                    unit_cost = base_cost * st_cost * plan_cost * unit_cost_noise
                    unit_cost *= (1 + cat_growth * 0.4) ** (month_idx / 12)

                    allowed = round(unit_cost * total_units, 2)
                    billed = round(allowed * np.random.uniform(1.6, 2.8), 2)
                    paid = round(allowed * np.random.uniform(0.80, 0.95), 2)
                    member_share = round(allowed - paid, 2)

                    pos = _pick_pos(cpt["category"])

                    rows.append({
                        "month": month,
                        "year": month.year,
                        "quarter": f"Q{(month.month - 1) // 3 + 1}",
                        "state": st,
                        "plan_type": plan,
                        "member_months": member_months,
                        "cpt_code": cpt["cpt_code"],
                        "cpt_description": cpt["description"],
                        "category": cpt["category"],
                        "subcategory": cpt["subcategory"],
                        "rvu_work": cpt["rvu_work"],
                        "rvu_total": cpt["rvu_total"],
                        "national_benchmark": cpt["national_avg_allowed"],
                        "place_of_service": pos,
                        "total_units": total_units,
                        "unit_cost": round(unit_cost, 2),
                        "allowed_amount": allowed,
                        "billed_amount": billed,
                        "paid_amount": paid,
                        "member_cost_share": member_share,
                        "utilization_per_1000": round(total_units / member_months * 1000, 4),
                        "pmpm": round(allowed / member_months, 4),
                    })

    df = pd.DataFrame(rows)
    return df


def generate_enrollment_summary() -> pd.DataFrame:
    """Generate monthly member enrollment counts per state/plan."""
    states = get_states_reference()
    months = pd.date_range("2023-01-01", "2025-12-31", freq="MS")
    rows = []
    for month in months:
        growth = 1 + 0.005 * ((month.year - 2023) * 12 + month.month - 1) / 12
        for _, state in states.iterrows():
            for plan, pct_key in [("Medicare", "medicare_pct"), ("Medicaid", "medicaid_pct")]:
                mm = int(state["population"] * state[pct_key] / 12 * growth)
                rows.append({
                    "month": month, "state": state["abbr"],
                    "plan_type": plan, "member_months": mm,
                })
            dual_mm = int(state["population"] * min(state["medicare_pct"], state["medicaid_pct"]) * 0.15 / 12 * growth)
            rows.append({
                "month": month, "state": state["abbr"],
                "plan_type": "Dual", "member_months": dual_mm,
            })
    return pd.DataFrame(rows)
