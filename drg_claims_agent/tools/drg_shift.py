"""
DRG Shift Analysis Tool -- Detects provider-level variation in DRG
severity assignment for the same clinical condition.

"DRG shift" occurs when different hospitals assign different severity-
level DRGs (base / CC / MCC) for patients with the same principal
diagnosis.  A high MCC capture rate relative to peers may indicate
superior clinical documentation -- or potential upcoding.
"""

import json
from langchain_core.tools import tool
from tools.drg_lookup import DRG_FAMILIES, MS_DRG_REFERENCE


SAMPLE_SHIFT_DATA = {
    "heart_failure": {
        "PRV01": {
            "name": "City General Hospital",
            "claims": [
                {"claim_id": "CLM019", "drg": "291", "icd": "I50.23"},
                {"claim_id": "CLM022", "drg": "291", "icd": "I50.23"},
                {"claim_id": "CLM049", "drg": "291", "icd": "I50.23"},
                {"claim_id": "CLM060", "drg": "291", "icd": "I50.33"},
                {"claim_id": "CLM061", "drg": "291", "icd": "I50.23"},
                {"claim_id": "CLM062", "drg": "292", "icd": "I50.9"},
                {"claim_id": "CLM063", "drg": "291", "icd": "I50.43"},
                {"claim_id": "CLM064", "drg": "293", "icd": "I50.9"},
            ],
        },
        "PRV02": {
            "name": "Regional Medical Center",
            "claims": [
                {"claim_id": "CLM020", "drg": "291", "icd": "I50.33"},
                {"claim_id": "CLM023", "drg": "291", "icd": "I50.9"},
                {"claim_id": "CLM065", "drg": "292", "icd": "I50.23"},
                {"claim_id": "CLM066", "drg": "292", "icd": "I50.33"},
                {"claim_id": "CLM067", "drg": "293", "icd": "I50.9"},
                {"claim_id": "CLM068", "drg": "292", "icd": "I50.43"},
                {"claim_id": "CLM069", "drg": "293", "icd": "I50.9"},
            ],
        },
        "PRV03": {
            "name": "University Hospital",
            "claims": [
                {"claim_id": "CLM021", "drg": "291", "icd": "I50.43"},
                {"claim_id": "CLM070", "drg": "292", "icd": "I50.23"},
                {"claim_id": "CLM071", "drg": "291", "icd": "I50.33"},
                {"claim_id": "CLM072", "drg": "293", "icd": "I50.9"},
                {"claim_id": "CLM073", "drg": "292", "icd": "I50.23"},
            ],
        },
    },
    "pneumonia": {
        "PRV01": {
            "name": "City General Hospital",
            "claims": [
                {"claim_id": "CLM029", "drg": "193", "icd": "J18.9"},
                {"claim_id": "CLM032", "drg": "193", "icd": "J15.1"},
                {"claim_id": "CLM074", "drg": "193", "icd": "J18.9"},
                {"claim_id": "CLM075", "drg": "193", "icd": "J15.9"},
                {"claim_id": "CLM076", "drg": "194", "icd": "J18.1"},
            ],
        },
        "PRV02": {
            "name": "Regional Medical Center",
            "claims": [
                {"claim_id": "CLM030", "drg": "193", "icd": "J15.9"},
                {"claim_id": "CLM033", "drg": "193", "icd": "J18.9"},
                {"claim_id": "CLM077", "drg": "194", "icd": "J18.9"},
                {"claim_id": "CLM078", "drg": "194", "icd": "J15.1"},
                {"claim_id": "CLM079", "drg": "195", "icd": "J18.1"},
            ],
        },
        "PRV03": {
            "name": "University Hospital",
            "claims": [
                {"claim_id": "CLM031", "drg": "193", "icd": "J18.1"},
                {"claim_id": "CLM080", "drg": "194", "icd": "J18.9"},
                {"claim_id": "CLM081", "drg": "194", "icd": "J15.9"},
                {"claim_id": "CLM082", "drg": "195", "icd": "J18.9"},
            ],
        },
    },
    "sepsis": {
        "PRV01": {
            "name": "City General Hospital",
            "claims": [
                {"claim_id": "CLM008", "drg": "871", "icd": "A41.9"},
                {"claim_id": "CLM011", "drg": "871", "icd": "A41.02"},
                {"claim_id": "CLM083", "drg": "871", "icd": "A41.9"},
                {"claim_id": "CLM084", "drg": "871", "icd": "A41.01"},
            ],
        },
        "PRV02": {
            "name": "Regional Medical Center",
            "claims": [
                {"claim_id": "CLM009", "drg": "871", "icd": "A41.01"},
                {"claim_id": "CLM012", "drg": "871", "icd": "A41.9"},
                {"claim_id": "CLM085", "drg": "872", "icd": "A41.9"},
                {"claim_id": "CLM047", "drg": "871", "icd": "A41.9"},
            ],
        },
        "PRV03": {
            "name": "University Hospital",
            "claims": [
                {"claim_id": "CLM010", "drg": "871", "icd": "A41.9"},
                {"claim_id": "CLM013", "drg": "871", "icd": "A41.01"},
                {"claim_id": "CLM086", "drg": "872", "icd": "A41.9"},
                {"claim_id": "CLM087", "drg": "872", "icd": "A41.02"},
            ],
        },
    },
    "stroke": {
        "PRV01": {
            "name": "City General Hospital",
            "claims": [
                {"claim_id": "CLM090", "drg": "064", "icd": "I63.9"},
                {"claim_id": "CLM091", "drg": "064", "icd": "I63.50"},
                {"claim_id": "CLM092", "drg": "065", "icd": "I63.9"},
            ],
        },
        "PRV02": {
            "name": "Regional Medical Center",
            "claims": [
                {"claim_id": "CLM093", "drg": "065", "icd": "I63.9"},
                {"claim_id": "CLM094", "drg": "066", "icd": "I63.9"},
            ],
        },
        "PRV03": {
            "name": "University Hospital",
            "claims": [
                {"claim_id": "CLM095", "drg": "064", "icd": "I63.9"},
            ],
        },
    },
    "hip_knee_replacement": {
        "PRV01": {
            "name": "City General Hospital",
            "claims": [
                {"claim_id": "CLM100", "drg": "470", "icd": "M16.11"},
                {"claim_id": "CLM101", "drg": "470", "icd": "M17.11"},
            ],
        },
        "PRV02": {
            "name": "Regional Medical Center",
            "claims": [
                {"claim_id": "CLM102", "drg": "470", "icd": "M16.12"},
            ],
        },
        "PRV03": {
            "name": "University Hospital",
            "claims": [
                {"claim_id": "CLM103", "drg": "469", "icd": "M16.9"},
            ],
        },
    },
    "uti": {
        "PRV01": {
            "name": "City General Hospital",
            "claims": [
                {"claim_id": "CLM110", "drg": "690", "icd": "N39.0"},
            ],
        },
        "PRV02": {
            "name": "Regional Medical Center",
            "claims": [
                {"claim_id": "CLM111", "drg": "690", "icd": "N39.0"},
            ],
        },
        "PRV03": {
            "name": "University Hospital",
            "claims": [
                {"claim_id": "CLM112", "drg": "689", "icd": "N39.0"},
            ],
        },
    },
}


