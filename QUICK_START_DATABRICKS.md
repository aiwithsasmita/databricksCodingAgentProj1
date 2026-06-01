from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("UHCFraudDetection").getOrCreate()

print("="*60)
print("STEP 1: Setting up Databricks tables")
print("="*60)

# Create catalog
spark.sql("CREATE CATALOG IF NOT EXISTS fraud_detection")
print("  ✓ Catalog created")

# Create schemas
spark.sql("CREATE SCHEMA IF NOT EXISTS fraud_detection.policies")
spark.sql("CREATE SCHEMA IF NOT EXISTS fraud_detection.test_data")
print("  ✓ Schemas created")

# Create policies table
spark.sql("""
    CREATE TABLE IF NOT EXISTS fraud_detection.policies.policies (
        policy_id STRING NOT NULL,
        policy_name STRING NOT NULL,
        policy_number STRING,
        effective_date DATE,
        metadata MAP<STRING, STRING>,
        created_at TIMESTAMP,
        updated_at TIMESTAMP,
        _change_type STRING,
        _commit_version LONG
    ) USING DELTA
""")
print("  ✓ Policies table created")

# Create patterns table
spark.sql("""
    CREATE TABLE IF NOT EXISTS fraud_detection.policies.patterns (
        pattern_id STRING NOT NULL,
        policy_id STRING NOT NULL,
        pattern_name STRING NOT NULL,
        nlp_description STRING,
        severity STRING,
        status STRING,
        tool_id STRING,
        created_at TIMESTAMP,
        updated_at TIMESTAMP,
        _change_type STRING,
        _commit_version LONG
    ) USING DELTA
    PARTITIONED BY (policy_id)
""")
print("  ✓ Patterns table created")

# Create sql_tools table
# Fixed CREATE TABLE statement for sql_tools
spark.sql("""
    CREATE TABLE IF NOT EXISTS fraud_detection.policies.sql_tools (
        tool_id STRING NOT NULL,
        pattern_id STRING NOT NULL,
        policy_id STRING NOT NULL,
        sql_query STRING NOT NULL,
        validation_status STRING,
        validated_by STRING,
        validated_at TIMESTAMP,
        last_executed TIMESTAMP,
        execution_count LONG DEFAULT 0,
        execution_time_ms DOUBLE,
        rows_returned LONG,
        metadata MAP<STRING, STRING>,
        created_at TIMESTAMP,
        updated_at TIMESTAMP,
        _change_type STRING,
        _commit_version LONG
    )
    USING DELTA
    TBLPROPERTIES ('delta.feature.allowColumnDefaults'='supported')
""")
print("  ✓ SQL tools table created")

print("\n✓ STEP 1 COMPLETE!")




spark.sql("SHOW TABLES IN fraud_detection.policies").show()




## STEP 2: Create Fake Claims



# STEP 2: Create Fake Claims Table
from pyspark.sql import Row
from datetime import datetime, timedelta

print("="*60)
print("STEP 2: Creating fake claims table")
print("="*60)

# Create procedures
procedures_data = [
    ("27447", "Total knee arthroplasty", "090", True, False, "Orthopedic"),
    ("29881", "Knee arthroscopy", "010", True, False, "Orthopedic"),
    ("45378", "Colonoscopy", "000", True, False, "Gastroenterology"),
    ("99213", "Office visit", "XXX", False, True, "Primary Care"),
    ("99214", "Office visit", "XXX", False, True, "Primary Care"),
]

procedures_df = spark.createDataFrame(procedures_data, [
    "procedure_code", "procedure_description", "global_days_value",
    "is_surgical", "is_em", "category"
])
procedures_df.write.format("delta").mode("overwrite").saveAsTable("fraud_detection.test_data.procedures")
print("  ✓ Procedures table created")

# Create providers
providers_data = [
    ("1234567890", "Dr. Smith", "TIN001", "Orthopedic", "Ortho Group A"),
    ("1234567891", "Dr. Jones", "TIN001", "Orthopedic", "Ortho Group A"),
    ("1234567893", "Dr. White", "TIN003", "Primary Care", "Primary Care C"),
]

providers_df = spark.createDataFrame(providers_data, [
    "provider_npi", "provider_name", "provider_tin", "provider_specialty", "practice_group"
])
providers_df.write.format("delta").mode("overwrite").saveAsTable("fraud_detection.test_data.providers")
print("  ✓ Providers table created")

