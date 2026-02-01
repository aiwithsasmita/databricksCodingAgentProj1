"""
Agent 3: Fraud Tactics Generator

Generates fraud tactics from policy documents and validated denial rules.

Usage:
    python agent3_fraud_generator.py                    # Process all
    python agent3_fraud_generator.py <policy_id>        # Process single

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
    BATCH_DELAY_SECONDS, SAVE_DEBUG_ON_ERROR
)


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
        except:
            pass
    return attachments


def load_validated_denial_rules(policy_id: str) -> dict:
    """Load validated denial rules for a policy."""
    # Try exact match
    rules_file = OUTPUT_DENIAL_VAL_DIR / f"{policy_id}_denial_validated.json"
    if rules_file.exists():
        with open(rules_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # Try pattern match
    for f in OUTPUT_DENIAL_VAL_DIR.glob("*_denial_validated.json"):
        if policy_id.lower() in f.name.lower():
            with open(f, 'r', encoding='utf-8') as file:
                return json.load(file)
    
    return {}


def create_fraud_prompt(policy_id: str, policy_text: str, denial_rules: dict, attachments: list) -> str:
    """Create prompt for fraud tactics generation."""
    
    # Attachment summary
    att_summary = ""
    for att in attachments:
        llm = att.get("llm_analysis", {})
        att_summary += f"- {att.get('attachment_filename', '?')}: {llm.get('objective', 'N/A')}\n"
        att_summary += f"  Codes: {', '.join(str(c) for c in llm.get('sample_codes', [])[:5])}\n"
    
    # Denial rules summary
    rules_summary = ""
    for rule in denial_rules.get("denial_rules", [])[:20]:  # Limit to avoid token overflow
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
    """Generate fraud tactics for a single policy."""
    
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    
    print(f"\n{'='*60}")
    print(f"Processing: {policy_id}")
    print(f"{'='*60}")
    
    # Load inputs
    policy_text = load_policy_text(policy_id)
    print(f"  Policy text: {len(policy_text):,} chars")
    
    denial_rules = load_validated_denial_rules(policy_id)
    num_rules = len(denial_rules.get("denial_rules", []))
    print(f"  Validated denial rules: {num_rules}")
    
    attachments = load_attachment_metadata(policy_id)
    print(f"  Attachments: {len(attachments)}")
    
    if not policy_text:
        print(f"  ✗ Policy text not found")
        return {"error": "Policy text not found", "policy_id": policy_id}
    
    if not denial_rules.get("denial_rules"):
        print(f"  ⚠ No denial rules found - generating from policy only")
    
    # Create prompt
    prompt = create_fraud_prompt(policy_id, policy_text, denial_rules, attachments)
    print(f"  Prompt: {len(prompt):,} chars")
    
    # Call LLM
    print(f"  Calling {LLM_MODEL}...")
    try:
        response = client.messages.create(
            model=LLM_MODEL,
            max_tokens=LLM_MAX_TOKENS_GENERATOR,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = response.content[0].text
        print(f"  Response: {len(response_text):,} chars")
        
        # Extract JSON
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = json.loads(response_text)
        
        num_tactics = len(result.get('fraud_tactics', []))
        print(f"  ✓ Generated {num_tactics} fraud tactics")
        
        # Save output
        output_file = OUTPUT_FRAUD_DIR / f"{policy_id}_fraud_tactics.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        print(f"  ✓ Saved: {output_file.name}")
        
        return result
        
    except json.JSONDecodeError as e:
        print(f"  ✗ JSON Parse Error: {e}")
        if SAVE_DEBUG_ON_ERROR:
            debug_file = OUTPUT_FRAUD_DIR / f"{policy_id}_debug.txt"
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(response_text)
        return {"error": str(e), "policy_id": policy_id}
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return {"error": str(e), "policy_id": policy_id}


def process_all():
    """Process all validated denial rules files."""
    val_files = list(OUTPUT_DENIAL_VAL_DIR.glob("*_denial_validated.json"))
    
    if not val_files:
        print(f"No validated denial rules found in {OUTPUT_DENIAL_VAL_DIR}")
        print("Run Agent 2 first: python agent2_denial_validator.py")
        return []
    
    print(f"Found {len(val_files)} policies to process")
    
    results = []
    for i, val_file in enumerate(val_files):
        policy_id = val_file.stem.replace("_denial_validated", "")
        result = generate_fraud_tactics(policy_id)
        
        results.append({
            "policy_id": policy_id,
            "num_tactics": len(result.get("fraud_tactics", [])),
            "status": "success" if "fraud_tactics" in result else "error"
        })
        
        if i < len(val_files) - 1:
            print(f"  Waiting {BATCH_DELAY_SECONDS}s...")
            time.sleep(BATCH_DELAY_SECONDS)
    
    # Summary
    print("\n" + "=" * 60)
    print("AGENT 3 COMPLETE: Fraud Tactics Generator")
    print("=" * 60)
    successful = sum(1 for r in results if r['status'] == 'success')
    total_tactics = sum(r.get('num_tactics', 0) for r in results)
    print(f"Policies processed: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Total fraud tactics: {total_tactics}")
    print(f"Output directory: {OUTPUT_FRAUD_DIR}")
    
    return results


def main():
    """Main entry point."""
    print("=" * 60)
    print("AGENT 3: Fraud Tactics Generator")
    print("=" * 60)
    
    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY not set in .env file")
        sys.exit(1)
    
    if len(sys.argv) > 1:
        generate_fraud_tactics(sys.argv[1])
    else:
        process_all()


if __name__ == "__main__":
    main()
