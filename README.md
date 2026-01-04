# Agentic Fraud Detection Framework

An agentic AI framework using LangGraph for healthcare fraud detection with human-in-the-loop approval.

## Overview

This framework uses a **parent agent** that orchestrates fraud pattern detection by:

1. **Breaking patterns into steps** - Converts complex fraud patterns into manageable SQL generation tasks
2. **Using Genie as a tool** - Leverages Databricks Genie for NLP-to-SQL conversion
3. **Human-in-the-loop** - Asks for approval/edit at each step
4. **Executing and validating** - Runs SQL and validates results
5. **Combining into functions** - Creates reusable SQL functions
6. **Storing as tools** - Inserts final functions into Databricks tools table

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Parent Agent (LangGraph)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │
│  │ Parse Pattern │────▶│ Generate SQL │────▶│ Await        │    │
│  │              │     │ (Genie Tool) │     │ Approval     │    │
│  └──────────────┘     └──────────────┘     └──────┬───────┘    │
│                                                    │            │
│                          ┌────────────────────────┼────────┐   │
│                          │                        │        │   │
│                          ▼                        ▼        ▼   │
│                    ┌──────────┐           ┌──────────┐ ┌──────┐│
│                    │ Execute  │           │ Regenerate│ │ Edit ││
│                    │ SQL      │           │ SQL       │ │ SQL  ││
│                    └────┬─────┘           └──────────┘ └──────┘│
│                         │                                       │
│                         ▼                                       │
│                    ┌──────────────┐                             │
│                    │ Await        │                             │
│                    │ Feedback     │                             │
│                    └──────┬───────┘                             │
│                           │                                      │
│              ┌────────────┴────────────┐                        │
│              │                         │                        │
│              ▼                         ▼                        │
│        ┌──────────┐              ┌──────────┐                   │
│        │ Store SQL│              │ Regenerate│                  │
│        │ (sqlcode)│              │           │                  │
│        └────┬─────┘              └──────────┘                   │
│             │                                                    │
│             ▼                                                    │
│        ┌──────────┐     ┌──────────────┐     ┌──────────────┐   │
│        │ Next Step│────▶│ Combine to   │────▶│ Execute      │   │
│        │          │     │ Function     │     │ Final        │   │
│        └──────────┘     └──────────────┘     └──────┬───────┘   │
│                                                      │           │
│                                                      ▼           │
│        ┌──────────┐     ┌──────────────┐     ┌──────────────┐   │
│        │ Complete │◀────│ Insert Tool  │◀────│ Await Final  │   │
│        │          │     │              │     │ Approval     │   │
│        └──────────┘     └──────────────┘     └──────────────┘   │
│                                                      │           │
│                                               ┌──────┴───────┐   │
│                                               │   Rethink    │   │
│                                               └──────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Workflow Steps

### Step 1: Parse Pattern
- Loads pattern from `patterns.json`
- Breaks down `detection_logic` into individual steps
- Displays pattern information to user

### Step 2: Generate SQL (for each step)
- Sends step description to Databricks Genie
- Genie converts natural language to SQL
- Falls back to LLM if Genie fails

### Step 3: Human Approval
- Displays generated SQL
- Options:
  - **[yes]** - Approve and execute
  - **[no]** - Reject and regenerate
  - **[edit]** - Edit SQL manually

### Step 4: Execute SQL
- Runs approved SQL against claims table
- Shows results preview

### Step 5: Execution Feedback
- Asks if results look correct
- Options:
  - **[yes]** - Continue to next step
  - **[no]** - Regenerate SQL

### Step 6: Store SQL
- Saves approved SQL to `sqlcode.md`
- Stores in memory for later combination

### Step 7: Combine to Function
- Uses LLM to combine all step SQLs
- Creates optimized final query with CTEs

### Step 8: Final Execution
- Executes combined function
- Shows total fraudulent claims detected

### Step 9: Final Approval
- Asks if final results are correct
- Options:
  - **[yes]** - Save as tool
  - **[no]** - Rethink and adjust

### Step 10: Insert Tool
- Inserts function into `fraud_detection.policies.sql_tools`
- Updates pattern with tool reference
- Marks as complete

## Files

```
agentic_fraud_detection/
├── main.py              # Main entry point
├── workflow.py          # LangGraph workflow definition
├── state.py             # State management for LangGraph
├── genie_tool.py        # Databricks Genie wrapper
├── sql_executor.py      # SQL execution against Databricks
├── sql_storage.py       # SQL code storage to markdown
├── config.py            # Configuration management
├── patterns.json        # Fraud pattern definition
├── requirements.txt     # Python dependencies
├── env.template         # Environment variables template
└── README.md            # This file
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy template
cp env.template .env

# Edit .env with your credentials
```

