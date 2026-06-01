# High-Cost Claimant Prediction — The Quick Win

## UHC's Fastest, Highest-Impact ML Use Case

---

## Why This One?

| Criteria | Score | Rationale |
|----------|-------|-----------|
| **Speed to Build** | ★★★★★ | Standard binary classification → 2-4 week MVP with data already in-house |
| **Business Impact** | ★★★★★ | 2.2% of members = 23% of spend. At UHC scale ($200B+ medical), even 1% improvement = $200M+ |
| **Data Readiness** | ★★★★★ | Requires only claims + enrollment — no external data purchase needed for v1 |
| **Stakeholder Appeal** | ★★★★★ | Visual SHAP explanations, dollar-value predictions, member risk cards |
| **Actionability** | ★★★★★ | Direct feed into Care Management, UM, actuarial reserving, stop-loss |
| **Proven Track Record** | ★★★★★ | Published research: XGBoost captures 76% of top-decile spend vs. 43.5% with historical methods |

**Bottom line:** This is the use case you demo to the C-suite in 4 weeks to get funding for everything else.

---

## 1. Problem Statement

> **Predict which members will exceed $50K / $100K / $250K in total allowed claims in the upcoming quarter, and estimate their expected spend.**

### Why It Matters — The Math

```
UHC Commercial + MA membership:  ~50 million members
Top 2.2% of claimants:           ~1.1 million members
Their share of total spend:       23% = ~$46 billion/year

If predictive model identifies these members 90 days early:
  → Care Management intervenes on 20% of cases
  → Average cost reduction per intervention: 10-15%
  → Annual savings potential: $920M - $1.38B

Even a modest 5% improvement in identification accuracy:
  → $46B × 5% × 10% cost reduction = $230M/year
```

---

## 2. Data Required (All Already Available In-House)

### 2.1 Primary Data Tables

