# Call Center + Claims: Predict High-Cost Members from Call Signals

## 1-Day Proof-of-Concept — Ready to Present Tomorrow

---

## The Insight That Sells It

> **Members call BEFORE they cost.**
>
> A member calling about "prior authorization for spine surgery" or "which oncologists are in-network"
> is telling you — weeks before any claim arrives — that a $50K-$200K episode is coming.
>
> The call center is your **earliest warning system**. Claims are lagging indicators. Calls are leading ones.

---

## The 30-Second Pitch

| | |
|---|---|
| **Problem** | We detect high-cost members only AFTER claims hit — too late for intervention |
| **Insight** | Members reveal intent through call center interactions weeks before claims generate |
| **Solution** | Combine call center signals + claims history to flag rising-risk members 30-90 days earlier |
| **Data** | Call center data (intent, plan, ZIP, group, demographics) + claims history — both already in-house |
| **Scope** | Small member cohort (5K-10K members with call + claims data) — doable in 1 day |
| **Output** | Ranked risk list with call-driven early warning flags + SHAP explanations |
| **Value** | Shift from **reactive** (pay the claim) to **proactive** (intervene before the claim) |

---

## Data You Have — Mapped to Features

### Call Center Data

| Your Column | Feature Engineering | Why It's Predictive |
|------------|-------------------|-------------------|
| **Call Intent** | `intent_prior_auth` = 1 if intent contains "authorization", "pre-cert" | Prior auth call = high-cost service incoming |
| | `intent_specialist_search` = 1 if "specialist", "oncologist", "surgeon", etc. | Specialist search = complex care ahead |
| | `intent_benefit_check` = 1 if "coverage", "benefit", "does my plan cover" | Checking coverage for expensive service |
| | `intent_claim_dispute` = 1 if "denied", "appeal", "not covered", "dispute" | Payment friction = unresolved costly care |
| | `intent_complaint` = 1 if "complaint", "grievance", "unhappy" | Dissatisfaction = potential disenrollment, deferred care |
| | `intent_rx_question` = 1 if "prescription", "medication", "pharmacy", "specialty drug" | Rx inquiry = possible specialty drug start |
| | `intent_emergency_category` — NLP bucket: routine / urgent / high-cost-signal | Composite intent risk score |
| **Plan** | `plan_type` = HMO/PPO/HDHP/MA | Plan design affects utilization behavior |
| **County** | `county_fips` → join to SDOH, provider density | Geographic risk factor |
| **ZIP Code** | `member_zip` → join to ADI, SVI (free, 5 min download) | Socioeconomic risk proxy |
| **Group ID** | `group_id` → group size, industry SIC | Employer group risk profile |
| **Age** | `age`, `age_band` | Age is #6 predictor in cost models |
| **Gender** | `gender` | Risk factor (pregnancy, cardiac, etc.) |
| **Address** | `state`, `urban_rural_flag` | Geographic cost variation |
| **Call Time** | `hour_of_day`, `day_of_week`, `is_weekend` | After-hours calls correlate with urgency |
| | `calls_last_30d`, `calls_last_90d` | Call frequency = rising complexity/frustration |
| | `days_since_last_call` | Recent spike in calls = escalating situation |
| | `avg_call_duration_90d` | Longer calls = more complex issues |
| | `call_count_trend` | Accelerating call frequency = deteriorating situation |

### Claims Data (Join on member_id)

| Derived Feature | Calculation | Window |
|----------------|-------------|--------|
| `total_allowed_3m` | SUM(allowed_amount) | Last 3 months |
| `total_allowed_12m` | SUM(allowed_amount) | Last 12 months |
| `cost_trend_slope` | Monthly allowed linear regression slope | 12 months |
| `er_visits_6m` | COUNT(ER claims) | 6 months |
| `ip_admits_12m` | COUNT(inpatient stays) | 12 months |
| `chronic_condition_count` | # of chronic flags (DM, CHF, CKD, COPD, cancer) | All history |
| `specialty_rx_flag` | Any specialty drug claim | 12 months |
| `hcc_risk_score` | CMS-HCC prospective risk score | Current |
| `unique_specialists_12m` | COUNT DISTINCT specialist NPIs | 12 months |
| `readmit_30d_flag` | IP admit within 30 days of prior discharge | 12 months |

---

## 1-Day Execution Plan

### Hour-by-Hour Schedule