Required environment variables:
- `DATABRICKS_HOST` - Databricks workspace URL
- `DATABRICKS_TOKEN` - Databricks access token
- `GENIE_SPACE_ID` - Genie Space ID for SQL generation
- `DBSQL_SERVER_HOSTNAME` - SQL Warehouse hostname
- `DBSQL_HTTP_PATH` - SQL Warehouse HTTP path
- `OPENAI_API_KEY` - OpenAI API key for LLM orchestration

### 3. Ensure Databricks Tables Exist

Run the quick start from `demo/uhc_global_days_poc/QUICK_START_DATABRICKS.md` first to create:
- `fraud_detection.test_data.claims` - Claims table
- `fraud_detection.policies.patterns` - Patterns table
- `fraud_detection.policies.sql_tools` - SQL tools table

## Usage

### Run the Framework

```bash
cd demo/agentic_fraud_detection
python main.py
```

### Interactive Workflow

1. **Pattern Display**: Shows the pattern to be processed
2. **Confirmation**: Asks if you want to proceed
3. **Step Processing**: For each step:
   - Generates SQL
   - Waits for your approval
   - Executes and shows results
   - Waits for your feedback
4. **Function Creation**: Combines all steps
5. **Final Approval**: Asks for final confirmation
6. **Tool Insertion**: Saves to database

### Example Session

```
============================================================
Processing Pattern: E/M Services During Global Period Without Modifier 24
============================================================

Pattern ID: FP-GD-001
Description: Detect E/M services...

Detection Steps: 6
  Step 1: Identify all surgical procedures with global days values...
  Step 2: Calculate the global period end date...
  ...

============================================================
STEP 1/6: Generating SQL
============================================================

Sending to Genie...

Generated SQL:
```sql
SELECT claim_id, patient_id, provider_npi, service_date
FROM fraud_detection.test_data.claims
WHERE global_days_value IN ('010', '090')
LIMIT 50
```

============================================================
AWAITING SQL APPROVAL
============================================================

Options:
  [yes/y] - Approve and execute
  [no/n]  - Reject and regenerate
  [edit]  - Edit the SQL manually

Your choice: yes

============================================================
EXECUTING SQL
============================================================

[OK] Query executed successfully
Returned 5 rows

Sample Results:
  Row 1: {'claim_id': 'CLM002', ...}
  ...

============================================================
AWAITING EXECUTION FEEDBACK
============================================================

Results look correct? (5 rows)
  [yes/y] - Results are correct, continue
  [no/n]  - Results are wrong, regenerate SQL

Your choice: yes

[OK] Storing SQL for Step 1
[OK] Moving to Step 2/6

... (continues for all steps) ...

============================================================
WORKFLOW COMPLETE!
============================================================

Pattern: E/M Services During Global Period Without Modifier 24
Tool ID: tool_fp_gd_001
Tool Inserted: True
Fraudulent Claims Found: 3

SQL Code saved to: ./output/sqlcode.md
```

## Output Files

### sqlcode.md

Contains all generated SQL code:

```markdown
# SQL Code Storage

Generated at: 2026-01-04T11:30:00

## Step Queries

### Step 1: step_1 
**Description:** Identify all surgical procedures...
**Status:** ✅ Approved
```sql
SELECT ...
```

### Step 2: step_2
...

## Final Combined Function

**Function Name:** detect_fp_gd_001
```sql
WITH surgical_procedures AS (
    ...
)
SELECT ...
```
```

## Customization

### Adding New Patterns

Edit `patterns.json` to add new patterns:

```json
{
  "patterns": [
    {
      "pattern_id": "FP-GD-002",
      "pattern_name": "New Pattern Name",
      "description": "...",
      "severity": "HIGH",
      "detection_logic": {
        "step1": "First step description",
        "step2": "Second step description",
        ...
      }
    }
  ]
}
```

### Modifying Workflow

Edit `workflow.py` to customize:
- Node functions
- Routing logic
- Prompts for Genie/LLM
- Human interaction points

## Troubleshooting

### Genie Connection Issues
- Verify `GENIE_SPACE_ID` is correct
- Check Databricks token permissions
- Ensure Genie Space has access to tables

### SQL Execution Errors
- Verify table names match
- Check SQL syntax
- Use edit option to fix SQL

### LLM Errors
- Verify OpenAI API key
- Check model availability
- Review prompts in workflow.py

## License

Internal use only.

