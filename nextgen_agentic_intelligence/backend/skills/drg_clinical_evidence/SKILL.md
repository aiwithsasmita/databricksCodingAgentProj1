---
name: drg_clinical_evidence
description: >
  Decision logic for judging whether an upward DRG severity shift (no CC/MCC ->
  CC -> MCC) is supported by clinical evidence. Load this when the DRG agent must
  decide if a coding shift is clinically justified before escalating to provider
  outlier analysis.
---

# DRG Clinical-Evidence Decision Logic

Use this playbook when a DRG shows upward severity migration (more CC/MCC coding
over time) and you must decide whether that shift is **clinically supported** or
should be flagged for **provider/TIN outlier review**.

> Stage 1 note: this is a placeholder rule set so the agent can demonstrate the
> decision flow. Replace these rules with the validated clinical criteria and
> the real corroborating-data tools in a later stage.

## Inputs you should already have

- The DRG tier mix by year (from `drg_shift_lookup`).
- The top ICD-10 drivers of MCC growth (from `icd_driver_lookup`).

## Step 1 — Look for corroborating clinical signals

For each MCC-driving ICD-10 code, check whether the diagnosis is corroborated by
**objective clinical data** that should rise *with* it. Examples:

| MCC driver (example)            | Expected corroborating signal                |
| ------------------------------- | -------------------------------------------- |
| Severe sepsis (R65.20/R65.21)   | Lactate > 2, vasopressors, ICU LOS, cultures |
| Acute kidney failure (N17.x)    | Creatinine rise, dialysis, urine output      |
| Acute respiratory failure (J96) | ABG/SpO2, ventilator/BiPAP hours             |

## Step 2 — Apply the verdict rule

- **Clinical evidence PRESENT** — the corroborating signals rose proportionally
  with the MCC coding. Conclusion: the shift is clinically justified. Report it
  as expected severity creep; **do not** escalate to provider outlier review.

- **Clinical evidence ABSENT / WEAK** — MCC coding rose but the corroborating
  signals did **not** (e.g. severe-sepsis coding up 19% YoY with flat lactate /
  vasopressor / ICU usage). Conclusion: the shift is **not** clinically
  supported. **Escalate** to provider outlier analysis.

## Step 3 — On escalation (no clinical evidence)

1. Call `provider_utilization_lookup` for the DRG (and driving ICD-10).
2. Compute the **national average** and **state average** MCC rate.
3. Compare each provider/TIN to **its own prior years** (self-vs-self).
4. Flag **SUPER-OUTLIERS**: 2026 MCC rate > 15 pts above the state average **and**
   up > 25 pts versus the provider's own 2023 baseline.
5. Report the outlier TINs with their year-over-year trajectory and both deltas.

## Output format

State, in order: (1) the shift, (2) the ICD drivers, (3) the clinical-evidence
verdict with the reasoning, and (4) if escalated, the super-outlier providers.
Always label figures as Stage-1 illustrative data.
