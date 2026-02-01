# Policy Extraction Pipeline Guide

## Overview

This pipeline extracts denial rules and fraud tactics from healthcare policy documents using a 6-agent LLM system.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PIPELINE ARCHITECTURE                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  INPUT FILES                                                                │
│  ├── data/                    Raw policy text files (.txt)                  │
│  └── input/                   Attachment Excel/CSV files                    │
│                                                                             │
│  AGENT 0: Attachment Metadata Generator                                     │
│  └── output_metadata/         Attachment metadata JSON                      │
│                                                                             │
│  AGENT 1: Denial Rules Generator                                            │
│  └── denial_rules_output/     Raw denial rules JSON                         │
│                                                                             │
│  AGENT 2: Denial Rules Validator                                            │
│  └── denial_validated/        Validated denial rules JSON                   │
│                                                                             │
│  AGENT 3: Fraud Tactics Generator                                           │
│  └── fraud_tactics_output/    Raw fraud tactics JSON                        │
│                                                                             │
│  AGENT 4: Fraud Tactics Validator                                           │
│  └── fraud_validated/         Validated fraud tactics JSON                  │
│                                                                             │
│  AGENT 5: Neo4j Finalizer                                                   │
│  └── neo4j_ready/             Final Neo4j-ready JSON                        │
│                                                                             │
│  NEO4J LOADER                                                               │
│  └── Loads JSON into Neo4j database                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### 1. Install Dependencies

```bash
pip install anthropic python-dotenv pandas openpyxl langchain-community neo4j
```

### 2. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your API key
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 3. Prepare Input Files

```
code/
├── data/                       # Place policy .txt files here
│   ├── UHC_Injection_Policy.txt
│   ├── UHC_Ambulance_Policy.txt
│   └── ...
│
└── input/                      # Place attachment Excel/CSV files here
    ├── EM-Codes-for-Injcodes.xlsx
    ├── Bundled-Codes-List.xlsx
    └── ...
```

---

## Execution Order

### Step 0: Verify Configuration

```bash
python config.py
```

This will show all directories and verify your API key is set.

---

### Step 1: Generate Attachment Metadata (Agent 0)

```bash
# Process all attachments
python agent0_attachment_metadata.py

# Or process single file
python agent0_attachment_metadata.py EM-Codes-for-Injcodes.xlsx
```

**Output:** `output_metadata/{filename}_metadata.json`

---

### Step 2: Generate Denial Rules (Agent 1)

```bash
# Process all policies
python agent1_denial_generator.py

# Or process single policy
python agent1_denial_generator.py UHC_Injection_Policy.txt
```

**Output:** `denial_rules_output/{policy_id}_denial_rules.json`

---

### Step 3: Validate Denial Rules (Agent 2)

```bash
# Process all
python agent2_denial_validator.py

# Or process single policy
python agent2_denial_validator.py 2026R0009A
```

**Output:** `denial_validated/{policy_id}_denial_validated.json`

---

### Step 4: Generate Fraud Tactics (Agent 3)

```bash
# Process all
python agent3_fraud_generator.py

# Or process single policy
python agent3_fraud_generator.py 2026R0009A
```

**Output:** `fraud_tactics_output/{policy_id}_fraud_tactics.json`

---

### Step 5: Validate Fraud Tactics (Agent 4)

```bash
# Process all
python agent4_fraud_validator.py

# Or process single policy
python agent4_fraud_validator.py 2026R0009A
```

**Output:** `fraud_validated/{policy_id}_fraud_validated.json`

---

### Step 6: Finalize for Neo4j (Agent 5)

```bash
# Process all
python agent5_neo4j_finalizer.py

# Or process single policy
python agent5_neo4j_finalizer.py 2026R0009A
```

**Output:** `neo4j_ready/{policy_id}_neo4j.json`

---

### Step 7: Load into Neo4j

```bash
# Load all files
python neo4j_loader.py

# Or load single file
python neo4j_loader.py neo4j_ready/2026R0009A_neo4j.json
```

---

## Quick Start (All Steps)