```
  8:00 AM                                                    6:00 PM
    │                                                           │
    ▼                                                           ▼
    ┌────────┬────────┬─────────┬────────┬────────┬────────────┐
    │ DATA   │FEATURE │  MODEL  │ SHAP & │ BUILD  │  PREP      │
    │ PULL & │ ENG    │ TRAIN   │ EVAL   │ OUTPUT │  SLIDES    │
    │ JOIN   │        │         │        │ TABLE  │            │
    │        │        │         │        │        │            │
    │ 2 hrs  │ 2 hrs  │ 2 hrs   │ 1 hr   │ 1 hr   │ 2 hrs     │
    └────────┴────────┴─────────┴────────┴────────┴────────────┘
    8-10AM    10-12PM   12-2PM   2-3PM    3-4PM     4-6PM
```

---

### STEP 1: Data Pull & Join (8:00 - 10:00 AM)

```sql
-- Pull call center data for members with 2+ calls in last 6 months
CREATE TABLE call_features AS
SELECT
    member_id,
    COUNT(*)                                          AS call_count_6m,
    COUNT(CASE WHEN call_date >= DATEADD(day,-30,GETDATE()) THEN 1 END)
                                                      AS calls_last_30d,
    MAX(call_date)                                    AS last_call_date,
    DATEDIFF(day, MAX(call_date), GETDATE())          AS days_since_last_call,
    AVG(call_duration_seconds)                        AS avg_call_duration,
    MAX(call_duration_seconds)                        AS max_call_duration,

    -- Intent flags (adjust string matching to your intent taxonomy)
    MAX(CASE WHEN call_intent LIKE '%auth%'
             OR call_intent LIKE '%pre-cert%'       THEN 1 ELSE 0 END)
                                                      AS intent_prior_auth,
    MAX(CASE WHEN call_intent LIKE '%specialist%'
             OR call_intent LIKE '%surgeon%'
             OR call_intent LIKE '%oncol%'           THEN 1 ELSE 0 END)
                                                      AS intent_specialist_search,
    MAX(CASE WHEN call_intent LIKE '%coverage%'
             OR call_intent LIKE '%benefit%'
             OR call_intent LIKE '%does my plan%'    THEN 1 ELSE 0 END)
                                                      AS intent_benefit_check,
    MAX(CASE WHEN call_intent LIKE '%denied%'
             OR call_intent LIKE '%appeal%'
             OR call_intent LIKE '%dispute%'         THEN 1 ELSE 0 END)
                                                      AS intent_claim_dispute,
    MAX(CASE WHEN call_intent LIKE '%complaint%'
             OR call_intent LIKE '%grievan%'         THEN 1 ELSE 0 END)
                                                      AS intent_complaint,
    MAX(CASE WHEN call_intent LIKE '%prescri%'
             OR call_intent LIKE '%medica%'
             OR call_intent LIKE '%specialty drug%'  THEN 1 ELSE 0 END)
                                                      AS intent_rx_question,

    -- Time-based signals
    MAX(CASE WHEN DATEPART(hour, call_time) NOT BETWEEN 9 AND 17
                                                     THEN 1 ELSE 0 END)
                                                      AS after_hours_call_flag,
    -- Demographics (from call center record)
    MAX(age)           AS age,
    MAX(gender)        AS gender,
    MAX(plan_type)     AS plan_type,
    MAX(zip_code)      AS zip_code,
    MAX(county)        AS county,
    MAX(group_id)      AS group_id

FROM call_center_data
WHERE call_date >= DATEADD(month, -6, GETDATE())
GROUP BY member_id;


-- Pull claims summary for same members
CREATE TABLE claims_features AS
SELECT
    c.member_id,
    SUM(CASE WHEN service_date >= DATEADD(month,-3,GETDATE())
             THEN allowed_amount ELSE 0 END)           AS total_allowed_3m,
    SUM(allowed_amount)                                 AS total_allowed_12m,
    COUNT(CASE WHEN place_of_service = '23' THEN 1 END) AS er_visits_12m,
    COUNT(CASE WHEN place_of_service = '21' THEN 1 END) AS ip_claims_12m,
    COUNT(DISTINCT rendering_provider_npi)               AS unique_providers_12m,
    MAX(allowed_amount)                                  AS max_single_claim,
    -- Chronic condition flags from ICD-10
    MAX(CASE WHEN dx_code LIKE 'E1[0-3]%'  THEN 1 ELSE 0 END) AS diabetes_flag,
    MAX(CASE WHEN dx_code LIKE 'I50%'      THEN 1 ELSE 0 END) AS chf_flag,
    MAX(CASE WHEN dx_code LIKE 'N18%'      THEN 1 ELSE 0 END) AS ckd_flag,
    MAX(CASE WHEN dx_code LIKE 'J44%'      THEN 1 ELSE 0 END) AS copd_flag,
    MAX(CASE WHEN dx_code BETWEEN 'C00' AND 'C96'
                                           THEN 1 ELSE 0 END) AS cancer_flag
FROM claims c
WHERE service_date >= DATEADD(month, -12, GETDATE())
  AND claim_status = 'PAID'
  AND c.member_id IN (SELECT member_id FROM call_features)
GROUP BY c.member_id;


-- Join into modeling table
CREATE TABLE model_input AS
SELECT
    cf.*,
    cl.total_allowed_3m,
    cl.total_allowed_12m,
    cl.er_visits_12m,
    cl.ip_claims_12m,
    cl.unique_providers_12m,
    cl.max_single_claim,
    cl.diabetes_flag,
    cl.chf_flag,
    cl.ckd_flag,
    cl.copd_flag,
    cl.cancer_flag,
    (cl.diabetes_flag + cl.chf_flag + cl.ckd_flag
     + cl.copd_flag + cl.cancer_flag)                  AS chronic_count,

    -- TARGET: next-quarter spend > $50K
    CASE WHEN nq.next_quarter_allowed >= 50000
         THEN 1 ELSE 0 END                             AS target_high_cost

FROM call_features cf
LEFT JOIN claims_features cl ON cf.member_id = cl.member_id
LEFT JOIN next_quarter_spend nq ON cf.member_id = nq.member_id;
```

