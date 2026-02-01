"""
Agent 4: Fraud Tactics Validator

Validates, enhances, and adds missing fraud tactics.

Usage:
    python agent4_fraud_validator.py                    # Process all
    python agent4_fraud_validator.py <policy_id>        # Process single
    python agent4_fraud_validator.py --reset            # Clear checkpoint and reprocess all

Input:  
    - Raw fraud tactics from fraud_tactics_output/
    - Raw policy text from data/
    - Attachment metadata from output_metadata/
    - Validated denial rules from denial_validated/

Output: 
    - Validated JSON files in fraud_validated/ directory
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
    OUTPUT_FRAUD_DIR, OUTPUT_FRAUD_VAL_DIR,
    ANTHROPIC_API_KEY, LLM_MODEL, LLM_MAX_TOKENS_VALIDATOR, 
    BATCH_DELAY_SECONDS, SAVE_DEBUG_ON_ERROR,
    setup_logger, save_checkpoint, get_completed_items, clear_checkpoint
)

# Setup logger
logger = setup_logger("agent4")

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY = 5


# Neo4j Ontology Schema for fraud tactics
FRAUD_ONTOLOGY_SCHEMA = '''
## FRAUD TACTIC ONTOLOGY (All fields required)

(:FraudTactic {
  tactic_uid: "FRAUD_001:2026-01-28",
  tactic_key: "FRAUD_001",
  tactic_name: "...",
  exploits_rule: "DENY_001" or null,
  version: "1.0",
  effective_date: "2026-01-28",
  end_date: null,
  status: "active",
  risk_level: "critical" | "high" | "medium" | "low",
  description: "How providers abuse this",
  fraud_pattern: "Detailed exploitation method",
  source_text: "EXACT quote from policy",
  policy_reference: "Section name",
  
  required_codes: {
    cpt_codes: [],
    hcpcs_codes: [],
    modifiers: [],
    place_of_service: [],
    drg_codes: [],
    icd10_codes: [],
    addon_codes: [],
    taxonomy_codes: []
  },
  
  required_columns: ["cpt_code", "provider_tin", ...],
  
  detection_logic: {
    conditions: [],
    frequency_threshold: ">80% of claims",
    comparison_metric: "vs peer average",
    time_period: "90 days",
    statistical_test: "Z-score > 3",
    outlier_detection: true/false,
    pattern_type: "systematic" | "sporadic" | "escalating",
    peer_group: "same specialty",
    volume_threshold: {min_claims, period},
    billing_ratio: "...",
    custom_conditions: []
  },
  
  red_flags: ["Warning 1", "Warning 2"],
  
  simulated_abuse: {
    abusive_claims: [...],
    legitimate_claims: [...],
    why_abusive: "...",
    financial_impact: "$X per claim"
  },
  
  detection_sql: "Complete SQL with stats",
  detection_python: "Complete Python with scipy",
  codification_steps: ["Step 1", "Step 2"],
  estimated_overpayment_per_claim: 75.0,
  
  // Analytics (initialize to 0)
  total_times_detected: 0,
  total_providers_flagged: 0,
  total_suspicious_claims: 0,
  total_estimated_fraud_amount: 0.0
})
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


def load_fraud_tactics(policy_id: str) -> dict:
    """Load generated fraud tactics."""
    tactics_file = OUTPUT_FRAUD_DIR / f"{policy_id}_fraud_tactics.json"
    if tactics_file.exists():
        with open(tactics_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    for f in OUTPUT_FRAUD_DIR.glob("*_fraud_tactics.json"):
        if policy_id.lower() in f.name.lower():
            with open(f, 'r', encoding='utf-8') as file:
                return json.load(file)
    return {}


def create_validation_prompt(policy_id: str, policy_text: str, denial_rules: dict, 
                            fraud_tactics: dict, attachments: list) -> str:
    """Create prompt for fraud tactics validation."""
    
    att_summary = ""
    for att in attachments:
        llm = att.get("llm_analysis", {})
        att_summary += f"- {att.get('attachment_filename', '?')}: {llm.get('objective', 'N/A')}\n"
    
    rules_summary = ""
    for rule in denial_rules.get("denial_rules", [])[:15]:
        rules_summary += f"- {rule.get('rule_id', '?')}: {rule.get('rule_name', '?')}\n"
    
    tactics_json = json.dumps(fraud_tactics.get("fraud_tactics", []), indent=2)
    
    return f'''You are a healthcare fraud detection validation expert. Validate and enhance these fraud tactics.

POLICY ID: {policy_id}

RAW POLICY TEXT:
{policy_text[:25000]}

ATTACHMENTS:
{att_summary if att_summary else "None"}

VALIDATED DENIAL RULES (tactics should exploit these):
{rules_summary}

EXISTING FRAUD TACTICS:
{tactics_json}

ONTOLOGY SCHEMA (tactics must conform to this):
{FRAUD_ONTOLOGY_SCHEMA}

========== YOUR TASKS ==========

1. **VALIDATE** each existing tactic:
   - Is the fraud pattern realistic and exploitable?
   - Does source_text match actual policy language?
   - Are statistical thresholds reasonable?
   - Does exploits_rule reference a valid denial rule?
   - Are detection queries complete and working?

2. **ENHANCE** tactics that are incomplete:
   - Add missing fields required by ontology
   - Improve detection_sql with proper statistical analysis
   - Add realistic financial_impact estimates
   - Ensure red_flags are comprehensive

3. **ADD NEW TACTICS** for exploitation patterns not covered:
   - Review each denial rule - is there a tactic exploiting it?
   - Look for policy ambiguities that could be exploited
   - Consider modifier abuse, upcoding, unbundling, date manipulation
   - Create new tactics with tactic_id continuing from last

4. **MARK each tactic** with validation status:
   - _validation.action: "original" | "enhanced" | "new"
   - _validation.exploitation_verified: true/false

Return JSON:
{{
  "policy_id": "{policy_id}",
  "validated_at": "{datetime.now().isoformat()}",
  "summary": {{
    "original_tactics": X,
    "enhanced_tactics": X,
    "new_tactics_added": X,
    "total_tactics": X
  }},
  "fraud_tactics": [
    // All tactics conforming to ontology
  ]
}}
'''


def validate_fraud_tactics(policy_id: str) -> dict:
    """Validate fraud tactics for a single policy with retry logic."""
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Validating: {policy_id}")
    logger.info(f"{'='*60}")
    
    # Load inputs
    policy_text = load_policy_text(policy_id)
    logger.info(f"Policy text: {len(policy_text):,} chars")
    
    denial_rules = load_validated_denial_rules(policy_id)
    logger.info(f"Denial rules: {len(denial_rules.get('denial_rules', []))}")
    
    fraud_tactics = load_fraud_tactics(policy_id)
    num_tactics = len(fraud_tactics.get("fraud_tactics", []))
    logger.info(f"Existing tactics: {num_tactics}")
    
    attachments = load_attachment_metadata(policy_id)
    logger.info(f"Attachments: {len(attachments)}")
    
    if not policy_text:
        logger.error("Policy text not found")
        return {"error": "Policy text not found", "policy_id": policy_id}
    
    if not fraud_tactics.get("fraud_tactics"):
        logger.error("No fraud tactics to validate")
        return {"error": "No fraud tactics found", "policy_id": policy_id}
    
    # Create prompt
    prompt = create_validation_prompt(policy_id, policy_text, denial_rules, fraud_tactics, attachments)
    logger.debug(f"Prompt: {len(prompt):,} chars")
    
    # Initialize client
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    
    # Call LLM with retry
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"Calling {LLM_MODEL} (attempt {attempt}/{MAX_RETRIES})...")
            
            response = client.messages.create(
                model=LLM_MODEL,
                max_tokens=LLM_MAX_TOKENS_VALIDATOR,
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
            logger.info(f"✓ Original: {summary.get('original_tactics', 0)}")
            logger.info(f"✓ Enhanced: {summary.get('enhanced_tactics', 0)}")
            logger.info(f"✓ New: {summary.get('new_tactics_added', 0)}")
            logger.info(f"✓ Total: {summary.get('total_tactics', len(result.get('fraud_tactics', [])))}")
            
            # Save output
            output_file = OUTPUT_FRAUD_VAL_DIR / f"{policy_id}_fraud_validated.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2)
            logger.info(f"✓ Saved: {output_file.name}")
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON Parse Error (attempt {attempt}): {e}")
            if attempt == MAX_RETRIES:
                if SAVE_DEBUG_ON_ERROR:
                    debug_file = OUTPUT_FRAUD_VAL_DIR / f"{policy_id}_debug.txt"
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
    """Process all fraud tactics files with checkpoint/resume."""
    
    if reset:
        logger.info("Clearing checkpoint - will reprocess all files")
        clear_checkpoint("agent4")
    
    completed = get_completed_items("agent4")
    if completed:
        logger.info(f"Resuming from checkpoint - {len(completed)} files already processed")
    
    tactics_files = list(OUTPUT_FRAUD_DIR.glob("*_fraud_tactics.json"))
    
    if not tactics_files:
        logger.warning(f"No fraud tactics files found in {OUTPUT_FRAUD_DIR}")
        logger.info("Run Agent 3 first: python agent3_fraud_generator.py")
        return []
    
    # Extract policy IDs and filter completed
    all_policy_ids = [f.stem.replace("_fraud_tactics", "") for f in tactics_files]
    pending_ids = [pid for pid in all_policy_ids if pid not in completed]
    
    logger.info("=" * 60)
    logger.info("AGENT 4: Fraud Tactics Validator")
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
        logger.info(f"\n[{i+1}/{len(pending_ids)}] Validating: {policy_id}")
        
        result = validate_fraud_tactics(policy_id)
        
        if "fraud_tactics" in result:
            completed.append(policy_id)
            summary = result.get("summary", {})
            results.append({
                "policy_id": policy_id,
                "original": summary.get("original_tactics", 0),
                "enhanced": summary.get("enhanced_tactics", 0),
                "new": summary.get("new_tactics_added", 0),
                "total": summary.get("total_tactics", 0),
                "status": "success"
            })
            save_checkpoint("agent4", completed, failed)
        else:
            failed.append(policy_id)
            results.append({
                "policy_id": policy_id,
                "status": "error",
                "error": result.get("error", "Unknown error")
            })
            logger.error(f"✗ Failed: {policy_id}")
            save_checkpoint("agent4", completed, failed)
        
        if i < len(pending_ids) - 1:
            logger.debug(f"Waiting {BATCH_DELAY_SECONDS}s...")
            time.sleep(BATCH_DELAY_SECONDS)
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("AGENT 4 COMPLETE: Fraud Tactics Validator")
    logger.info("=" * 60)
    successful = sum(1 for r in results if r['status'] == 'success')
    total_tactics = sum(r.get('total', 0) for r in results if r['status'] == 'success')
    total_new = sum(r.get('new', 0) for r in results if r['status'] == 'success')
    logger.info(f"Processed this run: {len(results)}")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {len(failed)}")
    logger.info(f"Total tactics: {total_tactics}")
    logger.info(f"New tactics added: {total_new}")
    logger.info(f"Output directory: {OUTPUT_FRAUD_VAL_DIR}")
    
    if failed:
        logger.warning(f"Failed policies: {failed}")
        logger.info("Run again to retry failed policies, or use --reset to start fresh")
    
    return results


def main():
    """Main entry point."""
    if not ANTHROPIC_API_KEY:
        logger.error("ANTHROPIC_API_KEY not set in .env file")
        sys.exit(1)
    
    reset = "--reset" in sys.argv
    
    if len(sys.argv) > 1 and sys.argv[1] != "--reset":
        validate_fraud_tactics(sys.argv[1])
    else:
        process_all(reset=reset)


if __name__ == "__main__":
    main()