```
┌─────────────────────────────────────────────────────────────────────┐
│                     WHAT YOU NEED (MVP)                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐   ┌──────────────┐   ┌──────────────────────┐     │
│  │  CLAIMS      │   │  ENROLLMENT  │   │  ADJUSTMENTS (835)   │     │
│  │  (837P/837I) │   │  (834)       │   │                      │     │
│  └──────┬──────┘   └──────┬───────┘   └──────────┬───────────┘     │
│         │                 │                       │                  │
│         └────────────┬────┴───────────────────────┘                  │
│                      ▼                                               │
│              ┌──────────────┐                                        │
│              │  MEMBER-MONTH│    ← This is your modeling grain       │
│              │  FEATURE     │                                        │
│              │  TABLE       │                                        │
│              └──────────────┘                                        │
│                                                                     │
│  NICE-TO-HAVE (Phase 2):                                            │
│  ┌──────────┐  ┌───────────┐  ┌─────────┐  ┌──────────────────┐    │
│  │ Pharmacy │  │ Auth / UM │  │ SDOH    │  │ Call Center      │    │
│  │ Claims   │  │ Data      │  │ (free)  │  │ (NLP features)   │    │
│  └──────────┘  └───────────┘  └─────────┘  └──────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Source Tables & Key Columns

**Table 1: Medical Claims (837P Professional + 837I Institutional)**

| Column | Source Field | Role in Model |
|--------|-------------|---------------|
| `claim_id` | CLM01 | Grain identifier |
| `member_id` | Box 1a (CMS-1500) | Join key to enrollment |
| `service_from_date` | Box 24A | Time windowing |
| `service_to_date` | Box 24A | LOS calculation |
| `icd10_dx_1` through `icd10_dx_12` | Box 21 (A-L) | HCC risk scoring, chronic condition flags |
| `cpt_hcpcs` | Box 24D | Service type classification |
| `cpt_modifier_1` through `cpt_modifier_4` | Box 24D | Procedure context |
| `place_of_service` | Box 24B | IP/OP/ER/Office classification |
| `billed_amount` | Box 28 | Charge inflation signal |
| `allowed_amount` | From 835 adjudication | Primary cost measure |
| `paid_amount` | From 835 | Net plan cost |
| `member_liability` | From 835 (deductible + copay + coinsurance) | Cost-sharing exhaustion signal |
| `rendering_provider_npi` | Box 24J | Provider efficiency linkage |
| `billing_provider_npi` | Box 33 | Provider organization |
| `drg_code` | UB-04 (institutional only) | Inpatient case mix |
| `revenue_code` | UB-04 (institutional only) | Facility service type |
| `admission_type` | UB-04 | Emergency vs. elective |
| `discharge_status` | UB-04 | SNF/home/expired → post-acute trajectory |
| `claim_status` | From adjudication | Paid/denied/adjusted filter |

**Table 2: Member Enrollment (834)**

| Column | Role in Model |
|--------|---------------|
| `member_id` | Primary key |
| `date_of_birth` | Age calculation → age band |
| `gender` | Age-sex risk factor |
| `plan_type` | HMO/PPO/HDHP segmentation |
| `metal_level` | ACA benefit richness (induced utilization) |
| `effective_date` | Enrollment tenure |
| `term_date` | Member months; churn signal |
| `zip_code` | Geographic risk factor, SDOH linkage key |
| `county_fips` | Geographic adjustment |
| `group_id` | Employer group (experience rating) |
| `pcp_npi` | Medical home attribution |
| `risk_score` | HCC prospective risk score |
| `lob` | Commercial / MA / Medicaid segmentation |

**Table 3: Adjustments/Remittance (835)**

| Column | Role in Model |
|--------|---------------|
| `claim_id` | Join to claims |
| `adjustment_reason_code` | Denial type (CO, PR, OA) |
| `paid_date` | Payment lag → IBNR signal |
| `deductible_applied` | Deductible exhaustion tracking |
| `copay_amount` | Member cost-sharing |
| `coinsurance_amount` | Member financial exposure |

---

## 3. Feature Engineering — The Secret Sauce

### 3.1 Feature Categories (85 Features Total)

Features are calculated over rolling windows: **3-month, 6-month, 12-month** lookbacks from prediction date.

#### Category A: Cost History (15 features) — Most Predictive

| # | Feature | Calculation | Window |
|---|---------|-------------|--------|
| 1 | `total_allowed_3m` | SUM(allowed_amount) | 3 months |
| 2 | `total_allowed_6m` | SUM(allowed_amount) | 6 months |
| 3 | `total_allowed_12m` | SUM(allowed_amount) | 12 months |
| 4 | `total_paid_12m` | SUM(paid_amount) | 12 months |
| 5 | `cost_trend_slope` | Linear regression slope of monthly allowed | 12 months |
| 6 | `cost_acceleration` | Δ(3m PMPM) / Δ(prior 3m PMPM) | 6 months |
| 7 | `max_single_claim` | MAX(allowed_amount) per claim | 12 months |
| 8 | `pct_cost_in_last_3m` | allowed_3m / allowed_12m | 12 months |
| 9 | `ip_allowed_12m` | SUM(allowed) WHERE POS in (21,51,61) | 12 months |
| 10 | `op_allowed_12m` | SUM(allowed) WHERE POS in (22,24) | 12 months |
| 11 | `er_allowed_12m` | SUM(allowed) WHERE POS = 23 | 12 months |
| 12 | `rx_allowed_12m` | SUM(allowed) from pharmacy claims | 12 months |
| 13 | `specialty_rx_flag` | ANY specialty drug claim (NDC list) | 12 months |
| 14 | `member_oop_12m` | SUM(deductible + copay + coinsurance) | 12 months |
| 15 | `deductible_exhausted` | member_oop_12m >= plan OOP max | Current year |

#### Category B: Utilization Patterns (20 features)

| # | Feature | Calculation |
|---|---------|-------------|
| 16 | `ip_admits_12m` | COUNT distinct inpatient stays |
| 17 | `ip_days_12m` | SUM(service_to - service_from + 1) for IP |
| 18 | `er_visits_12m` | COUNT distinct ER claims |
| 19 | `er_visits_3m` | COUNT distinct ER claims (recent) |
| 20 | `op_visits_12m` | COUNT distinct outpatient claims |
| 21 | `office_visits_12m` | COUNT claims WHERE POS = 11 |
| 22 | `unique_providers_12m` | COUNT DISTINCT rendering_provider_npi |
| 23 | `unique_specialties_12m` | COUNT DISTINCT provider_specialty |
| 24 | `imaging_count_12m` | COUNT claims WHERE CPT in (70000-79999) |
| 25 | `lab_count_12m` | COUNT claims WHERE CPT in (80000-89999) |
| 26 | `surgery_count_12m` | COUNT claims WHERE CPT in (10000-69999) |
| 27 | `readmit_30day_flag` | IP admit within 30 days of prior discharge |
| 28 | `avg_los` | AVG(discharge_date - admit_date) for IP stays |
| 29 | `observation_hours_12m` | SUM observation hours (revenue code 0762) |
| 30 | `snf_days_12m` | SUM SNF days (POS = 31) |
| 31 | `home_health_visits_12m` | COUNT home health claims (POS = 12) |
| 32 | `telehealth_visits_12m` | COUNT telehealth claims (POS = 02, modifier 95) |
| 33 | `dme_claims_12m` | COUNT DME claims |
| 34 | `ambulance_claims_12m` | COUNT ambulance claims (HCPCS A0XXX) |
| 35 | `utilization_trend_slope` | Linear regression slope of monthly claim count |

#### Category C: Clinical / Diagnosis Profile (20 features)

| # | Feature | Calculation |
|---|---------|-------------|
| 36 | `hcc_risk_score` | CMS-HCC prospective risk score |
| 37 | `hcc_risk_score_change` | Current vs. prior year risk score delta |
| 38 | `unique_hcc_count` | COUNT distinct HCC categories triggered |
| 39 | `chronic_condition_count` | COUNT of CMS Chronic Condition Warehouse flags |
| 40 | `diabetes_flag` | ICD-10 E08-E13 in claims |
| 41 | `chf_flag` | ICD-10 I50.x in claims |
| 42 | `ckd_esrd_flag` | ICD-10 N18.x, Z99.2 |
| 43 | `copd_flag` | ICD-10 J44.x |
| 44 | `cancer_flag` | ICD-10 C00-C96 |
| 45 | `mental_health_flag` | ICD-10 F01-F99 |
| 46 | `substance_use_flag` | ICD-10 F10-F19 |
| 47 | `transplant_history` | ICD-10 Z94.x or CPT transplant codes |
| 48 | `obesity_flag` | ICD-10 E66.x |
| 49 | `pregnancy_flag` | ICD-10 O00-O9A, Z33-Z37 |
| 50 | `trauma_flag` | ICD-10 S00-T88 |
| 51 | `new_cancer_dx_6m` | First cancer ICD-10 in last 6 months (no prior history) |
| 52 | `new_esrd_dx_6m` | First ESRD code in last 6 months |
| 53 | `comorbidity_elixhauser` | Elixhauser comorbidity index from ICD-10 codes |
| 54 | `polypharmacy_flag` | 5+ distinct therapeutic drug classes in Rx claims |
| 55 | `high_risk_dx_combination` | Co-occurring CHF + CKD + diabetes (triple threat) |

#### Category D: Demographics & Plan Design (15 features)

| # | Feature | Calculation |
|---|---------|-------------|
| 56 | `age` | (prediction_date - dob) / 365.25 |
| 57 | `age_band` | Bucketed: 0-17, 18-25, 26-34, 35-44, 45-54, 55-64, 65-74, 75-84, 85+ |
| 58 | `gender` | M / F |
| 59 | `plan_type` | HMO / PPO / EPO / HDHP / MA |
| 60 | `metal_level` | Bronze / Silver / Gold / Platinum / NA |
| 61 | `lob` | Commercial / MA / Medicaid |
| 62 | `enrollment_tenure_months` | Months continuously enrolled |
| 63 | `new_member_flag` | Enrolled < 3 months |
| 64 | `deductible_amount` | Plan-level annual deductible |
| 65 | `oop_max` | Plan-level OOP maximum |
| 66 | `coinsurance_rate` | Member coinsurance % |
| 67 | `network_type` | Narrow / Broad / Tiered |
| 68 | `pcp_attributed` | Has assigned PCP (Y/N) |
| 69 | `group_size_band` | Small (<50), Mid (50-500), Large (500+), Individual |
| 70 | `dependent_flag` | Subscriber vs. dependent |

#### Category E: Provider & Network (10 features)

| # | Feature | Calculation |
|---|---------|-------------|
| 71 | `pcp_efficiency_score` | PCP's risk-adjusted cost percentile |
| 72 | `oon_claim_pct` | % of claims at out-of-network providers |
| 73 | `oon_cost_pct` | % of allowed from out-of-network claims |
| 74 | `pcp_visit_count_12m` | Number of PCP visits (care engagement proxy) |
| 75 | `specialist_referral_count` | Number of unique specialist referrals |
| 76 | `high_cost_provider_flag` | Majority of care at top-quartile cost providers |
| 77 | `academic_medical_center` | Any claims at AMC / teaching hospital |
| 78 | `provider_density_zip` | Providers per 1000 population in member ZIP |
| 79 | `distance_to_pcp` | Estimated miles from member ZIP to PCP ZIP |
| 80 | `usual_source_of_care` | Has consistent care site (not ER-primary) |

#### Category F: SDOH & Geographic (5 features — Free Data)

| # | Feature | Calculation |
|---|---------|-------------|
| 81 | `adi_national_rank` | ADI percentile (1-100) from member ZIP → block group |
| 82 | `svi_overall_score` | CDC SVI composite (0-1) from member tract |
| 83 | `median_household_income` | ACS B19013 for member ZCTA |
| 84 | `food_desert_flag` | USDA Food Atlas LILA flag for member tract |
| 85 | `hpsa_primary_care_flag` | HRSA HPSA designation for member county |

---

## 4. Model Architecture — Two-Stage Design

```
                        ALL MEMBERS (e.g., 10M)
                              │
                    ┌─────────┴──────────┐
                    ▼                    │
            ┌──────────────┐             │
            │   STAGE 1    │             │
            │              │             │
            │  Binary      │             │
            │  Classifier  │             │
            │              │             │
            │  "Will this  │             │
            │  member      │             │
            │  exceed      │             │
            │  $50K next   │             │
            │  quarter?"   │             │
            │              │             │
            │  XGBoost     │             │
            │  85 features │             │
            └──────┬───────┘             │
                   │                     │
          ┌────────┴────────┐            │
          ▼                 ▼            ▼
     P(high-cost)      P(high-cost)   Low-risk
      > 0.30            ≤ 0.30        members
     (flagged)          (monitor)     (no action)
     ~150K members      ~850K         ~9M
          │
          ▼
   ┌──────────────┐
   │   STAGE 2    │
   │              │
   │  Regression  │
   │  Model       │
   │              │
   │  "HOW MUCH   │
   │  will they   │
   │  cost?"      │
   │              │
   │  LightGBM    │
   │  Log-target  │
   └──────┬───────┘
          │
          ▼
   ┌──────────────────────────────────────────────┐
   │              OUTPUT PER MEMBER                │
   │                                               │
   │  member_id:          M-12345678               │
   │  probability:        0.73 (73% chance >$50K)  │
   │  predicted_spend:    $127,400                 │
   │  confidence_interval: [$82K - $195K]          │
   │  risk_tier:          CRITICAL                 │
   │  top_drivers:                                 │
   │    1. Prior 3m spend: $38K (↑ accelerating)   │
   │    2. New ESRD diagnosis                      │
   │    3. 2 ER visits in last 90 days             │
   │    4. Specialty Rx: adalimumab started         │
   │    5. CHF + CKD + diabetes comorbidity        │
   │  recommended_action: CM outreach, nephrology  │
   │                      care coordination        │
   └──────────────────────────────────────────────┘
