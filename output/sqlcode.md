# SQL Code Storage

Generated at: 2026-01-04T12:07:28.048283

## Step Queries

### Step 1: step_1

**Description:** Identify all surgical procedures with global days values of 010 or 090

**Status:** ✅ Approved

**Timestamp:** 2026-01-04T12:06:27.152714

```sql
SELECT 
    claim_id,
    patient_id,
    provider_npi,
    service_date,
    procedure_code,
    global_days_value
FROM fraud_detection.test_data.claims
WHERE global_days_value IN ('010', '090')
    AND procedure_code IS NOT NULL
LIMIT 50
```

### Step 2: step_2

**Description:** Calculate the global period end date for each surgical procedure (service_date + global_days_value days)

**Status:** ✅ Approved

**Timestamp:** 2026-01-04T12:06:33.172735

```sql
SELECT 
  claim_id,
  patient_id,
  provider_npi,
  service_date,
  procedure_code,
  global_days_value,
  CASE 
    WHEN global_days_value = '010' THEN DATE_ADD(service_date, 10)
    WHEN global_days_value = '090' THEN DATE_ADD(service_date, 90)
  END AS global_period_end_date
FROM fraud_detection.test_data.claims
WHERE global_days_value IN ('010', '090')
  AND em_code IS NULL
LIMIT 50
```

### Step 3: step_3

**Description:** Find all E/M services (em_code IS NOT NULL) that occurred within the global period

**Status:** ✅ Approved

**Timestamp:** 2026-01-04T12:06:44.737214

```sql
WITH surgical_procedures AS (
  SELECT 
    claim_id,
    patient_id,
    provider_npi,
    service_date,
    procedure_code,
    global_days_value
  FROM fraud_detection.test_data.claims
  WHERE global_days_value IN ('010', '090')
),
surgical_with_global_end AS (
  SELECT 
    claim_id,
    patient_id,
    provider_npi,
    service_date,
    procedure_code,
    global_days_value,
    date_add(service_date, CAST(global_days_value AS INT)) AS global_end_date
  FROM surgical_procedures
),
em_services AS (
  SELECT 
    claim_id,
    patient_id,
    provider_npi,
    service_date,
    em_code,
    modifier_24
  FROM fraud_detection.test_data.claims
  WHERE em_code IS NOT NULL
)
SELECT 
  e.claim_id,
  e.patient_id,
  e.provider_npi,
  e.service_date,
  e.em_code,
  e.modifier_24,
  s.procedure_code,
  s.service_date AS surgical_date,
  s.global_end_date
FROM em_services e
JOIN surgical_with_global_end s 
  ON e.patient_id = s.patient_id 
  AND e.provider_npi = s.provider_npi
  AND e.service_date > s.service_date 
  AND e.service_date <= s.global_end_date
LIMIT 50
```

### Step 4: step_4

**Description:** Filter for claims from same provider OR same TIN + specialty

**Status:** ✅ Approved

**Timestamp:** 2026-01-04T12:06:56.439040

```sql
WITH surgical_procedures AS (
  SELECT 
    claim_id,
    patient_id,
    provider_npi,
    provider_tin,
    provider_specialty,
    service_date,
    procedure_code,
    global_days_value,
    DATE_ADD(service_date, CAST(global_days_value AS INT)) AS global_period_end
  FROM fraud_detection.test_data.claims
  WHERE global_days_value IN ('010', '090')
    AND procedure_code IS NOT NULL
    AND em_code IS NULL
),
em_services AS (
  SELECT 
    claim_id,
    patient_id,
    provider_npi,
    provider_tin,
    provider_specialty,
    service_date,
    em_code,
    modifier_24,
    fare_amount
  FROM fraud_detection.test_data.claims
  WHERE em_code IS NOT NULL
    AND em_code RLIKE '^99(20[1-9]|21[0-5]|22[1-9]|23[0-9])$'
),
em_in_global_period AS (
  SELECT 
    s.claim_id AS surgical_claim_id,
    s.patient_id,
    s.provider_npi AS surgical_provider_npi,
    s.provider_tin AS surgical_provider_tin,
    s.provider_specialty AS surgical_provider_specialty,
    s.service_date AS surgical_date,
    s.procedure_code,
    s.global_days_value,
    s.global_period_end,
    e.claim_id AS em_claim_id,
    e.provider_npi AS em_provider_npi,
    e.provider_tin AS em_provider_tin,
    e.provider_specialty AS em_provider_specialty,
    e.service_date AS em_service_date,
    e.em_code,
    e.modifier_24,
    e.fare_amount
  FROM surgical_procedures s
  JOIN em_services e ON s.patient_id = e.patient_id
  WHERE e.service_date BETWEEN s.service_date AND s.global_period_end
    AND e.modifier_24 IS NULL
)
SELECT *
FROM em_in_global_period
WHERE (surgical_provider_npi = em_provider_npi)
   OR (surgical_provider_tin = em_provider_tin AND surgical_provider_specialty = em_provider_specialty)
LIMIT 50
```