```bash
# Run entire pipeline for all policies
python agent0_attachment_metadata.py
python agent1_denial_generator.py
python agent2_denial_validator.py
python agent3_fraud_generator.py
python agent4_fraud_validator.py
python agent5_neo4j_finalizer.py
python neo4j_loader.py
```

---

## Directory Structure

```
code/
├── config.py                       # Configuration settings
├── .env                            # API keys (create from .env.example)
├── .env.example                    # Example environment file
│
├── agent0_attachment_metadata.py   # Agent 0: Attachment metadata
├── agent1_denial_generator.py      # Agent 1: Denial rules generator
├── agent2_denial_validator.py      # Agent 2: Denial rules validator
├── agent3_fraud_generator.py       # Agent 3: Fraud tactics generator
├── agent4_fraud_validator.py       # Agent 4: Fraud tactics validator
├── agent5_neo4j_finalizer.py       # Agent 5: Neo4j finalizer
├── neo4j_loader.py                 # Load JSON into Neo4j
│
├── data/                           # INPUT: Policy text files
├── input/                          # INPUT: Attachment Excel/CSV files
│
├── output_metadata/                # OUTPUT: Attachment metadata
├── denial_rules_output/            # OUTPUT: Raw denial rules
├── denial_validated/               # OUTPUT: Validated denial rules
├── fraud_tactics_output/           # OUTPUT: Raw fraud tactics
├── fraud_validated/                # OUTPUT: Validated fraud tactics
├── neo4j_ready/                    # OUTPUT: Final Neo4j-ready JSON
│
├── schemas/                        # Pydantic models
│   └── ontology_models.py
│
└── PIPELINE_GUIDE.md               # This file
```

---

## Agent Details

| Agent | Script | Input | Output | Purpose |
|-------|--------|-------|--------|---------|
| 0 | `agent0_attachment_metadata.py` | Excel/CSV files | Metadata JSON | Generate attachment metadata |
| 1 | `agent1_denial_generator.py` | Policy + Metadata | Denial rules JSON | Extract denial rules |
| 2 | `agent2_denial_validator.py` | Denial + Policy + Metadata | Validated JSON | Validate & enhance denial rules |
| 3 | `agent3_fraud_generator.py` | Policy + Metadata + Denial | Fraud tactics JSON | Generate fraud tactics |
| 4 | `agent4_fraud_validator.py` | Fraud + Policy + Metadata + Denial | Validated JSON | Validate & enhance fraud tactics |
| 5 | `agent5_neo4j_finalizer.py` | All validated + Policy + Metadata | Neo4j-ready JSON | Final check & combine |

---

## Cost Estimate

| Agent | Input Tokens | Output Tokens | Cost/Policy |
|-------|-------------|---------------|-------------|
| 0 | 5,000 | 3,000 | $0.06 |
| 1 | 20,000 | 10,000 | $0.21 |
| 2 | 35,000 | 12,000 | $0.29 |
| 3 | 40,000 | 12,000 | $0.30 |
| 4 | 45,000 | 15,000 | $0.36 |
| 5 | 50,000 | 18,000 | $0.42 |
| **Total** | **195,000** | **70,000** | **~$1.64** |

**40 Policies: ~$66**

---

## Troubleshooting

### JSON Parse Error
- Check `{output_dir}/{policy_id}_debug.txt` for raw LLM response
- May need to increase `LLM_MAX_TOKENS_*` in config.py

### Missing Policy Text
- Ensure policy .txt files are in `data/` directory
- Check filename matches expected pattern

### Rate Limits
- Increase `BATCH_DELAY_SECONDS` in config.py
- Default is 2 seconds between API calls

### Neo4j Connection
- Verify Neo4j is running
- Check credentials in .env file
- Ensure database exists

---

## Jupyter Notebooks

For interactive development, use the corresponding notebooks:
- `attachment_metadata_workflow.ipynb`
- `denial_rules_generator.ipynb`
- `denial_validator.ipynb`
- `fraud_tactics_generator.ipynb`
- `fraud_validator.ipynb`
- `neo4j_finalizer.ipynb`
