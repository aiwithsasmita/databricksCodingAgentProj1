import pandas as pd
import numpy as np
from datetime import datetime, timedelta

np.random.seed(42)

FLORIDA_PROVIDERS = [
    {"name": "AdventHealth Orlando", "npi": "1234567890", "region": "Central", "county": "Orange", "type": "Hospital System", "bed_count": 1368},
    {"name": "Baptist Health South Florida", "npi": "1234567891", "region": "Southeast", "county": "Miami-Dade", "type": "Hospital System", "bed_count": 1500},
    {"name": "Tampa General Hospital", "npi": "1234567892", "region": "West", "county": "Hillsborough", "type": "Hospital System", "bed_count": 1041},
    {"name": "UF Health Shands Hospital", "npi": "1234567893", "region": "North", "county": "Alachua", "type": "Academic Medical Center", "bed_count": 973},
    {"name": "Mayo Clinic Jacksonville", "npi": "1234567894", "region": "Northeast", "county": "Duval", "type": "Academic Medical Center", "bed_count": 304},
    {"name": "Cleveland Clinic Florida", "npi": "1234567895", "region": "Southeast", "county": "Broward", "type": "Hospital System", "bed_count": 206},
    {"name": "Moffitt Cancer Center", "npi": "1234567896", "region": "West", "county": "Hillsborough", "type": "Specialty Center", "bed_count": 206},
    {"name": "Jackson Memorial Hospital", "npi": "1234567897", "region": "Southeast", "county": "Miami-Dade", "type": "Hospital System", "bed_count": 1550},
    {"name": "Lee Health", "npi": "1234567898", "region": "Southwest", "county": "Lee", "type": "Hospital System", "bed_count": 1592},
    {"name": "Orlando Health", "npi": "1234567899", "region": "Central", "county": "Orange", "type": "Hospital System", "bed_count": 1956},
    {"name": "Memorial Healthcare System", "npi": "1234567900", "region": "Southeast", "county": "Broward", "type": "Hospital System", "bed_count": 1900},
    {"name": "Sarasota Memorial Hospital", "npi": "1234567901", "region": "Southwest", "county": "Sarasota", "type": "Hospital System", "bed_count": 839},
    {"name": "NCH Healthcare System", "npi": "1234567902", "region": "Southwest", "county": "Collier", "type": "Hospital System", "bed_count": 716},
    {"name": "HCA Florida JFK Hospital", "npi": "1234567903", "region": "Southeast", "county": "Palm Beach", "type": "Hospital System", "bed_count": 424},
    {"name": "Tallahassee Memorial HealthCare", "npi": "1234567904", "region": "North", "county": "Leon", "type": "Hospital System", "bed_count": 772},
    {"name": "Ascension Sacred Heart Pensacola", "npi": "1234567905", "region": "Northwest", "county": "Escambia", "type": "Hospital System", "bed_count": 566},
    {"name": "Halifax Health Daytona", "npi": "1234567906", "region": "Central", "county": "Volusia", "type": "Hospital System", "bed_count": 678},
    {"name": "Broward Health Medical Center", "npi": "1234567907", "region": "Southeast", "county": "Broward", "type": "Hospital System", "bed_count": 716},
    {"name": "Palm Beach Gardens Medical Center", "npi": "1234567908", "region": "Southeast", "county": "Palm Beach", "type": "Hospital System", "bed_count": 199},
    {"name": "Nemours Children's Hospital", "npi": "1234567909", "region": "Central", "county": "Orange", "type": "Specialty Center", "bed_count": 130},
    {"name": "Bascom Palmer Eye Institute", "npi": "1234567910", "region": "Southeast", "county": "Miami-Dade", "type": "Specialty Center", "bed_count": 25},
    {"name": "Jupiter Medical Center", "npi": "1234567911", "region": "Southeast", "county": "Palm Beach", "type": "Hospital System", "bed_count": 327},
    {"name": "Martin Health System", "npi": "1234567912", "region": "Southeast", "county": "Martin", "type": "Hospital System", "bed_count": 336},
    {"name": "Lakeland Regional Health", "npi": "1234567913", "region": "Central", "county": "Polk", "type": "Hospital System", "bed_count": 892},
    {"name": "Baptist Medical Center Jacksonville", "npi": "1234567914", "region": "Northeast", "county": "Duval", "type": "Hospital System", "bed_count": 534},
    {"name": "St. Joseph's Hospital Tampa", "npi": "1234567915", "region": "West", "county": "Hillsborough", "type": "Hospital System", "bed_count": 929},
    {"name": "Northwest Florida Dermatology", "npi": "1234567916", "region": "Northwest", "county": "Okaloosa", "type": "Specialty Clinic", "bed_count": 0},
    {"name": "Florida Cancer Specialists", "npi": "1234567917", "region": "West", "county": "Pinellas", "type": "Specialty Clinic", "bed_count": 0},
    {"name": "Skin & Cancer Associates", "npi": "1234567918", "region": "Southeast", "county": "Miami-Dade", "type": "Specialty Clinic", "bed_count": 0},
    {"name": "Florida Orthopedic Institute", "npi": "1234567919", "region": "West", "county": "Hillsborough", "type": "Specialty Clinic", "bed_count": 0},
    {"name": "South Florida Cardiology", "npi": "1234567920", "region": "Southeast", "county": "Broward", "type": "Specialty Clinic", "bed_count": 0},
    {"name": "Gulf Coast Neurology", "npi": "1234567921", "region": "Southwest", "county": "Lee", "type": "Specialty Clinic", "bed_count": 0},
    {"name": "Central FL Pulmonary Group", "npi": "1234567922", "region": "Central", "county": "Orange", "type": "Specialty Clinic", "bed_count": 0},
    {"name": "Sunshine State GI Associates", "npi": "1234567923", "region": "Central", "county": "Seminole", "type": "Specialty Clinic", "bed_count": 0},
    {"name": "Palm Beach Mental Health Center", "npi": "1234567924", "region": "Southeast", "county": "Palm Beach", "type": "Specialty Clinic", "bed_count": 0},
    {"name": "Florida Maternal-Fetal Medicine", "npi": "1234567925", "region": "Central", "county": "Orange", "type": "Specialty Clinic", "bed_count": 0},
    {"name": "Bay Area Renal Associates", "npi": "1234567926", "region": "West", "county": "Pinellas", "type": "Specialty Clinic", "bed_count": 0},
    {"name": "Space Coast Endocrinology", "npi": "1234567927", "region": "Central", "county": "Brevard", "type": "Specialty Clinic", "bed_count": 0},
    {"name": "Treasure Coast Rheumatology", "npi": "1234567928", "region": "Southeast", "county": "St. Lucie", "type": "Specialty Clinic", "bed_count": 0},
    {"name": "Panhandle Surgical Associates", "npi": "1234567929", "region": "Northwest", "county": "Bay", "type": "Specialty Clinic", "bed_count": 0},
]

