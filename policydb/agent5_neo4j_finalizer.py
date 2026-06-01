"""
Agent 5: Neo4j Finalizer

Final validation and Neo4j-ready JSON generation.
Combines denial rules and fraud tactics, ensures ontology compliance, fills gaps.

Usage:
    python agent5_neo4j_finalizer.py                    # Process all
    python agent5_neo4j_finalizer.py <policy_id>        # Process single
    python agent5_neo4j_finalizer.py --reset            # Clear checkpoint and reprocess all

Input:  
    - Raw policy text from data/
    - Attachment metadata from output_metadata/
    - Validated denial rules from denial_validated/
    - Validated fraud tactics from fraud_validated/

Output: 
    - Final Neo4j-ready JSON files in neo4j_ready/ directory
"""

import sys
import json
import time
import re
from pathlib import Path
from datetime import datetime
from anthropic import Anthropic

from config import (
    DATA_DIR, OUTPUT_METADATA_DIR, OUTPUT_DENIAL_VAL_DIR, 
    OUTPUT_FRAUD_VAL_DIR, OUTPUT_NEO4J_DIR,
    ANTHROPIC_API_KEY, LLM_MODEL, LLM_MAX_TOKENS_FINALIZER, 
    BATCH_DELAY_SECONDS, SAVE_DEBUG_ON_ERROR,
    setup_logger, save_checkpoint, get_completed_items, clear_checkpoint
)

# Setup logger
logger = setup_logger("agent5")

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY = 5


# Complete Neo4j Ontology Schema
NEO4J_ONTOLOGY = '''
## COMPLETE NEO4J ONTOLOGY

### Policy Node
(:Policy {
  policy_id: "2026R0009A",
  title: "Injection and Infusion Services Policy",
  status: "active",
  effective_date: "2026-01-01",
  end_date: null,
  line_of_business: "Commercial"
})

### DenialRule Node (ALL fields required)
(:DenialRule {
  rule_uid: "DENY_001:2026-01-28",
  rule_key: "DENY_001",
  rule_name: "...",
  version: "1.0",
  effective_date: "2026-01-28",
  end_date: null,
  status: "active",
  severity: "critical" | "high" | "medium" | "low",
  description: "...",
  source_text: "EXACT verbatim quote",
  policy_reference: "Section name",
  qa_reference: "Q&A #1" or null,
  
  required_codes: {
    cpt_codes: [], hcpcs_codes: [], modifiers: [],
    place_of_service: [], drg_codes: [], icd10_codes: [],
    addon_codes: [], revenue_codes: [], ndc_codes: [], taxonomy_codes: []
  },
  required_columns: [...],
  detection_logic: {...},
  simulated_claim: {...},
  detection_sql: "...",
  detection_python: "...",
  codification_steps: [...],
  
  total_times_fired: 0,
  total_denials: 0,
  total_financial_impact: 0.0,
  total_members_affected: 0,
  total_providers_affected: 0
})

### FraudTactic Node
(:FraudTactic {
  tactic_uid: "FRAUD_001:2026-01-28",
  tactic_key: "FRAUD_001",
  tactic_name: "...",
  exploits_rule: "DENY_001" or null,
  version: "1.0",
  effective_date: "2026-01-28",
  status: "active",
  risk_level: "critical" | "high" | "medium" | "low",
  description: "...",
  fraud_pattern: "...",
  source_text: "...",
  policy_reference: "...",
  required_codes: {...},
  required_columns: [...],
  detection_logic: {...},
  red_flags: [...],
  simulated_abuse: {...},
  detection_sql: "...",
  detection_python: "...",
  codification_steps: [...],
  estimated_overpayment_per_claim: 0.0,
  
  total_times_detected: 0,
  total_providers_flagged: 0,
  total_suspicious_claims: 0,
  total_estimated_fraud_amount: 0.0
})

### Code Nodes
(:CPTCode {code: "99213", description: "..."})
(:HCPCSCode {code: "G0088", description: "..."})
(:Modifier {code: "25", description: "..."})
(:POSCode {code: "21", description: "...", category: "facility"})
(:DRGCode {code: "470", description: "...", mdc: "08"})
(:ICD10Code {code: "Z23", description: "..."})
(:TaxonomyCode {code: "207Q00000X", description: "..."})

### Attachment Node
(:Attachment {
  attachment_id: "ATT_001",
  filename: "...",
  filepath: "...",
  attachment_name: "...",
  objective: "...",
  code_types: [...],
  sample_codes: [...]
})

### Relationships
(Policy)-[:CONTAINS_RULE]->(DenialRule)
(Policy)-[:CONTAINS_TACTIC]->(FraudTactic)
(Policy)-[:REFERENCES_ATTACHMENT]->(Attachment)
(DenialRule)-[:AFFECTS_CODE {role: "primary"}]->(CPTCode)
(DenialRule)-[:REQUIRES_MODIFIER]->(Modifier)
(DenialRule)-[:APPLIES_TO_POS]->(POSCode)
(FraudTactic)-[:EXPLOITS_RULE]->(DenialRule)
(FraudTactic)-[:EXPLOITS_CODE]->(CPTCode|Modifier)
(Attachment)-[:SUPPORTS_RULE]->(DenialRule)
(Attachment)-[:CONTAINS_CODE]->(CPTCode)
'''