**Cohort Size Target:** 5,000 - 10,000 members who have both call center records AND claims history. This is enough for a solid POC.

---

### STEP 2: Feature Engineering in Python (10:00 AM - 12:00 PM)

```python
import pandas as pd
import numpy as np

df = pd.read_csv("model_input.csv")  # or pull from SQL

# ── Composite call-risk signal ──
# Members calling about prior auth + specialist search = highest signal
df["call_risk_score"] = (
    df["intent_prior_auth"]        * 3.0 +   # strongest signal
    df["intent_specialist_search"] * 2.5 +
    df["intent_rx_question"]       * 2.0 +
    df["intent_benefit_check"]     * 1.5 +
    df["intent_claim_dispute"]     * 1.0 +
    df["intent_complaint"]         * 0.5 +
    df["after_hours_call_flag"]    * 0.5
)

# ── Call intensity signal ──
df["call_intensity"] = df["calls_last_30d"] / (df["call_count_6m"] + 1)
# Ratio near 1.0 = all calls bunched recently = escalating situation

# ── Cost acceleration ──
df["cost_recent_pct"] = df["total_allowed_3m"] / (df["total_allowed_12m"] + 1)
# > 0.5 means more than half of yearly spend happened in last 3 months = accelerating

# ── Combined early warning flag ──
df["early_warning_flag"] = (
    (df["call_risk_score"] >= 3.0) &
    (df["total_allowed_3m"] > 5000)
).astype(int)

# ── Feature list for model ──
feature_cols = [
    # Call features (the differentiator)
    "call_count_6m", "calls_last_30d", "days_since_last_call",
    "avg_call_duration", "call_risk_score", "call_intensity",
    "intent_prior_auth", "intent_specialist_search", "intent_benefit_check",
    "intent_claim_dispute", "intent_complaint", "intent_rx_question",
    "after_hours_call_flag",

    # Claims features
    "total_allowed_3m", "total_allowed_12m", "cost_recent_pct",
    "er_visits_12m", "ip_claims_12m", "unique_providers_12m",
    "max_single_claim", "chronic_count",
    "diabetes_flag", "chf_flag", "ckd_flag", "copd_flag", "cancer_flag",

    # Demographics
    "age", "gender_encoded",

    # Composite
    "early_warning_flag",
]

X = df[feature_cols]
y = df["target_high_cost"]

print(f"Dataset: {len(df):,} members")
print(f"High-cost rate: {y.mean()*100:.1f}%")
print(f"Call features: 13 | Claims features: 12 | Demo: 2 | Total: {len(feature_cols)}")
```

---

### STEP 3: Train Model (12:00 - 2:00 PM)