CLINICAL_CLUSTERS = {
    "Oncology / Cancer": {"avg_cost": 85000, "std": 45000, "prevalence": 0.035, "growth_rate": 1.06, "color": "#E74C3C"},
    "Dermatology / Skin": {"avg_cost": 8500, "std": 6000, "prevalence": 0.12, "growth_rate": 1.04, "color": "#F39C12"},
    "Cardiovascular": {"avg_cost": 52000, "std": 30000, "prevalence": 0.065, "growth_rate": 1.05, "color": "#E91E63"},
    "Orthopedic / MSK": {"avg_cost": 35000, "std": 20000, "prevalence": 0.08, "growth_rate": 1.04, "color": "#3498DB"},
    "Neurological": {"avg_cost": 42000, "std": 25000, "prevalence": 0.04, "growth_rate": 1.07, "color": "#9B59B6"},
    "Respiratory / Pulmonary": {"avg_cost": 28000, "std": 15000, "prevalence": 0.055, "growth_rate": 1.03, "color": "#1ABC9C"},
    "Gastrointestinal": {"avg_cost": 22000, "std": 12000, "prevalence": 0.07, "growth_rate": 1.03, "color": "#2ECC71"},
    "Behavioral Health": {"avg_cost": 15000, "std": 10000, "prevalence": 0.09, "growth_rate": 1.08, "color": "#8E44AD"},
    "Maternity / OB-GYN": {"avg_cost": 18000, "std": 8000, "prevalence": 0.025, "growth_rate": 1.02, "color": "#FF69B4"},
    "Renal / Nephrology": {"avg_cost": 65000, "std": 35000, "prevalence": 0.022, "growth_rate": 1.05, "color": "#D35400"},
    "Endocrine / Diabetes": {"avg_cost": 12000, "std": 7000, "prevalence": 0.11, "growth_rate": 1.06, "color": "#16A085"},
    "Autoimmune / Rheumatology": {"avg_cost": 30000, "std": 18000, "prevalence": 0.03, "growth_rate": 1.09, "color": "#C0392B"},
}