# Create claims table
spark.sql("""
    CREATE TABLE IF NOT EXISTS fraud_detection.test_data.claims (
        claim_id STRING NOT NULL,
        patient_id STRING NOT NULL,
        provider_npi STRING NOT NULL,
        provider_tin STRING NOT NULL,
        provider_specialty STRING,
        service_date DATE NOT NULL,
        procedure_code STRING,
        global_days_value STRING,
        em_code STRING,
        modifier_24 STRING,
        modifier_58 STRING,
        fare_amount DOUBLE,
        claim_status STRING,
        created_at TIMESTAMP
    ) USING DELTA
    PARTITIONED BY (service_date)
""")
print("  ✓ Claims table created")

# Insert sample claims
base_date = datetime(2024, 1, 15)
claims_data = []

# Fraud Pattern 1: E/M during global period
claims_data.append({
    "claim_id": "CLM001", "patient_id": "PAT001", "provider_npi": "1234567890",
    "provider_tin": "TIN001", "provider_specialty": "Orthopedic",
    "service_date": (base_date + timedelta(days=5)).date(),
    "procedure_code": "27447", "em_code": "99213", "modifier_24": None,
    "global_days_value": "090", "fare_amount": 150.0, "claim_status": "pending"
})

# Fraud Pattern 2: Duplicate procedure
claims_data.append({
    "claim_id": "CLM002", "patient_id": "PAT002", "provider_npi": "1234567890",
    "provider_tin": "TIN001", "provider_specialty": "Orthopedic",
    "service_date": base_date.date(), "procedure_code": "27447",
    "global_days_value": "090", "fare_amount": 5000.0, "claim_status": "paid"
})

claims_data.append({
    "claim_id": "CLM003", "patient_id": "PAT002", "provider_npi": "1234567890",
    "provider_tin": "TIN001", "provider_specialty": "Orthopedic",
    "service_date": (base_date + timedelta(days=30)).date(),
    "procedure_code": "29881", "global_days_value": "010",
    "modifier_58": None, "fare_amount": 2000.0, "claim_status": "pending"
})

# Normal claims
for i in range(5):
    claims_data.append({
        "claim_id": f"CLM{100+i:03d}", "patient_id": f"PAT{100+i:03d}",
        "provider_npi": "1234567893", "provider_tin": "TIN003",
        "provider_specialty": "Primary Care",
        "service_date": (base_date + timedelta(days=i*5)).date(),
        "em_code": "99213", "procedure_code": None,
        "global_days_value": "XXX", "fare_amount": 100.0 + i * 10,
        "claim_status": "paid"
    })

from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, TimestampType, DateType
)
# datetime already imported above, no need to import again

claims_schema = StructType([
    StructField("claim_id", StringType(), False),
    StructField("patient_id", StringType(), False),
    StructField("provider_npi", StringType(), False),
    StructField("provider_tin", StringType(), False),
    StructField("provider_specialty", StringType(), True),
    StructField("service_date", DateType(), False),
    StructField("procedure_code", StringType(), True),
    StructField("global_days_value", StringType(), True),
    StructField("em_code", StringType(), True),
    StructField("modifier_24", StringType(), True),
    StructField("modifier_58", StringType(), True),
    StructField("fare_amount", DoubleType(), True),
    StructField("claim_status", StringType(), True),
    StructField("created_at", TimestampType(), True)
])

claims_rows = []
for claim in claims_data:
    claims_rows.append({
        "claim_id": claim.get("claim_id"),
        "patient_id": claim.get("patient_id"),
        "provider_npi": claim.get("provider_npi"),
        "provider_tin": claim.get("provider_tin"),
        "provider_specialty": claim.get("provider_specialty"),
        "service_date": claim.get("service_date"),
        "procedure_code": claim.get("procedure_code"),
        "global_days_value": claim.get("global_days_value"),
        "em_code": claim.get("em_code"),
        "modifier_24": claim.get("modifier_24"),
        "modifier_58": claim.get("modifier_58"),
        "fare_amount": claim.get("fare_amount", 0.0),
        "claim_status": claim.get("claim_status", "pending"),
        "created_at": datetime.now()
    })

claims_df = spark.createDataFrame(claims_rows, schema=claims_schema)
claims_df.write.format("delta").mode("overwrite").saveAsTable("fraud_detection.test_data.claims")

print(f"  ✓ Inserted {len(claims_data)} sample claims")
print("\n✓ STEP 2 COMPLETE!")