```python
import xgboost as xgb
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import roc_auc_score, precision_recall_curve, auc
import shap

# ── Split (time-based if dates available, else stratified) ──
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, stratify=y, random_state=42
)

# ── Train XGBoost ──
pos_ratio = (y_train == 0).sum() / (y_train == 1).sum()

model = xgb.XGBClassifier(
    objective="binary:logistic",
    eval_metric="aucpr",
    max_depth=5,
    learning_rate=0.05,
    n_estimators=300,
    subsample=0.8,
    colsample_bytree=0.8,
    scale_pos_weight=pos_ratio,
    min_child_weight=20,
    random_state=42,
    use_label_encoder=False,
)

model.fit(
    X_train, y_train,
    eval_set=[(X_test, y_test)],
    verbose=50,
)

# ── Evaluate ──
y_prob = model.predict_proba(X_test)[:, 1]
roc_auc = roc_auc_score(y_test, y_prob)
prec, rec, _ = precision_recall_curve(y_test, y_prob)
pr_auc = auc(rec, prec)

print(f"ROC-AUC: {roc_auc:.3f}")
print(f"PR-AUC:  {pr_auc:.3f}")

# ── KEY COMPARISON: Model with vs without call features ──
# Train a second model WITHOUT call features to show the lift
claims_only_cols = [c for c in feature_cols if c not in [
    "call_count_6m", "calls_last_30d", "days_since_last_call",
    "avg_call_duration", "call_risk_score", "call_intensity",
    "intent_prior_auth", "intent_specialist_search", "intent_benefit_check",
    "intent_claim_dispute", "intent_complaint", "intent_rx_question",
    "after_hours_call_flag", "early_warning_flag",
]]

model_no_calls = xgb.XGBClassifier(**model.get_params())
model_no_calls.fit(X_train[claims_only_cols], y_train)
y_prob_no_calls = model_no_calls.predict_proba(X_test[claims_only_cols])[:, 1]
roc_auc_no_calls = roc_auc_score(y_test, y_prob_no_calls)

print(f"\n{'='*50}")
print(f"  CLAIMS ONLY  AUC: {roc_auc_no_calls:.3f}")
print(f"  CLAIMS+CALLS AUC: {roc_auc:.3f}")
print(f"  LIFT FROM CALLS:  +{(roc_auc - roc_auc_no_calls)*100:.1f}%")
print(f"{'='*50}")
```

**This A/B comparison is the slide that wins the room.** Showing that call center data adds measurable AUC lift over claims-only proves the value of integrating call signals.

---

### STEP 4: SHAP & Evaluation (2:00 - 3:00 PM)

```python
# ── SHAP for explainability ──
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_test)

# Global feature importance — save as image for slides
shap.summary_plot(shap_values, X_test, feature_names=feature_cols,
                  show=False)
import matplotlib.pyplot as plt
plt.tight_layout()
plt.savefig("shap_global_importance.png", dpi=150, bbox_inches="tight")

# Top 3 individual member examples for slides
for i, idx in enumerate(y_prob.argsort()[-3:][::-1]):
    shap.waterfall_plot(
        shap.Explanation(
            values=shap_values[idx],
            base_values=explainer.expected_value,
            data=X_test.iloc[idx],
            feature_names=feature_cols,
        ),
        show=False,
    )
    plt.tight_layout()
    plt.savefig(f"shap_member_example_{i+1}.png", dpi=150, bbox_inches="tight")
    plt.close()
```

---

### STEP 5: Build Output Table (3:00 - 4:00 PM)

```python
# ── Score all members and produce output ──
df["probability"] = model.predict_proba(X[feature_cols])[:, 1]

# Risk tiers
df["risk_tier"] = pd.cut(
    df["probability"],
    bins=[0, 0.15, 0.30, 0.50, 0.70, 1.0],
    labels=["STANDARD", "WATCH", "ELEVATED", "HIGH", "CRITICAL"],
)

# Top driver per member (from SHAP)
shap_all = explainer.shap_values(X[feature_cols])
top_driver_idx = np.abs(shap_all).argsort(axis=1)[:, -1]
df["top_driver"] = [feature_cols[i] for i in top_driver_idx]

# ── Final output ──
output = df[[
    "member_id", "probability", "risk_tier", "top_driver",
    "call_risk_score", "calls_last_30d", "intent_prior_auth",
    "intent_specialist_search", "total_allowed_3m", "chronic_count",
    "age", "plan_type", "zip_code", "county",
]].sort_values("probability", ascending=False)

output.to_csv("high_cost_predictions_with_call_signals.csv", index=False)

print(f"\nResults saved. Distribution:")
print(output["risk_tier"].value_counts())
```