```

### 4.1 Stage 1: Binary Classifier (Will Exceed Threshold?)

**Algorithm:** XGBoost (Gradient Boosted Decision Trees)

**Why XGBoost:**
- Handles mixed feature types (numeric + categorical) natively
- Robust to missing values (common in claims data)
- Built-in feature importance
- Proven top performer in healthcare cost prediction literature (R² = 0.757, recall@10 = 76%)
- Fast training even on millions of rows

**Hyperparameters (Starting Point):**

```python
import xgboost as xgb

params = {
    "objective": "binary:logistic",
    "eval_metric": ["auc", "aucpr"],
    "max_depth": 6,
    "learning_rate": 0.05,
    "n_estimators": 500,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "min_child_weight": 50,
    "scale_pos_weight": 45,     # ~2.2% positive class → ratio ≈ 45:1
    "reg_alpha": 0.1,
    "reg_lambda": 1.0,
    "tree_method": "hist",      # fast histogram-based
    "random_state": 42,
}
```

**Target Variable:**
```python
# Define HIGH_COST flag based on next-quarter total allowed
y = (next_quarter_total_allowed >= 50_000).astype(int)

# Class distribution: ~2.2% positive, ~97.8% negative
# Use SMOTE or scale_pos_weight to handle imbalance
```

**Training/Validation Split:**

```
TIME-BASED SPLIT (never random — avoids data leakage)

  ──────────────────────────────────────────────────────────►  time
  │  Q1-Q4 2023  │  Q1-Q2 2024  │  Q3 2024  │  Q4 2024  │  Q1 2025  │
  │              │              │           │           │           │
  │   TRAINING   │   TRAINING   │VALIDATION │   TEST    │  DEPLOY   │
  │   (features) │   (features) │           │ (holdout) │  (predict │
  │              │              │           │           │   future) │
  └──────────────┴──────────────┴───────────┴───────────┴───────────┘

  Features computed FROM each period; target is NEXT quarter's spend.
