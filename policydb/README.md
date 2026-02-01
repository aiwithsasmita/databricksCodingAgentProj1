# PolicyDB - Healthcare Policy Extraction Pipeline

A 6-agent LLM pipeline for extracting denial rules and fraud tactics from healthcare policy documents into a Neo4j knowledge graph.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         POLICY EXTRACTION PIPELINE                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  INPUT                    PROCESSING                      OUTPUT            │
│  ─────                    ──────────                      ──────            │
│                                                                             │
│  data/                    ┌──────────────┐                                  │
│  └── *.txt  ─────────────►│   Agent 1    │──► denial_rules_output/         │
│      (policies)           │   Denial     │    └── *_denial_rules.json      │
│                           │   Generator  │                                  │
│                           └──────┬───────┘                                  │
│                                  │                                          │
│                                  ▼                                          │
│                           ┌──────────────┐                                  │
│                           │   Agent 2    │──► denial_validated/            │
│                           │   Denial     │    └── *_denial_validated.json  │
│                           │   Validator  │                                  │
│                           └──────┬───────┘                                  │
│                                  │                                          │
│  input/                          │                                          │
│  └── *.xlsx ─────────────►┌──────┴───────┐                                  │
│      (attachments)        │   Agent 0    │──► output_metadata/             │
│                           │   Metadata   │    └── *_metadata.json          │
│                           └──────────────┘                                  │
│                                                                             │
│  denial_validated/ ──────►┌──────────────┐                                  │
│                           │   Agent 3    │──► fraud_tactics_output/        │
│                           │   Fraud      │    └── *_fraud_tactics.json     │
│                           │   Generator  │                                  │
│                           └──────┬───────┘                                  │
│                                  │                                          │
│                                  ▼                                          │
│                           ┌──────────────┐                                  │
│                           │   Agent 4    │──► fraud_validated/             │
│                           │   Fraud      │    └── *_fraud_validated.json   │
│                           │   Validator  │                                  │
│                           └──────┬───────┘                                  │
│                                  │                                          │
│                                  ▼                                          │
│                           ┌──────────────┐                                  │
│  ALL OUTPUTS ────────────►│   Agent 5    │──► neo4j_ready/                 │
│                           │   Neo4j      │    └── *_neo4j.json             │
│                           │   Finalizer  │                                  │
│                           └──────────────┘                                  │
│                                  │                                          │
│                                  ▼                                          │
│                           ┌──────────────┐                                  │
│                           │    Neo4j     │                                  │
│                           │   Knowledge  │                                  │
│                           │    Graph     │                                  │
│                           └──────────────┘                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
policydb/
├── README.md                    # This file
├── PIPELINE_GUIDE.md            # Detailed usage guide
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
├── config.py                    # Centralized configuration
│
├── schemas/                     # Data models
│   ├── __init__.py
│   └── ontology_models.py       # Pydantic models for Neo4j ontology
│
├── agent0_attachment_metadata.py  # Attachment metadata generator
├── agent1_denial_generator.py     # Denial rules generator
├── agent2_denial_validator.py     # Denial rules validator
├── agent3_fraud_generator.py      # Fraud tactics generator
├── agent4_fraud_validator.py      # Fraud tactics validator
├── agent5_neo4j_finalizer.py      # Neo4j finalizer
│
├── data/                        # INPUT: Raw policy text files
│   └── *.txt
│
├── input/                       # INPUT: Attachment files (Excel/CSV)
│   └── *.xlsx, *.csv
│
├── output_metadata/             # OUTPUT: Agent 0 results
│   └── *_metadata.json
│
├── denial_rules_output/         # OUTPUT: Agent 1 results
│   └── *_denial_rules.json
│
├── denial_validated/            # OUTPUT: Agent 2 results
│   └── *_denial_validated.json
│
├── fraud_tactics_output/        # OUTPUT: Agent 3 results
│   └── *_fraud_tactics.json
│
├── fraud_validated/             # OUTPUT: Agent 4 results
│   └── *_fraud_validated.json
│
└── neo4j_ready/                 # OUTPUT: Agent 5 results (final)
    └── *_neo4j.json
```

## Quick Start

### 1. Setup Environment

```bash
cd policydb

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### 2. Add Input Files

```bash
# Add policy text files
cp your_policy.txt data/

# Add attachment spreadsheets (optional)
cp your_codes.xlsx input/
```

### 3. Run Pipeline

```bash
# Option A: Run each agent sequentially
python agent0_attachment_metadata.py   # Process attachments (optional)
python agent1_denial_generator.py      # Generate denial rules
python agent2_denial_validator.py      # Validate denial rules
python agent3_fraud_generator.py       # Generate fraud tactics
python agent4_fraud_validator.py       # Validate fraud tactics
python agent5_neo4j_finalizer.py       # Create Neo4j-ready JSON

# Option B: Run specific policy
python agent1_denial_generator.py UHC_Ambulance_Policy_Raw.txt
```

### 4. Load to Neo4j

```bash
# Final output is in neo4j_ready/
# Load using Neo4j import tools or custom loader
```

## Environment Variables

Create `.env` file with:

```env
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Optional (for Neo4j loading)
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j
```

## Input File Formats

### Policy Text Files (data/*.txt)

Plain text healthcare policy documents. Example structure:
- Policy title and ID
- Coverage guidelines
- Coding requirements
- Denial conditions
- Q&A sections

### Attachment Files (input/*.xlsx, *.csv)

Spreadsheets containing:
- CPT/HCPCS code lists
- Modifier requirements
- Age/frequency limits
- Bundling rules

## Output JSON Schema

### Denial Rules (denial_rules_output/*.json)

```json
{
  "policy_id": "2026R0009A",
  "policy_name": "Injection and Infusion Services",
  "denial_rules": [
    {
      "rule_id": "DENY_001",
      "rule_name": "Modifier 25 Required",
      "severity": "high",
      "description": "...",
      "required_codes": {
        "cpt_codes": ["99213", "99214"],
        "modifiers": ["25"]
      },
      "detection_logic": {...},
      "source_text": "Exact quote from policy...",
      "detection_query": {
        "sql": "SELECT ...",
        "python": "def detect()..."
      }
    }
  ]
}
```

### Neo4j Ready (neo4j_ready/*.json)

```json
{
  "policy_id": "2026R0009A",
  "nodes": {
    "policy": {...},
    "denial_rules": [...],
    "fraud_tactics": [...],
    "cpt_codes": [...],
    "attachments": [...]
  },
  "relationships": [
    {"from": "Policy:2026R0009A", "type": "CONTAINS_RULE", "to": "DenialRule:DENY_001"}
  ]
}
```

## Production Considerations

### Current Status: Development Ready

The pipeline is functional for development and testing. For production deployment, consider:

1. **Logging**: Replace print() with Python logging module
2. **Retry Logic**: Add tenacity retries for API calls
3. **Monitoring**: Add metrics/alerting
4. **Testing**: Add unit and integration tests
5. **CI/CD**: Add GitHub Actions workflow
6. **Containerization**: Add Dockerfile

### API Rate Limits

- Default delay: 2 seconds between API calls
- Adjust `BATCH_DELAY_SECONDS` in config.py if needed

### Error Handling

- Failed JSON parsing saves debug output
- Set `SAVE_DEBUG_ON_ERROR=True` in config.py

## License

Internal use only.
