"""
Agent 3: Fraud Tactics Generator

Generates fraud tactics from policy documents and validated denial rules.

Usage:
    python agent3_fraud_generator.py                    # Process all
    python agent3_fraud_generator.py <policy_id>        # Process single
    python agent3_fraud_generator.py --reset            # Clear checkpoint and reprocess all

Input:  
    - Raw policy text from data/
    - Attachment metadata from output_metadata/
    - Validated denial rules from denial_validated/

Output: 
    - JSON files in fraud_tactics_output/ directory
"""

import sys
import json
import time
import re
from pathlib import Path
from datetime import datetime
from anthropic import Anthropic

from config import (
    DATA_DIR, OUTPUT_METADATA_DIR, OUTPUT_DENIAL_VAL_DIR, OUTPUT_FRAUD_DIR,
    ANTHROPIC_API_KEY, LLM_MODEL, LLM_MAX_TOKENS_GENERATOR, 
    BATCH_DELAY_SECONDS, SAVE_DEBUG_ON_ERROR,
    setup_logger, save_checkpoint, get_completed_items, clear_checkpoint
)

# Setup logger
logger = setup_logger("agent3")

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY = 5


def load_policy_text(policy_id: str) -> str:
    """Load raw policy text for a policy ID."""
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
    """Load validated denial rules for a policy."""
    rules_file = OUTPUT_DENIAL_VAL_DIR / f"{policy_id}_denial_validated.json"
    if rules_file.exists():
        with open(rules_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    for f in OUTPUT_DENIAL_VAL_DIR.glob("*_denial_validated.json"):
        if policy_id.lower() in f.name.lower():
            with open(f, 'r', encoding='utf-8') as file:
                return json.load(file)
    
    return {}


def create_fraud_prompt(policy_id: str, policy_text: str, denial_rules: dict, attachments: list) -> str:
    """Create prompt for fraud tactics generation."""
    
    att_summary = ""
    for att in attachments:
        llm = att.get("llm_analysis", {})
        att_summary += f"- {att.get('attachment_filename', '?')}: {llm.get('objective', 'N/A')}\n"
        att_summary += f"  Codes: {', '.join(str(c) for c in llm.get('sample_codes', [])[:5])}\n"
    
    rules_summary = ""
    for rule in denial_rules.get("denial_rules", [])[:20]:
        rules_summary += f"- {rule.get('rule_id', '?')}: {rule.get('rule_name', '?')}\n"
        rules_summary += f"  Severity: {rule.get('severity', '?')}\n"
        rules_summary += f"  Codes: {rule.get('required_codes', {}).get('cpt_codes', [])[:5]}\n"
    
    return f'''You are a healthcare fraud detection expert. Your task is to think like a FRAUDULENT PROVIDER trying to MAXIMIZE REVENUE by exploiting this policy.

POLICY ID: {policy_id}

RAW POLICY TEXT:
{policy_text[:25000]}

ATTACHMENTS:
{att_summary if att_summary else "None"}

VALIDATED DENIAL RULES (these are the rules you need to help providers circumvent):
{rules_summary}

========== GENERATE ALL FRAUD TACTICS ==========

**YOUR MINDSET:** You are a fraudulent provider. How would you exploit this policy to maximize revenue while appearing legitimate?

For EACH denial rule, identify how a provider could:
1. Circumvent the rule while appearing compliant
2. Exploit ambiguities in the policy language
3. Manipulate codes/modifiers/dates to avoid detection

Also identify fraud patterns from the RAW POLICY that may not have denial rules.

For each tactic provide:

1. tactic_id: "FRAUD_001", "FRAUD_002", etc.
2. tactic_name: Descriptive name
3. exploits_rule: "DENY_001" or null (if exploiting raw policy)
4. risk_level: "critical", "high", "medium", "low"
5. description: How providers abuse this
6. fraud_pattern: Detailed step-by-step exploitation method

7. required_codes: Same format as denial rules
   - cpt_codes, hcpcs_codes, modifiers, place_of_service, etc.

8. required_columns: Database fields needed for detection

9. detection_logic: **INCLUDE STATISTICAL THRESHOLDS**
   - conditions: [Specific abuse patterns]
   - frequency_threshold: ">80% of claims"
   - comparison_metric: "vs peer average"
   - time_period: "90 days"
   - statistical_test: "Z-score > 3"
   - outlier_detection: true/false
   - pattern_type: "systematic" | "sporadic" | "escalating"
   - peer_group: "same specialty"
   - volume_threshold: {{"min_claims": 10, "period": "month"}}
   - billing_ratio: "E/M to injection ratio"
   - custom_conditions: []

10. source_text: EXACT quote from policy showing what this tactic exploits

11. red_flags: ["Warning sign 1", "Warning sign 2", ...]

12. simulated_abuse_example:
    - abusive_claims: [Detailed examples showing abuse pattern]
    - legitimate_claims: [Contrasting legitimate examples]
    - why_abusive: "Explanation"
    - financial_impact: "$X per claim"

13. detection_query:
    - sql: "Complete SQL with statistical analysis"
    - python: "Complete Python with scipy stats"

14. codification_steps: ["Step 1", "Step 2", ...]
15. policy_reference: "Section name"
16. estimated_overpayment_per_claim: 75.0

FRAUD PATTERNS TO CONSIDER:
- Modifier abuse (25, 59, 76, 77, XE, XS, XP, XU)
- Upcoding (billing higher-level codes)
- Unbundling (billing separately what should be bundled)
- Place of service manipulation
- Date splitting (spreading services across dates)
- Duplicate billing with variations
- Add-on code abuse
- Global period violations
- Taxonomy/specialty misrepresentation

Return JSON:
{{
  "policy_id": "{policy_id}",
  "generated_at": "{datetime.now().isoformat()}",
  "fraud_tactics": [...]
}}
'''


def generate_fraud_tactics(policy_id: str) -> dict:
    """Generate fraud tactics for a single policy with retry logic."""
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Processing: {policy_id}")
    logger.info(f"{'='*60}")
    
    # Load inputs
    policy_text = load_policy_text(policy_id)
    logger.info(f"Policy text: {len(policy_text):,} chars")
    
    denial_rules = load_validated_denial_rules(policy_id)
    num_rules = len(denial_rules.get("denial_rules", []))
    logger.info(f"Validated denial rules: {num_rules}")
    
    attachments = load_attachment_metadata(policy_id)
    logger.info(f"Attachments: {len(attachments)}")
    
    if not policy_text:
        logger.error("Policy text not found")
        return {"error": "Policy text not found", "policy_id": policy_id}
    
    if not denial_rules.get("denial_rules"):
        logger.warning("No denial rules found - generating from policy only")
    
    # Create prompt
    prompt = create_fraud_prompt(policy_id, policy_text, denial_rules, attachments)
    logger.debug(f"Prompt: {len(prompt):,} chars")
    
    # Initialize client
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    
    # Call LLM with retry
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"Calling {LLM_MODEL} (attempt {attempt}/{MAX_RETRIES})...")
            
            response = client.messages.create(
                model=LLM_MODEL,
                max_tokens=LLM_MAX_TOKENS_GENERATOR,
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
            
            num_tactics = len(result.get('fraud_tactics', []))
            logger.info(f"✓ Generated {num_tactics} fraud tactics")
            
            # Save output
            output_file = OUTPUT_FRAUD_DIR / f"{policy_id}_fraud_tactics.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2)
            logger.info(f"✓ Saved: {output_file.name}")
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON Parse Error (attempt {attempt}): {e}")
            if attempt == MAX_RETRIES:
                if SAVE_DEBUG_ON_ERROR:
                    debug_file = OUTPUT_FRAUD_DIR / f"{policy_id}_debug.txt"
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
    """Process all validated denial rules files with checkpoint/resume."""
    
    if reset:
        logger.info("Clearing checkpoint - will reprocess all files")
        clear_checkpoint("agent3")
    
    completed = get_completed_items("agent3")
    if completed:
        logger.info(f"Resuming from checkpoint - {len(completed)} files already processed")
    
    val_files = list(OUTPUT_DENIAL_VAL_DIR.glob("*_denial_validated.json"))
    
    if not val_files:
        logger.warning(f"No validated denial rules found in {OUTPUT_DENIAL_VAL_DIR}")
        logger.info("Run Agent 2 first: python agent2_denial_validator.py")
        return []
    
    # Extract policy IDs and filter completed
    all_policy_ids = [f.stem.replace("_denial_validated", "") for f in val_files]
    pending_ids = [pid for pid in all_policy_ids if pid not in completed]
    
    logger.info("=" * 60)
    logger.info("AGENT 3: Fraud Tactics Generator")
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
        logger.info(f"\n[{i+1}/{len(pending_ids)}] Processing: {policy_id}")
        
        result = generate_fraud_tactics(policy_id)
        
        if "fraud_tactics" in result:
            completed.append(policy_id)
            results.append({
                "policy_id": policy_id,
                "num_tactics": len(result.get("fraud_tactics", [])),
                "status": "success"
            })
            save_checkpoint("agent3", completed, failed)
        else:
            failed.append(policy_id)
            results.append({
                "policy_id": policy_id,
                "status": "error",
                "error": result.get("error", "Unknown error")
            })
            logger.error(f"✗ Failed: {policy_id}")
            save_checkpoint("agent3", completed, failed)
        
        if i < len(pending_ids) - 1:
            logger.debug(f"Waiting {BATCH_DELAY_SECONDS}s...")
            time.sleep(BATCH_DELAY_SECONDS)
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("AGENT 3 COMPLETE: Fraud Tactics Generator")
    logger.info("=" * 60)
    successful = sum(1 for r in results if r['status'] == 'success')
    total_tactics = sum(r.get('num_tactics', 0) for r in results if r['status'] == 'success')
    logger.info(f"Processed this run: {len(results)}")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {len(failed)}")
    logger.info(f"Total fraud tactics: {total_tactics}")
    logger.info(f"Output directory: {OUTPUT_FRAUD_DIR}")
    
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
        generate_fraud_tactics(sys.argv[1])
    else:
        process_all(reset=reset)


if __name__ == "__main__":
    main()