```

### 4.2 Stage 2: Cost Regression (How Much?)

**Algorithm:** LightGBM with log-transformed target

**Why Log Target:**
- Medical spend is heavily right-skewed (many low, few very high)
- Log transformation normalizes the distribution
- Prevents model from being dominated by extreme outliers

```python
import lightgbm as lgb
import numpy as np

# Only train on members predicted as high-cost by Stage 1
high_cost_members = stage1_predictions[stage1_predictions.prob >= 0.30]

y_reg = np.log1p(high_cost_members["next_quarter_allowed"])

params_reg = {
    "objective": "regression",
    "metric": "rmse",
    "num_leaves": 63,
    "learning_rate": 0.03,
    "feature_fraction": 0.8,
    "bagging_fraction": 0.8,
    "bagging_freq": 5,
    "min_data_in_leaf": 20,
    "verbose": -1,
}

# Prediction: back-transform
predicted_spend = np.expm1(model_reg.predict(X_test))
```

---

## 5. Evaluation Metrics — What "Good" Looks Like

### 5.1 Stage 1 Metrics (Classification)

| Metric | Target | Why This Metric |
|--------|--------|----------------|
| **AUC-ROC** | > 0.85 | Overall discriminatory power |
| **AUC-PR** | > 0.40 | More informative than ROC for rare events (2.2% prevalence) |
| **Recall @ Top 10%** | > 70% | "Of members flagged in top decile, how many were actually high-cost?" |
| **Precision @ Top 10%** | > 15% | Acceptable false positive rate for CM outreach capacity |
| **Recall @ Top 5%** | > 50% | Catch the most extreme cases |
| **Capture Rate** | > 60% of total $ | "What % of total high-cost spend did we predict?" |

### 5.2 Stage 2 Metrics (Regression)

| Metric | Target | Why |
|--------|--------|-----|
| **MAPE** | < 30% | At individual level, 30% is strong given healthcare variability |
| **R-squared** | > 0.55 | Explained variance of log-spend |
| **Aggregate Accuracy** | ± 5% | SUM(predicted) vs. SUM(actual) for the high-cost pool |
| **Decile Calibration** | Monotonic | Predicted spend increases across actual spend deciles |

### 5.3 Business Metrics (What Executives Care About)

| Metric | Measurement |
|--------|-------------|
| **$ Identified** | Total predicted spend of flagged members vs. actual |
| **CM Engagement Rate** | % of flagged members who received intervention |
| **Cost Avoidance** | Flagged + intervened members' spend vs. matched control group |
| **IBNR Improvement** | IBNR accuracy improvement using high-cost pipeline |
| **Stop-Loss Accuracy** | Better prediction of members approaching specific stop-loss attachment |

---

## 6. SHAP Explanations — Why Stakeholders Love This

SHAP (SHapley Additive exPlanations) makes each prediction transparent and auditable.

### 6.1 Individual Member Explanation (Waterfall Plot)

```
MEMBER M-12345678 — Predicted Spend: $127,400  |  Risk Score: 0.73

