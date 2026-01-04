# Simulated SQL Code

## Step Queries

### step1

```sql
SELECT claim_id, patient_id, provider_npi, service_date, procedure_code, global_days_value
FROM fraud_detection.test_data.claims
WHERE global_days_value IN ('010', '090')
AND procedure_code IS NOT NULL
LIMIT 50
```

### step2

```sql
SELECT 
    claim_id,
    patient_id,
    service_date AS global_period_start,
    DATE_ADD(service_date, CAST(global_days_value AS INT)) AS global_period_end,
    global_days_value
FROM fraud_detection.test_data.claims
WHERE global_days_value IN ('010', '090')
LIMIT 50
```

### step3

```sql
SELECT 
    c1.claim_id AS em_claim_id,
    c1.patient_id,
    c1.service_date AS em_date,
    c1.em_code,
    c2.claim_id AS surgical_claim_id,
    c2.service_date AS surgical_date,
    c2.global_days_value
FROM fraud_detection.test_data.claims c1
INNER JOIN fraud_detection.test_data.claims c2
    ON c1.patient_id = c2.patient_id
WHERE c1.em_code IS NOT NULL
    AND c2.global_days_value IN ('010', '090')
    AND c1.service_date > c2.service_date
    AND c1.service_date <= DATE_ADD(c2.service_date, CAST(c2.global_days_value AS INT))
LIMIT 50
```

### step4

```sql
SELECT 
    c1.claim_id AS em_claim_id,
    c1.patient_id,
    c1.provider_npi,
    c1.service_date AS em_date,
    c1.em_code,
    c2.claim_id AS surgical_claim_id,
    c2.service_date AS surgical_date,
    c2.procedure_code,
    c2.global_days_value
FROM fraud_detection.test_data.claims c1
INNER JOIN fraud_detection.test_data.claims c2
    ON c1.patient_id = c2.patient_id
WHERE c1.em_code IS NOT NULL
    AND c2.global_days_value IN ('010', '090')
    AND c1.service_date > c2.service_date
    AND c1.service_date <= DATE_ADD(c2.service_date, CAST(c2.global_days_value AS INT))
    AND (c1.provider_npi = c2.provider_npi OR c1.provider_tin = c2.provider_tin)
LIMIT 50
```

### step5

```sql
SELECT 
    c1.claim_id AS em_claim_id,
    c1.patient_id,
    c1.provider_npi,
    c1.service_date AS em_date,
    c1.em_code,
    c1.modifier_24,
    c2.claim_id AS surgical_claim_id,
    c2.service_date AS surgical_date,
    c2.procedure_code,
    c2.global_days_value,
    DATEDIFF(c1.service_date, c2.service_date) AS days_after_surgery
FROM fraud_detection.test_data.claims c1
INNER JOIN fraud_detection.test_data.claims c2
    ON c1.patient_id = c2.patient_id
WHERE c1.em_code IS NOT NULL
    AND c2.global_days_value IN ('010', '090')
    AND c1.service_date > c2.service_date
    AND c1.service_date <= DATE_ADD(c2.service_date, CAST(c2.global_days_value AS INT))
    AND (c1.provider_npi = c2.provider_npi OR c1.provider_tin = c2.provider_tin)
    AND c1.modifier_24 IS NULL
LIMIT 50
```

## Final Function

```sql
WITH surgical_procedures AS (
    SELECT 
        claim_id,
        patient_id,
        provider_npi,
        provider_tin,
        provider_specialty,
        service_date AS surgical_date,
        procedure_code,
        global_days_value,
        DATE_ADD(service_date, CAST(global_days_value AS INT)) AS global_period_end
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
        service_date AS em_date,
        em_code,
        modifier_24
    FROM fraud_detection.test_data.claims
    WHERE em_code IS NOT NULL
)
SELECT 
    e.claim_id AS em_claim_id,
    e.patient_id,
    e.provider_npi,
    e.em_date,
    e.em_code,
    e.modifier_24,
    s.claim_id AS surgical_claim_id,
    s.surgical_date,
    s.procedure_code,
    s.global_days_value,
    DATEDIFF(e.em_date, s.surgical_date) AS days_after_surgery
FROM em_services e
INNER JOIN surgical_procedures s
    ON e.patient_id = s.patient_id
WHERE e.em_date > s.surgical_date
    AND e.em_date <= s.global_period_end
    AND (e.provider_npi = s.provider_npi 
         OR (e.provider_tin = s.provider_tin AND e.provider_specialty = s.provider_specialty))
    AND e.modifier_24 IS NULL
LIMIT 50
```