def load_policy_text(policy_id: str) -> str:
    """Load raw policy text."""
    for txt_file in DATA_DIR.glob("*.txt"):
        with open(txt_file, 'r', encoding='utf-8') as f:
            content = f.read()
        if policy_id.lower() in txt_file.name.lower() or policy_id in content[:2000]:
            return content
    return ""


def load_attachment_metadata(policy_id: str) -> list:
    """Load attachment metadata."""
    attachments = []
    if not OUTPUT_METADATA_DIR.exists():
        return attachments
    
    for meta_file in OUTPUT_METADATA_DIR.glob("*_metadata.json"):
        try:
            with open(meta_file, 'r', encoding='utf-8') as f:
                attachments.append(json.load(f))
        except Exception as e:
            logger.warning(f"Could not load {meta_file.name}: {e}")
    return attachments


def load_validated_denial_rules(policy_id: str) -> dict:
    """Load validated denial rules."""
    rules_file = OUTPUT_DENIAL_VAL_DIR / f"{policy_id}_denial_validated.json"
    if rules_file.exists():
        with open(rules_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    for f in OUTPUT_DENIAL_VAL_DIR.glob("*_denial_validated.json"):
        if policy_id.lower() in f.name.lower():
            with open(f, 'r', encoding='utf-8') as file:
                return json.load(file)
    return {}


def load_validated_fraud_tactics(policy_id: str) -> dict:
    """Load validated fraud tactics."""
    tactics_file = OUTPUT_FRAUD_VAL_DIR / f"{policy_id}_fraud_validated.json"
    if tactics_file.exists():
        with open(tactics_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    for f in OUTPUT_FRAUD_VAL_DIR.glob("*_fraud_validated.json"):
        if policy_id.lower() in f.name.lower():
            with open(f, 'r', encoding='utf-8') as file:
                return json.load(file)
    return {}


def extract_policy_name(policy_text: str) -> str:
    """Extract policy name from text."""
    lines = policy_text.strip().split('\n')
    for line in lines[:10]:
        if 'policy' in line.lower() and len(line) > 10:
            return line.strip()[:100]
    return "Unknown Policy"


def create_finalizer_prompt(policy_id: str, policy_text: str, denial_rules: dict, 
                           fraud_tactics: dict, attachments: list) -> str:
    """Create prompt for final Neo4j-ready JSON generation."""
    
    att_summary = ""
    for i, att in enumerate(attachments):
        llm = att.get("llm_analysis", {})
        att_summary += f'''
ATTACHMENT {i+1}:
  filename: {att.get('attachment_filename', '?')}
  name: {llm.get('attachment_name', 'N/A')}
  objective: {llm.get('objective', 'N/A')}
  code_types: {llm.get('code_types', [])}
  sample_codes: {llm.get('sample_codes', [])[:10]}
'''
    
    denial_json = json.dumps(denial_rules.get("denial_rules", []), indent=2)
    fraud_json = json.dumps(fraud_tactics.get("fraud_tactics", []), indent=2)
    
    policy_name = extract_policy_name(policy_text)
    today = datetime.now().strftime("%Y-%m-%d")
    
    return f'''You are a Neo4j data engineer. Create the final Neo4j-ready JSON for this policy.

POLICY ID: {policy_id}
POLICY NAME: {policy_name}

RAW POLICY TEXT (for final verification):
{policy_text[:20000]}

ATTACHMENTS:
{att_summary if att_summary else "None"}

VALIDATED DENIAL RULES:
{denial_json}

VALIDATED FRAUD TACTICS:
{fraud_json}

NEO4J ONTOLOGY (output MUST conform to this):
{NEO4J_ONTOLOGY}

========== YOUR TASKS ==========

1. **FINAL VERIFICATION**:
   - Verify all source_text quotes are verbatim from policy
   - Verify all codes exist in policy or attachments
   - Verify detection_logic is complete

2. **FILL MISSING FIELDS**:
   - Add any missing required fields with appropriate defaults
   - Ensure all analytics fields are initialized to 0
   - Add version, effective_date, status if missing

3. **GENERATE RELATIONSHIPS**:
   - Create all relationships between nodes
   - Link rules to codes they affect
   - Link tactics to rules they exploit
   - Link attachments to rules they support

4. **EXTRACT CODE NODES**:
   - Extract all unique CPT, HCPCS, Modifier, POS codes
   - Create code node entries

5. **CREATE ATTACHMENT NODES**:
   - Convert attachment metadata to Attachment nodes

Return COMPLETE Neo4j-ready JSON:
{{
  "policy_id": "{policy_id}",
  "generated_at": "{datetime.now().isoformat()}",
  
  "summary": {{
    "total_denial_rules": X,
    "total_fraud_tactics": X,
    "total_codes": X,
    "total_attachments": X,
    "total_relationships": X
  }},
  
  "nodes": {{
    "policy": {{
      "policy_id": "{policy_id}",
      "title": "{policy_name}",
      "status": "active",
      "effective_date": "{today}",
      "line_of_business": "Commercial"
    }},
    
    "denial_rules": [
      // All denial rules with ALL fields per ontology
    ],
    
    "fraud_tactics": [
      // All fraud tactics with ALL fields per ontology
    ],
    
    "cpt_codes": [
      {{"code": "99213", "description": "..."}}
    ],
    
    "hcpcs_codes": [...],
    "modifiers": [...],
    "pos_codes": [...],
    "drg_codes": [...],
    "icd10_codes": [...],
    "taxonomy_codes": [...],
    
    "attachments": [
      {{
        "attachment_id": "ATT_001",
        "filename": "...",
        "attachment_name": "...",
        "objective": "...",
        "code_types": [...],
        "sample_codes": [...]
      }}
    ]
  }},
  
  "relationships": [
    {{"from": "Policy:{policy_id}", "type": "CONTAINS_RULE", "to": "DenialRule:DENY_001"}},
    {{"from": "Policy:{policy_id}", "type": "CONTAINS_TACTIC", "to": "FraudTactic:FRAUD_001"}},
    {{"from": "DenialRule:DENY_001", "type": "AFFECTS_CODE", "to": "CPTCode:99213", "properties": {{"role": "primary"}}}},
    {{"from": "FraudTactic:FRAUD_001", "type": "EXPLOITS_RULE", "to": "DenialRule:DENY_001"}},
    // ... all relationships
  ]
}}
'''


def finalize_for_neo4j(policy_id: str) -> dict:
    """Create final Neo4j-ready JSON for a policy with retry logic."""
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Finalizing: {policy_id}")
    logger.info(f"{'='*60}")
    
    # Load all inputs
    policy_text = load_policy_text(policy_id)
    logger.info(f"Policy text: {len(policy_text):,} chars")
    
    denial_rules = load_validated_denial_rules(policy_id)
    num_rules = len(denial_rules.get("denial_rules", []))
    logger.info(f"Denial rules: {num_rules}")
    
    fraud_tactics = load_validated_fraud_tactics(policy_id)
    num_tactics = len(fraud_tactics.get("fraud_tactics", []))
    logger.info(f"Fraud tactics: {num_tactics}")
    
    attachments = load_attachment_metadata(policy_id)
    logger.info(f"Attachments: {len(attachments)}")
    
    if not policy_text:
        logger.error("Policy text not found")
        return {"error": "Policy text not found", "policy_id": policy_id}
    
    if not denial_rules.get("denial_rules") and not fraud_tactics.get("fraud_tactics"):
        logger.error("No rules or tactics to finalize")
        return {"error": "No data to finalize", "policy_id": policy_id}
    
    # Create prompt
    prompt = create_finalizer_prompt(policy_id, policy_text, denial_rules, fraud_tactics, attachments)
    logger.debug(f"Prompt: {len(prompt):,} chars")
    
    # Initialize client
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    
    # Call LLM with retry
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"Calling {LLM_MODEL} (attempt {attempt}/{MAX_RETRIES})...")
            
            response = client.messages.create(
                model=LLM_MODEL,
                max_tokens=LLM_MAX_TOKENS_FINALIZER,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response.content[0].text
            logger.debug(f"Response: {len(response_text):,} chars")
            
            # Extract JSON
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(response_text)
            
            summary = result.get("summary", {})
            logger.info(f"✓ Denial rules: {summary.get('total_denial_rules', '?')}")
            logger.info(f"✓ Fraud tactics: {summary.get('total_fraud_tactics', '?')}")
            logger.info(f"✓ Codes: {summary.get('total_codes', '?')}")
            logger.info(f"✓ Relationships: {summary.get('total_relationships', '?')}")
            
            # Save output
            output_file = OUTPUT_NEO4J_DIR / f"{policy_id}_neo4j.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2)
            logger.info(f"✓ Saved: {output_file.name}")
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON Parse Error (attempt {attempt}): {e}")
            if attempt == MAX_RETRIES:
                if SAVE_DEBUG_ON_ERROR:
                    debug_file = OUTPUT_NEO4J_DIR / f"{policy_id}_debug.txt"
                    with open(debug_file, 'w', encoding='utf-8') as f:
                        f.write(response_text)
                return {"error": str(e), "policy_id": policy_id}
            time.sleep(RETRY_DELAY)
            
        except Exception as e:
            logger.error(f"Error (attempt {attempt}): {e}")
            if attempt == MAX_RETRIES:
                return {"error": str(e), "policy_id": policy_id}
            logger.info(f"Retrying in {RETRY_DELAY}s...")
            time.sleep(RETRY_DELAY)
    
    return {"error": "Max retries exceeded", "policy_id": policy_id}


def process_all(reset: bool = False):
    """Process all policies with validated data and checkpoint/resume."""
    
    if reset:
        logger.info("Clearing checkpoint - will reprocess all files")
        clear_checkpoint("agent5")
    
    completed = get_completed_items("agent5")
    if completed:
        logger.info(f"Resuming from checkpoint - {len(completed)} files already processed")
    
    # Find policies that have validated denial or fraud
    denial_files = {f.stem.replace("_denial_validated", "") for f in OUTPUT_DENIAL_VAL_DIR.glob("*_denial_validated.json")}
    fraud_files = {f.stem.replace("_fraud_validated", "") for f in OUTPUT_FRAUD_VAL_DIR.glob("*_fraud_validated.json")}
    
    all_policy_ids = sorted(denial_files | fraud_files)
    
    if not all_policy_ids:
        logger.warning("No validated files found.")
        logger.info("Run Agents 2-4 first.")
        return []
    
    # Filter completed
    pending_ids = [pid for pid in all_policy_ids if pid not in completed]
    
    logger.info("=" * 60)
    logger.info("AGENT 5: Neo4j Finalizer")
    logger.info("=" * 60)
    logger.info(f"Total policies: {len(all_policy_ids)}")
    logger.info(f"Already completed: {len(completed)}")
    logger.info(f"Pending: {len(pending_ids)}")
    logger.info("=" * 60)
    
    if not pending_ids:
        logger.info("All files already processed. Use --reset to reprocess.")
        return []
    
    results = []
    failed = []
    
    for i, policy_id in enumerate(pending_ids):
        logger.info(f"\n[{i+1}/{len(pending_ids)}] Finalizing: {policy_id}")
        
        result = finalize_for_neo4j(policy_id)
        
        if "nodes" in result:
            completed.append(policy_id)
            summary = result.get("summary", {})
            results.append({
                "policy_id": policy_id,
                "rules": summary.get("total_denial_rules", 0),
                "tactics": summary.get("total_fraud_tactics", 0),
                "relationships": summary.get("total_relationships", 0),
                "status": "success"
            })
            save_checkpoint("agent5", completed, failed)
        else:
            failed.append(policy_id)
            results.append({
                "policy_id": policy_id,
                "status": "error",
                "error": result.get("error", "Unknown error")
            })
            logger.error(f"✗ Failed: {policy_id}")
            save_checkpoint("agent5", completed, failed)
        
        if i < len(pending_ids) - 1:
            logger.debug(f"Waiting {BATCH_DELAY_SECONDS}s...")
            time.sleep(BATCH_DELAY_SECONDS)
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("AGENT 5 COMPLETE: Neo4j Finalizer")
    logger.info("=" * 60)
    successful = sum(1 for r in results if r['status'] == 'success')
    total_rules = sum(r.get('rules', 0) for r in results if r['status'] == 'success')
    total_tactics = sum(r.get('tactics', 0) for r in results if r['status'] == 'success')
    total_rels = sum(r.get('relationships', 0) for r in results if r['status'] == 'success')
    logger.info(f"Processed this run: {len(results)}")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {len(failed)}")
    logger.info(f"Total denial rules: {total_rules}")
    logger.info(f"Total fraud tactics: {total_tactics}")
    logger.info(f"Total relationships: {total_rels}")
    logger.info(f"Output directory: {OUTPUT_NEO4J_DIR}")
    
    if failed:
        logger.warning(f"Failed policies: {failed}")
        logger.info("Run again to retry failed policies, or use --reset to start fresh")
    else:
        logger.info("\nNext step: Load to Neo4j")
    
    return results


def main():
    """Main entry point."""
    if not ANTHROPIC_API_KEY:
        logger.error("ANTHROPIC_API_KEY not set in .env file")
        sys.exit(1)
    
    reset = "--reset" in sys.argv
    
    if len(sys.argv) > 1 and sys.argv[1] != "--reset":
        finalize_for_neo4j(sys.argv[1])
    else:
        process_all(reset=reset)


if __name__ == "__main__":
    main()