CLUSTER_PROVIDER_MAP = {
    "Oncology / Cancer": [0, 1, 2, 3, 4, 5, 6, 7, 9, 10, 17, 27],
    "Dermatology / Skin": [0, 1, 9, 10, 16, 26, 28],
    "Cardiovascular": [0, 1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 14, 20, 30],
    "Orthopedic / MSK": [0, 1, 2, 3, 8, 9, 10, 11, 13, 25, 29],
    "Neurological": [0, 1, 2, 3, 4, 7, 9, 10, 14, 21, 31],
    "Respiratory / Pulmonary": [0, 1, 2, 3, 7, 8, 9, 10, 15, 16, 32],
    "Gastrointestinal": [0, 1, 2, 3, 7, 8, 9, 10, 11, 12, 23, 33],
    "Behavioral Health": [0, 1, 3, 7, 9, 10, 14, 15, 34],
    "Maternity / OB-GYN": [0, 1, 2, 7, 8, 9, 10, 13, 19, 35],
    "Renal / Nephrology": [0, 1, 2, 3, 7, 8, 9, 10, 36],
    "Endocrine / Diabetes": [0, 1, 2, 3, 8, 9, 10, 12, 22, 37],
    "Autoimmune / Rheumatology": [0, 1, 3, 4, 5, 9, 10, 38],
}

FLORIDA_REGIONS = {
    "Southeast": {"population_share": 0.30, "counties": ["Miami-Dade", "Broward", "Palm Beach", "Martin", "St. Lucie"]},
    "Central": {"population_share": 0.25, "counties": ["Orange", "Seminole", "Volusia", "Polk", "Brevard"]},
    "West": {"population_share": 0.18, "counties": ["Hillsborough", "Pinellas"]},
    "Southwest": {"population_share": 0.10, "counties": ["Lee", "Collier", "Sarasota"]},
    "Northeast": {"population_share": 0.08, "counties": ["Duval"]},
    "North": {"population_share": 0.05, "counties": ["Alachua", "Leon"]},
    "Northwest": {"population_share": 0.04, "counties": ["Escambia", "Okaloosa", "Bay"]},
}


def generate_monthly_dates(start="2023-01-01", end="2025-12-31"):
    return pd.date_range(start=start, end=end, freq="MS")