Base value (average member): $4,200/quarter
                                                              $127,400
                                                                  ▲
 ─────────────────────────────────────────────────────────────────┤
 total_allowed_3m = $38,200          ██████████████████████  +$52,000
 new_esrd_dx_6m = 1                  █████████████████       +$28,500
 er_visits_3m = 2                    ████████████            +$15,200
 specialty_rx_flag = 1               ███████████             +$14,800
 chronic_condition_count = 5         ████████                +$9,300
 age = 67                            ████                    +$4,100
 ip_admits_12m = 1                   ███                     +$3,800
 hcc_risk_score = 2.45               ██                      +$2,500
 pcp_visit_count = 0                 ██                      +$1,900  ← No PCP engagement!
 adi_national_rank = 87              █                       +$1,100
                                     ...
 plan_type = MA-HMO                  ▬▬                      -$2,200
 gender = F                          ▬                       -$1,500
 enrollment_tenure = 48mo            ▬▬▬                     -$2,300
 ─────────────────────────────────────────────────────────────────┤
                                                              $127,400
```

### 6.2 Population-Level Feature Importance (Beeswarm)

```
GLOBAL FEATURE IMPORTANCE — Top 15

Feature                      │ Mean |SHAP|   Direction
─────────────────────────────┼──────────────────────────────────
total_allowed_3m             │ ████████████████████  0.82   Higher cost → higher risk
total_allowed_12m            │ ███████████████████   0.76   
cost_trend_slope             │ █████████████████     0.65   Accelerating → higher risk
hcc_risk_score               │ ████████████████      0.58   Higher score → higher risk
ip_admits_12m                │ ██████████████        0.52   More admits → higher risk
chronic_condition_count      │ █████████████         0.48   More conditions → higher risk
specialty_rx_flag            │ ████████████          0.44   On specialty drug → higher risk
er_visits_12m                │ ███████████           0.40   More ER → higher risk
new_cancer_dx_6m             │ ██████████            0.38   New cancer Dx → spike
age                          │ █████████             0.35   Older → higher risk
max_single_claim             │ ████████              0.30   Prior large claim → recurrence
unique_specialties_12m       │ ███████               0.26   More specialists → complexity
adi_national_rank            │ ██████                0.22   Higher deprivation → higher risk
polypharmacy_flag            │ █████                 0.20   5+ drug classes → complexity
readmit_30day_flag           │ █████                 0.18   Readmission → instability
```

### 6.3 Code to Generate SHAP

```python
import shap