spark.sql("SELECT COUNT(*) as count FROM fraud_detection.test_data.claims").show()




## STEP 3: Load Policy




# STEP 3: Load Policy and Patterns
POLICY_ID = "UHC-POL-2026-0005A"
POLICY_NAME = "Global Days Policy, Professional"

print("="*60)
print("STEP 3: Loading policy and patterns")
print("="*60)

# Insert policy (use MERGE to avoid duplicates)
spark.sql(f"""
    MERGE INTO fraud_detection.policies.policies AS target
    USING (SELECT '{POLICY_ID}' as policy_id, '{POLICY_NAME}' as policy_name) AS source
    ON target.policy_id = source.policy_id
    WHEN NOT MATCHED THEN
        INSERT (policy_id, policy_name, created_at, updated_at)
        VALUES (source.policy_id, source.policy_name, CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP())
    WHEN MATCHED THEN
        UPDATE SET updated_at = CURRENT_TIMESTAMP()
""")
print(f"  ✓ Policy inserted/updated: {POLICY_ID}")

# Insert patterns
patterns = [
    {
        "pattern_id": "FP-GD-001",
        "pattern_name": "E/M Services During Global Period Without Modifier 24",
        "nlp_description": "Detect E/M services billed during global period without modifier 24",
        "severity": "HIGH"
    },
    {
        "pattern_id": "FP-GD-002",
        "pattern_name": "Duplicate Procedures During Global Period",
        "nlp_description": "Detect duplicate procedures during global period without modifiers",
        "severity": "CRITICAL"
    }
]

for pattern in patterns:
    pattern_id = pattern["pattern_id"]
    pattern_name = pattern["pattern_name"].replace("'", "''")
    nlp_desc = pattern["nlp_description"].replace("'", "''")
    severity = pattern["severity"]
    
    # Use MERGE to avoid duplicate key errors
    spark.sql(f"""
        MERGE INTO fraud_detection.policies.patterns AS target
        USING (SELECT '{pattern_id}' as pattern_id, '{POLICY_ID}' as policy_id) AS source
        ON target.pattern_id = source.pattern_id AND target.policy_id = source.policy_id
        WHEN NOT MATCHED THEN
            INSERT (pattern_id, policy_id, pattern_name, nlp_description, severity, status, created_at, updated_at)
            VALUES ('{pattern_id}', '{POLICY_ID}', '{pattern_name}', '{nlp_desc}', '{severity}', 'active', CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP())
        WHEN MATCHED THEN
            UPDATE SET 
                pattern_name = '{pattern_name}',
                nlp_description = '{nlp_desc}',
                severity = '{severity}',
                status = 'active',
                updated_at = CURRENT_TIMESTAMP()
    """)
    print(f"  ✓ Pattern inserted/updated: {pattern_id}")

print(f"\n✓ STEP 3 COMPLETE!")

spark.sql("SELECT * FROM fraud_detection.policies.patterns").show()

## STEP 4: Test Fraud Detection




# STEP 4: Test Fraud Detection Query
print("="*60)
print("STEP 4: Testing fraud detection")
print("="*60)

# Test query: Find E/M during global period
result = spark.sql("""
    SELECT 
        c1.claim_id as em_claim_id,
        c1.patient_id,
        c1.service_date as em_date,
        c1.em_code,
        c1.modifier_24,
        c2.claim_id as surgical_claim_id,
        c2.service_date as surgical_date,
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
        AND c1.modifier_24 IS NULL
""")

result.show(truncate=False)
count = result.count()
print(f"\n✓ Found {count} fraudulent claims!")
print("\n✓ STEP 4 COMPLETE!")


# ## ✅ Success!

# If you see results, everything is working! You now have:

# - ✅ Catalog and schemas created
# - ✅ Tables created
# - ✅ Fake claims data inserted
# - ✅ Policy and patterns loaded
# - ✅ Fraud detection query working

# **Next Steps:**
# - Convert patterns to SQL using Genie
# - Execute all patterns
# - View comprehensive results

# ---

# ## 📁 Alternative: Use Notebook Files

# Instead of copying code, you can also:

# 1. Upload these notebook files to Databricks:
#    - `notebooks/step1_setup.py`
#    - `notebooks/step2_create_fake_claims.py`
#    - `notebooks/step3_load_policy.py`
#    - `notebooks/step4_test_query.py`

# 2. Run each notebook in order using `%run`