def generate_claims_data():
    months = generate_monthly_dates()
    rows = []

    for month in months:
        month_idx = (month.year - 2023) * 12 + month.month - 1
        seasonal_factor = 1.0 + 0.08 * np.sin(2 * np.pi * (month.month - 3) / 12)

        for cluster_name, cluster_info in CLINICAL_CLUSTERS.items():
            provider_indices = CLUSTER_PROVIDER_MAP[cluster_name]

            yearly_growth = cluster_info["growth_rate"] ** (month_idx / 12)

            for pidx in provider_indices:
                provider = FLORIDA_PROVIDERS[pidx]
                region = provider["region"]
                region_pop = FLORIDA_REGIONS[region]["population_share"]

                base_members = int(12000 * region_pop * cluster_info["prevalence"])
                member_count = max(5, int(base_members * (1 + np.random.normal(0, 0.15))))
                member_count = int(member_count * yearly_growth)

                claims_per_member = max(1, np.random.poisson(2.5))
                claim_count = member_count * claims_per_member

                avg_paid = cluster_info["avg_cost"] / 12
                noise = np.random.normal(1.0, 0.12)
                total_paid = max(1000, avg_paid * member_count * seasonal_factor * yearly_growth * noise)

                allowed_amount = total_paid * np.random.uniform(1.15, 1.35)
                billed_amount = allowed_amount * np.random.uniform(1.8, 2.5)
                member_cost_share = total_paid * np.random.uniform(0.08, 0.20)
                pmpm = total_paid / max(1, member_count)

                high_cost_count = max(0, int(member_count * np.random.uniform(0.01, 0.04)))
                high_cost_amount = high_cost_count * cluster_info["avg_cost"] * np.random.uniform(1.5, 3.0) / 12

                admits_per_1000 = np.random.uniform(3, 25) if provider["bed_count"] > 0 else 0
                er_visits_per_1000 = np.random.uniform(15, 80)
                readmission_rate = np.random.uniform(0.05, 0.18)
                avg_los = np.random.uniform(2, 8) if provider["bed_count"] > 0 else 0
                risk_score = np.random.uniform(0.8, 2.5)

                rows.append({
                    "month": month,
                    "year": month.year,
                    "quarter": f"Q{(month.month - 1) // 3 + 1}",
                    "provider_name": provider["name"],
                    "npi": provider["npi"],
                    "provider_type": provider["type"],
                    "region": region,
                    "county": provider["county"],
                    "bed_count": provider["bed_count"],
                    "clinical_cluster": cluster_name,
                    "member_count": member_count,
                    "claim_count": claim_count,
                    "total_paid": round(total_paid, 2),
                    "allowed_amount": round(allowed_amount, 2),
                    "billed_amount": round(billed_amount, 2),
                    "member_cost_share": round(member_cost_share, 2),
                    "pmpm": round(pmpm, 2),
                    "high_cost_claimants": high_cost_count,
                    "high_cost_amount": round(high_cost_amount, 2),
                    "admits_per_1000": round(admits_per_1000, 2),
                    "er_visits_per_1000": round(er_visits_per_1000, 2),
                    "readmission_rate": round(readmission_rate, 4),
                    "avg_length_of_stay": round(avg_los, 2),
                    "avg_risk_score": round(risk_score, 3),
                })

    return pd.DataFrame(rows)


def generate_prediction_data(df):
    future_months = pd.date_range(start="2026-01-01", end="2026-12-31", freq="MS")
    cluster_trends = df.groupby(["clinical_cluster", "month"])["total_paid"].sum().reset_index()

    prediction_rows = []
    for cluster_name, cluster_info in CLINICAL_CLUSTERS.items():
        cluster_data = cluster_trends[cluster_trends["clinical_cluster"] == cluster_name].sort_values("month")
        if len(cluster_data) < 6:
            continue

        recent_avg = cluster_data["total_paid"].tail(6).mean()

        for fm in future_months:
            seasonal = 1.0 + 0.08 * np.sin(2 * np.pi * (fm.month - 3) / 12)
            growth = cluster_info["growth_rate"] ** (1 / 12)
            predicted = recent_avg * growth * seasonal

            prediction_rows.append({
                "month": fm,
                "clinical_cluster": cluster_name,
                "predicted_paid": round(predicted, 2),
                "lower_bound": round(predicted * 0.85, 2),
                "upper_bound": round(predicted * 1.15, 2),
                "is_prediction": True,
            })

    return pd.DataFrame(prediction_rows)


def get_summary_kpis(df):
    latest_year = df["year"].max()
    prev_year = latest_year - 1
    curr = df[df["year"] == latest_year]
    prev = df[df["year"] == prev_year]

    total_paid = curr["total_paid"].sum()
    prev_paid = prev["total_paid"].sum()
    yoy_change = (total_paid - prev_paid) / prev_paid * 100

    total_members = curr.groupby(["month", "clinical_cluster"])["member_count"].sum().mean()
    total_claims = curr["claim_count"].sum()
    avg_pmpm = curr["pmpm"].mean()
    avg_risk = curr["avg_risk_score"].mean()
    high_cost = curr["high_cost_claimants"].sum()

    return {
        "total_paid": total_paid,
        "yoy_change": yoy_change,
        "total_members": int(total_members),
        "total_claims": total_claims,
        "avg_pmpm": avg_pmpm,
        "avg_risk_score": avg_risk,
        "high_cost_claimants": high_cost,
    }