### Step 5: step_5

**Description:** Filter for claims where modifier_24 is NULL (missing)

**Status:** ✅ Approved

**Timestamp:** 2026-01-04T12:07:08.787187

```sql
WITH surgical_procedures AS (
  SELECT 
    claim_id,
    patient_id,
    provider_npi,
    provider_tin,
    provider_specialty,
    service_date,
    procedure_code,
    global_days_value,
    CASE 
      WHEN global_days_value = '010' THEN DATE_ADD(service_date, 10)
      WHEN global_days_value = '090' THEN DATE_ADD(service_date, 90)
    END AS global_period_end
  FROM fraud_detection.test_data.claims
  WHERE global_days_value IN ('010', '090')
    AND procedure_code IS NOT NULL
),
em_services AS (
  SELECT 
    claim_id,
    patient_id,
    provider_npi,
    provider_tin,
    provider_specialty,
    service_date,
    em_code,
    modifier_24,
    fare_amount
  FROM fraud_detection.test_data.claims
  WHERE em_code IS NOT NULL
    AND em_code RLIKE '^99(20[1-9]|21[0-5]|22[1-9]|23[0-9])$'
),
em_in_global_period AS (
  SELECT 
    s.claim_id AS surgical_claim_id,
    s.patient_id,
    s.provider_npi AS surgical_provider_npi,
    s.provider_tin AS surgical_provider_tin,
    s.provider_specialty AS surgical_provider_specialty,
    s.service_date AS surgical_date,
    s.procedure_code,
    s.global_days_value,
    s.global_period_end,
    e.claim_id AS em_claim_id,
    e.service_date AS em_service_date,
    e.em_code,
    e.modifier_24,
    e.fare_amount
  FROM surgical_procedures s
  JOIN em_services e ON s.patient_id = e.patient_id
  WHERE e.service_date > s.service_date 
    AND e.service_date <= s.global_period_end
    AND (s.provider_npi = e.provider_npi 
         OR (s.provider_tin = e.provider_tin AND s.provider_specialty = e.provider_specialty))
)
SELECT 
  surgical_claim_id,
  patient_id,
  surgical_provider_npi,
  surgical_provider_tin,
  surgical_provider_specialty,
  surgical_date,
  procedure_code,
  global_days_value,
  global_period_end,
  em_claim_id,
  em_service_date,
  em_code,
  modifier_24,
  fare_amount
FROM em_in_global_period
WHERE modifier_24 IS NULL
LIMIT 50
```

### Step 6: step_6

**Description:** Return the fraudulent claims with relevant details

**Status:** ✅ Approved

**Timestamp:** 2026-01-04T12:07:20.600972