def _analyze_family(family_name: str) -> dict:
    """Run DRG shift analysis for one DRG family across providers."""
    fam = DRG_FAMILIES.get(family_name)
    if not fam:
        return {"error": f"Unknown family '{family_name}'. Available: {', '.join(DRG_FAMILIES.keys())}"}

    data = SAMPLE_SHIFT_DATA.get(family_name)
    if not data:
        return {"error": f"No claims data available for family '{family_name}'."}

    tier_codes = {
        tier: fam[tier] for tier in ("mcc", "cc", "base") if fam[tier]
    }
    tier_weights = {}
    for tier, code in tier_codes.items():
        ref = MS_DRG_REFERENCE.get(code, {})
        tier_weights[code] = ref.get("relative_weight", 0)

    providers = []
    all_mcc_rates = []

    for prov_id, prov_data in data.items():
        total = len(prov_data["claims"])
        counts = {}
        for tier, code in tier_codes.items():
            cnt = sum(1 for c in prov_data["claims"] if c["drg"] == code)
            counts[tier] = {"drg": code, "count": cnt, "pct": round(cnt / total * 100, 1)}

        mcc_code = tier_codes.get("mcc")
        mcc_rate = counts.get("mcc", {}).get("pct", 0)
        all_mcc_rates.append(mcc_rate)

        avg_weight = sum(
            tier_weights.get(c["drg"], 0) for c in prov_data["claims"]
        ) / total

        providers.append({
            "provider_id": prov_id,
            "provider_name": prov_data["name"],
            "total_claims": total,
            "distribution": counts,
            "mcc_capture_rate_pct": mcc_rate,
            "avg_drg_weight": round(avg_weight, 4),
        })

    peer_avg_mcc = round(sum(all_mcc_rates) / len(all_mcc_rates), 1) if all_mcc_rates else 0

    flags = []
    for p in providers:
        rate = p["mcc_capture_rate_pct"]
        if peer_avg_mcc > 0:
            ratio = rate / peer_avg_mcc
            p["vs_peer_avg"] = f"{'+' if rate > peer_avg_mcc else ''}{round(rate - peer_avg_mcc, 1)}%"
            p["mcc_ratio_to_peer"] = round(ratio, 2)
            if ratio >= 1.8:
                flags.append({
                    "provider": p["provider_name"],
                    "severity": "HIGH",
                    "finding": (
                        f"MCC capture rate {rate}% is {ratio:.1f}x the peer "
                        f"average of {peer_avg_mcc}%. Potential upcoding or "
                        f"superior clinical documentation. Recommend chart review."
                    ),
                })
            elif ratio <= 0.5 and peer_avg_mcc > 20:
                flags.append({
                    "provider": p["provider_name"],
                    "severity": "MODERATE",
                    "finding": (
                        f"MCC capture rate {rate}% is only {ratio:.1f}x the peer "
                        f"average of {peer_avg_mcc}%. Possible undercoding -- "
                        f"documentation improvement could increase revenue."
                    ),
                })
        else:
            p["vs_peer_avg"] = "N/A"
            p["mcc_ratio_to_peer"] = None

    weights_spread = max(tier_weights.values()) - min(tier_weights.values()) if tier_weights else 0

    return {
        "family": family_name,
        "label": fam["label"],
        "drg_tiers": {
            tier: {
                "code": code,
                "weight": tier_weights.get(code, 0),
            }
            for tier, code in tier_codes.items()
        },
        "weight_spread": round(weights_spread, 4),
        "peer_avg_mcc_rate_pct": peer_avg_mcc,
        "providers": providers,
        "flags": flags,
        "recommendation": (
            "Chart review recommended for flagged providers."
            if flags else "No significant DRG shift detected across providers."
        ),
    }


@tool
def drg_shift_analysis(family_name: str) -> str:
    """Analyze DRG shift patterns across providers for a given DRG family.

    Compares how different hospitals assign severity-level DRGs (base, CC,
    MCC) for the same clinical condition. Identifies providers with
    unusually high or low MCC capture rates relative to peers.

    A high MCC capture rate may indicate:
      - Superior clinical documentation (legitimate)
      - DRG upcoding (potential compliance issue)

    A low MCC capture rate may indicate:
      - Undercoding and missed revenue opportunity

    Available families: heart_failure, pneumonia, sepsis,
    hip_knee_replacement, stroke, uti.

    Args:
        family_name: The DRG family to analyze (e.g. 'heart_failure',
                     'pneumonia', 'sepsis').
    """
    result = _analyze_family(family_name.strip().lower().replace(" ", "_"))
    return json.dumps(result, indent=2)