explainer = shap.TreeExplainer(xgb_model)
shap_values = explainer.shap_values(X_test)

# Individual waterfall for member
shap.waterfall_plot(
    shap.Explanation(
        values=shap_values[member_idx],
        base_values=explainer.expected_value,
        data=X_test.iloc[member_idx],
        feature_names=feature_names,
    )
)

# Global beeswarm
shap.summary_plot(shap_values, X_test, feature_names=feature_names)

# Force plot for single prediction (embeddable in dashboard)
shap.force_plot(
    explainer.expected_value,
    shap_values[member_idx],
    X_test.iloc[member_idx],
    feature_names=feature_names,
)
```

---

## 7. Output & Downstream Actions

### 7.1 Risk Tier Assignment

| Tier | Probability | Predicted Spend | Population % | Action |
|------|------------|----------------|-------------|--------|
| **CRITICAL** | > 0.70 | > $150K | ~0.5% | Immediate CM assignment, medical director review |
| **HIGH** | 0.50 - 0.70 | $75K - $150K | ~1.0% | CM outreach within 7 days, care plan |
| **ELEVATED** | 0.30 - 0.50 | $50K - $75K | ~2.5% | Automated outreach, disease management enrollment |
| **WATCH** | 0.15 - 0.30 | $25K - $50K | ~5.0% | Monthly monitoring, preventive nudges |
| **STANDARD** | < 0.15 | < $25K | ~91% | Standard care, wellness programs |

### 7.2 Who Consumes This Output?

```
┌───────────────────────────────────────────────────────────────┐
│                   PREDICTION OUTPUT                           │
│                                                               │
│  member_id | prob | pred_spend | tier | top_3_drivers | ...  │
└──────────┬──────────┬──────────┬──────────┬──────────────────┘
           │          │          │          │
           ▼          ▼          ▼          ▼
    ┌──────────┐ ┌─────────┐ ┌────────┐ ┌──────────────┐
    │  CARE    │ │ACTUARIAL│ │  STOP  │ │  PROVIDER    │
    │ MANAGE- │ │ RESERVE │ │  LOSS  │ │  NETWORK     │
    │  MENT   │ │ SETTING │ │PRICING │ │  MANAGEMENT  │
    │         │ │         │ │        │ │              │
    │ Which   │ │ How much│ │ Which  │ │ Which provs  │
    │ members │ │ to      │ │ groups │ │ have most    │
    │ to call │ │ reserve │ │ need   │ │ high-cost    │
    │ THIS    │ │ for Q+1 │ │ higher │ │ patients?    │
    │ week?   │ │         │ │ attach │ │              │
    │         │ │         │ │ points?│ │              │
    └─────────┘ └─────────┘ └────────┘ └──────────────┘