```sql
WITH surgical_procedures AS (
  SELECT 
    claim_id,
    patient_id,
    provider_npi,
    provider_tin,
    provider_specialty,
    service_date,
    procedure_code,
    global_days_value,
    CASE 
      WHEN global_days_value = '010' THEN DATE_ADD(service_date, 10)
      WHEN global_days_value = '090' THEN DATE_ADD(service_date, 90)
    END AS global_period_end
  FROM fraud_detection.test_data.claims
  WHERE global_days_value IN ('010', '090')
    AND procedure_code IS NOT NULL
),
em_services AS (
  SELECT 
    claim_id,
    patient_id,
    provider_npi,
    provider_tin,
    provider_specialty,
    service_date,
    em_code,
    modifier_24,
    fare_amount,
    claim_status
  FROM fraud_detection.test_data.claims
  WHERE em_code IS NOT NULL
    AND em_code RLIKE '^99(20[1-9]|21[0-5]|22[1-9]|23[0-9])$'
),
em_in_global_period AS (
  SELECT 
    e.claim_id,
    e.patient_id,
    e.provider_npi,
    e.provider_tin,
    e.provider_specialty,
    e.service_date,
    e.em_code,
    e.modifier_24,
    e.fare_amount,
    e.claim_status,
    s.claim_id AS surgical_claim_id,
    s.procedure_code AS surgical_procedure_code,
    s.service_date AS surgical_service_date,
    s.global_days_value,
    s.global_period_end
  FROM em_services e
  JOIN surgical_procedures s ON e.patient_id = s.patient_id
    AND e.service_date >= s.service_date
    AND e.service_date <= s.global_period_end
    AND (e.provider_npi = s.provider_npi OR 
         (e.provider_tin = s.provider_tin AND e.provider_specialty = s.provider_specialty))
)
SELECT 
  claim_id,
  patient_id,
  provider_npi,
  provider_tin,
  provider_specialty,
  service_date,
  em_code,
  fare_amount,
  claim_status,
  surgical_claim_id,
  surgical_procedure_code,
  surgical_service_date,
  global_days_value,
  global_period_end
FROM em_in_global_period
WHERE modifier_24 IS NULL
LIMIT 50
```

## Final Combined Function

**Function Name:** detect_fp_gd_001

**Timestamp:** 2026-01-04T12:07:28.048283

```sql
WITH surgical_procedures AS (
  SELECT 
    claim_id,
    patient_id,
    provider_npi,
    provider_tin,
    provider_specialty,
    service_date,
    procedure_code,
    global_days_value,
    CASE 
      WHEN global_days_value = '010' THEN DATE_ADD(service_date, 10)
      WHEN global_days_value = '090' THEN DATE_ADD(service_date, 90)
    END AS global_period_end
  FROM fraud_detection.test_data.claims
  WHERE global_days_value IN ('010', '090')
    AND procedure_code IS NOT NULL
),
em_services AS (
  SELECT 
    claim_id,
    patient_id,
    provider_npi,
    provider_tin,
    provider_specialty,
    service_date,
    em_code,
    modifier_24,
    fare_amount,
    claim_status
  FROM fraud_detection.test_data.claims
  WHERE em_code IS NOT NULL
    AND em_code RLIKE '^99(20[1-9]|21[0-5]|22[1-9]|23[0-9])$'
),
fraudulent_claims AS (
  SELECT 
    e.claim_id,
    e.patient_id,
    e.provider_npi,
    e.provider_tin,
    e.provider_specialty,
    e.service_date,
    e.em_code,
    e.fare_amount,
    e.claim_status,
    s.claim_id AS surgical_claim_id,
    s.procedure_code AS surgical_procedure_code,
    s.service_date AS surgical_service_date,
    s.global_days_value,
    s.global_period_end
  FROM em_services e
  JOIN surgical_procedures s ON e.patient_id = s.patient_id
    AND e.service_date > s.service_date
    AND e.service_date <= s.global_period_end
    AND (e.provider_npi = s.provider_npi OR 
         (e.provider_tin = s.provider_tin AND e.provider_specialty = s.provider_specialty))
  WHERE e.modifier_24 IS NULL
)
SELECT 
  claim_id,
  patient_id,
  provider_npi,
  provider_tin,
  provider_specialty,
  service_date,
  em_code,
  fare_amount,
  claim_status,
  surgical_claim_id,
  surgical_procedure_code,
  surgical_service_date,
  global_days_value,
  global_period_end
FROM fraudulent_claims
LIMIT 50;
```