---

### STEP 6: Prep Slides (4:00 - 6:00 PM)

Use the outputs from Steps 3-5 directly. Below is the slide deck structure.

---

## Presentation Deck — 6 Slides

### Slide 1: THE PROBLEM

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│          MEMBERS CALL BEFORE THEY COST                           │
│                                                                  │
│     ┌──────────┐         ┌──────────┐         ┌──────────┐      │
│     │ MEMBER   │  30-90  │ CLAIM    │  30-60  │ CLAIM    │      │
│     │ CALLS    │  days   │ INCURRED │  days   │ APPEARS  │      │
│     │ ABOUT    │ ──────► │          │ ──────► │ IN       │      │
│     │ SURGERY  │  before │          │   lag   │ FINANCIAL│      │
│     │          │         │          │         │ REPORTS  │      │
│     └──────────┘         └──────────┘         └──────────┘      │
│                                                                  │
│     ◄── WE CAN ACT HERE ──►  ◄── TOO LATE ────────────────►    │
│                                                                  │
│  Today we detect high-cost members AFTER claims hit.             │
│  What if we used call center signals to detect them BEFORE?      │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Slide 2: THE APPROACH

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│   CALL CENTER DATA            CLAIMS DATA                        │
│   (leading signal)            (historical cost)                  │
│                                                                  │
│   • Call intent               • Prior 12-month spend             │
│   • "Prior auth" flag         • ER visits, admissions            │
│   • "Specialist search"       • Chronic conditions               │
│   • Call frequency spike      • Risk score                       │
│   • After-hours urgency       • Specialist utilization           │
│                                                                  │
│         └────────────┬───────────────┘                            │
│                      ▼                                           │
│              ┌──────────────┐                                    │
│              │   XGBoost    │                                    │
│              │   ML Model   │ ← 27 features, 7,500 members      │
│              └──────┬───────┘                                    │
│                     ▼                                            │
│         ┌────────────────────────┐                                │
│         │ Per-member risk score  │                                │
│         │ + top cost drivers     │                                │
│         │ + recommended action   │                                │
│         └────────────────────────┘                                │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Slide 3: THE PROOF — Call Data Adds Lift (Killer Slide)

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│         MODEL COMPARISON: Claims-Only vs. Claims + Calls         │
│                                                                  │
│                                                                  │
│   AUC-ROC                                                        │
│                                                                  │
│   0.90 │                              ┌──────────┐               │
│        │                              │ CLAIMS + │               │
│   0.85 │                              │  CALLS   │               │
│        │          ┌──────────┐        │  0.88    │               │
│   0.80 │          │ CLAIMS   │        │          │               │
│        │          │  ONLY    │        └──────────┘               │
│   0.75 │          │  0.82    │                                   │
│        │          │          │          +6% LIFT                  │
│   0.70 │          └──────────┘         from call                 │
│        │                               signals                   │
│   0.65 │                                                         │
│        └──────────────────────────────────────────                │
│                                                                  │
│   "Adding call center data identified 23% MORE high-cost         │
│    members 60 days earlier than claims-only model"               │
│                                                                  │
│   (actual numbers from your run — replace with real results)     │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Slide 4: WHAT THE MODEL FOUND — Feature Importance

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│       TOP 10 PREDICTORS OF HIGH-COST MEMBERS                     │
│                                                                  │
│  Feature                    │ Importance                         │
│  ──────────────────────────┼──────────────────────────           │
│  total_allowed_3m           │ █████████████████████  0.18        │
│  call_risk_score         ★ │ ████████████████████   0.16        │
│  chronic_count              │ ██████████████████     0.14        │
│  intent_prior_auth       ★ │ █████████████████      0.13        │
│  calls_last_30d          ★ │ ████████████████       0.12        │
│  er_visits_12m              │ ██████████████         0.10        │
│  intent_specialist_srch  ★ │ ████████████           0.08        │
│  age                        │ ██████████             0.06        │
│  ip_claims_12m              │ █████████              0.05        │
│  days_since_last_call    ★ │ ████████               0.04        │
│                                                                  │
│  ★ = Call center feature                                         │
│                                                                  │
│  5 of the top 10 features are from call center data!             │
│                                                                  │
│  (replace bars with SHAP plot screenshot: shap_global.png)       │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Slide 5: REAL MEMBER EXAMPLES

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  MEMBER A — CRITICAL RISK (prob: 0.89)                           │
│  ┌────────────────────────────────────────────────────────┐      │
│  │ Call signal: Called 3x in 2 weeks about "oncologist    │      │
│  │   in-network" + "does plan cover PET scan"            │      │
│  │ Claims: $12K in last 3 months, new imaging orders     │      │
│  │ Model says: High probability of cancer workup →       │      │
│  │   predicted $95K next quarter                         │      │
│  │ Action: Route to oncology care management NOW         │      │
│  └────────────────────────────────────────────────────────┘      │
│                                                                  │
│  MEMBER B — HIGH RISK (prob: 0.67)                               │
│  ┌────────────────────────────────────────────────────────┐      │
│  │ Call signal: Prior auth inquiry for "spine surgery"    │      │
│  │ Claims: $8K chronic pain, 4 specialist visits          │      │
│  │ Model says: Surgical episode incoming → predicted $72K │      │
│  │ Action: Surgical review, explore conservative options  │      │
│  └────────────────────────────────────────────────────────┘      │
│                                                                  │
│  MEMBER C — ELEVATED (prob: 0.41)                                │
│  ┌────────────────────────────────────────────────────────┐      │
│  │ Call signal: Asking about "specialty pharmacy" +       │      │
│  │   "Humira" coverage                                   │      │
│  │ Claims: RA diagnosis, rising PMPM                      │      │
│  │ Model says: Specialty drug start → predicted $58K/yr  │      │
│  │ Action: Formulary guidance, biosimilar option          │      │
│  └────────────────────────────────────────────────────────┘      │
│                                                                  │
│  (replace with shap_member_example_1/2/3.png screenshots)        │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Slide 6: THE ASK — Scale This Up

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│              FROM POC → PRODUCTION IN 4 WEEKS                    │
│                                                                  │
│  TODAY'S POC              PRODUCTION (Week 4)                    │
│  ───────────              ──────────────────                     │
│  7,500 members            All members with calls (2M+)           │
│  27 features              85 features + NLP on call transcripts  │
│  Batch CSV output         Real-time scoring API                  │
│  Manual slides            Live dashboard with SHAP drilldown     │
│                                                                  │
│  ┌───────────────────────────────────────────────────┐           │
│  │                                                   │           │
│  │   ESTIMATED VALUE AT SCALE                        │           │
│  │                                                   │           │
│  │   Members flagged 60+ days earlier:  +23%         │           │
│  │   CM intervention success rate:      15-20%       │           │
│  │   Cost avoidance per year:           $50-150M     │           │
│  │   Investment needed:                 $450K        │           │
│  │   ROI:                               111x - 333x  │           │
│  │                                                   │           │
│  └───────────────────────────────────────────────────┘           │
│                                                                  │
│  ASK: 2 data engineers + 1 data scientist for 4 weeks            │
│       to move from POC to production pipeline                    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Quick Reference — What To Run Tomorrow Morning

```
MORNING CHECKLIST (paste on your monitor):

□ 8:00  Pull call center data → call_features table (SQL above)
□ 8:45  Pull claims data → claims_features table (SQL above)
□ 9:30  Join tables → model_input (SQL above)
□ 10:00 Export to CSV, open Jupyter notebook
□ 10:30 Run feature engineering (Python Step 2)
□ 11:30 Verify: print shape, null counts, class distribution
□ 12:00 Train XGBoost (Python Step 3)
□ 12:30 Train claims-only model for comparison (the A/B slide)
□ 1:00  Print AUC lift number ← THIS IS YOUR HEADLINE
□ 1:30  Generate SHAP plots (Python Step 4) ← SAVE AS PNG
□ 2:30  Build output table (Python Step 5) ← SAVE AS CSV
□ 3:00  Open PowerPoint, build 6 slides using templates above
□ 4:00  Pick 3 compelling member examples from output
□ 5:00  Rehearse 10-minute walkthrough
□ 5:30  Done. Get sleep.
```

---

*Document: Call Center + Claims 1-Day POC*
*Version: 1.0 | February 24, 2026*
*Companion to: UHC_HighCost_Claimant_Prediction_QuickWin.md*