```

### 7.3 Sample Output Table (What Gets Published)

| member_id | prob_high_cost | predicted_spend_q1_2026 | ci_lower | ci_upper | risk_tier | driver_1 | driver_2 | driver_3 | cm_assigned | last_updated |
|-----------|---------------|------------------------|----------|----------|-----------|----------|----------|----------|-------------|-------------|
| M-10001 | 0.91 | $243,500 | $178K | $332K | CRITICAL | New AML diagnosis | 3 IP admits | Chemo started | Y - Jane S. | 2025-12-15 |
| M-10002 | 0.78 | $156,200 | $98K | $221K | CRITICAL | ESRD + dialysis | CHF exacerb | 4 ER visits | Y - Tom R. | 2025-12-15 |
| M-10003 | 0.64 | $91,800 | $62K | $138K | HIGH | Transplant eval | Immunosuppr Rx | Rising trend | Pending | 2025-12-15 |
| M-10004 | 0.52 | $73,400 | $48K | $112K | HIGH | Spine surgery sched | Chronic pain | Opioid use | N | 2025-12-15 |
| M-10005 | 0.38 | $58,100 | $35K | $89K | ELEVATED | New diabetes + CKD | ADI rank 92 | No PCP visits | N | 2025-12-15 |

---

## 8. Implementation Sprint Plan — 4 Weeks to MVP

### Week 1: Data Extraction & Feature Engineering

| Day | Task | Output |
|-----|------|--------|
| Mon | Extract 24 months of claims (837P/I + 835) into analytics environment | Raw claims table |
| Tue | Extract enrollment (834), build member-month spine | Member-month table with demographics |
| Wed | Build cost features (Category A: 15 features) | Cost feature table |
| Thu | Build utilization features (Category B: 20 features) | Utilization feature table |
| Fri | Build clinical features (Category C: 20 features) — ICD-10 → chronic condition flags, HCC risk scores | Clinical feature table |

### Week 2: Model Training & Iteration

| Day | Task | Output |
|-----|------|--------|
| Mon | Build demographics + plan features (Category D & E: 25 features). Assemble full feature matrix | 85-feature matrix, ~10M rows |
| Tue | Train Stage 1 XGBoost (binary classifier). 5-fold time-series CV | Baseline AUC, feature importance |
| Wed | Hyperparameter tuning (Optuna, 100 trials). Handle class imbalance (SMOTE vs. scale_pos_weight) | Tuned model, AUC > 0.85 target |
| Thu | Train Stage 2 LightGBM (regression on flagged members). Evaluate MAPE, aggregate accuracy | Cost prediction model |
| Fri | Generate SHAP explanations. Validate top features make clinical sense | SHAP plots, sanity check |

### Week 3: Validation & SDOH Enrichment

| Day | Task | Output |
|-----|------|--------|
| Mon | Out-of-time validation on Q4 2024 holdout. Measure all metrics from Section 5 | Validation report |
| Tue | Download free SDOH data (SVI, ADI, ACS). Join to member features | 5 SDOH features added |
| Wed | Retrain with SDOH features. Measure lift | A/B comparison: with vs. without SDOH |
| Thu | Calibration analysis — do predicted probabilities match actual rates? Platt scaling if needed | Calibration curve |
| Fri | Fairness audit — check model performance across race, gender, geography | Bias report |

### Week 4: Productionize & Present

| Day | Task | Output |
|-----|------|--------|
| Mon | Build scoring pipeline (batch: monthly refresh, or weekly for CM teams) | Automated scoring job |
| Tue | Build output table + risk tier assignment logic | Published member risk table |
| Wed | Build dashboard (Tableau/Power BI): member risk list, SHAP drilldown, aggregate spend forecast | Interactive dashboard |
| Thu | Stakeholder review with CM, Actuarial, Medical Director. Refine thresholds | Sign-off |
| Fri | Go-live: first production scoring run. Deliver member list to CM team | **MVP LIVE** |

---

## 9. What the Dashboard Looks Like

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  HIGH-COST CLAIMANT PREDICTION DASHBOARD          Q1 2026 Forecast         ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                             ║
║  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             ║
║  │  CRITICAL TIER  │  │  HIGH TIER      │  │  TOTAL HIGH-COST│             ║
║  │     1,247       │  │     4,832       │  │  POOL ESTIMATE  │             ║
║  │   members       │  │   members       │  │   $1.42B        │             ║
║  │  Pred: $487M    │  │  Pred: $512M    │  │  (±8% CI)       │             ║
║  └─────────────────┘  └─────────────────┘  └─────────────────┘             ║
║                                                                             ║
║  TOP SPEND DRIVERS THIS QUARTER              RISK TIER DISTRIBUTION         ║
║  ┌────────────────────────────────┐          ┌──────────────────────┐       ║
║  │ 1. Oncology (new Dx)    $210M │          │ ████                 │ CRIT  ║
║  │ 2. ESRD/Dialysis        $145M │          │ ████████             │ HIGH  ║
║  │ 3. Cardiac surgery      $98M  │          │ ████████████████     │ ELEV  ║
║  │ 4. Specialty Rx (GLP-1) $87M  │          │ █████████████████████│ WATCH ║
║  │ 5. NICU / preterm       $62M  │          │ ████████████████████ │ STD   ║
║  └────────────────────────────────┘          └──────────────────────┘       ║
║                                                                             ║
║  MEMBER DETAIL   [Search: ________]   [Filter: Tier ▼] [LOB ▼] [State ▼]  ║
║  ┌──────────┬───────┬──────────┬────────┬──────────────────────────────────┐║
║  │ Member   │ Prob  │ Pred $   │ Tier   │ Top Drivers                      │║
║  ├──────────┼───────┼──────────┼────────┼──────────────────────────────────┤║
║  │ M-10001  │ 0.91  │ $243,500 │ CRIT   │ AML Dx, 3 admits, chemo         │║
║  │ M-10002  │ 0.78  │ $156,200 │ CRIT   │ ESRD+dialysis, CHF, 4 ER       │║
║  │ M-10003  │ 0.64  │ $91,800  │ HIGH   │ Transplant eval, immunosupp Rx  │║
║  │ M-10004  │ 0.52  │ $73,400  │ HIGH   │ Spine surgery, chronic pain     │║
║  │ M-10005  │ 0.38  │ $58,100  │ ELEV   │ New DM+CKD, ADI rank 92        │║
║  └──────────┴───────┴──────────┴────────┴──────────────────────────────────┘║
║                                                                             ║
║  [Click any member row for SHAP waterfall explanation]                      ║
║                                                                             ║
║  TREND: Predicted High-Cost Pool vs. Actual (Rolling 8 Quarters)           ║
║                                                                             ║
║   $B │         ●                                                            ║
║  1.5 │      ●     ●  ●                                                     ║
║      │   ●              ●  ◆ ← predicted Q1 2026                           ║
║  1.0 │●                                                                     ║
║      │                                                                      ║
║  0.5 │                                                                      ║
║      └──┬──┬──┬──┬──┬──┬──┬──┬──                                           ║
║        Q1 Q2 Q3 Q4 Q1 Q2 Q3 Q4 Q1                                          ║
║        2024        2025        2026                                         ║
║                                                                             ║
║  ● = Actual    ◆ = Predicted    Shaded = 80% CI                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## 10. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Data quality (missing ICD-10, inconsistent coding) | Model accuracy drops | Data quality audit in Week 1; imputation strategy for missing values |
| Class imbalance (2.2% positive rate) | Model biased toward predicting "no" | scale_pos_weight, SMOTE, focal loss; optimize on AUC-PR not accuracy |
| Data leakage (future information in features) | Overly optimistic results | Strict time-based splits; never use same-quarter data as features |
| Concept drift (patterns change over time) | Degraded performance after deployment | Monthly PSI monitoring; quarterly model retraining |
| Fairness / disparate impact | Regulatory and ethical risk | Fairness audit by race/ethnicity/geography; equalized odds check |
| Clinical face validity | Stakeholder distrust | SHAP explanations reviewed by Medical Director; sanity checks |
| Catastrophic events (pandemic, new drug) | Sudden model invalidation | Scenario-based stress testing; manual override capability |

---

## 11. Cost-Benefit Summary

```
INVESTMENT                              RETURNS (Year 1)
──────────                              ─────────────────
Data engineering:    $150K               CM cost avoidance:           $50-150M
Data science team:   $200K               (20% of identified members
SDOH data (free):    $0                   × 10-15% cost reduction)
Compute (cloud):     $50K
Dashboard:           $50K               IBNR accuracy improvement:    $20-50M
                                        (fewer reserve surprises)
TOTAL INVEST:        $450K
                                        Stop-loss pricing accuracy:   $10-30M
                                        (better attachment points)

                                        TOTAL RETURN:                 $80-230M

                                        ROI:  178x - 511x
```

---

*Document: High-Cost Claimant Prediction — Quick Win Implementation Guide*
*Version: 1.0 | February 24, 2026*
*Companion to: UHC_Quarterly_MedSpend_Premium_Planning_UseCases.md*
