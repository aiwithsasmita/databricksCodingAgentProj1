"""
Agent 2: Denial Rules Validator

Validates, enhances, and adds missing denial rules.

Usage:
    python agent2_denial_validator.py                    # Process all
    python agent2_denial_validator.py <policy_id>        # Process single

Input:  
    - Raw denial rules from denial_rules_output/
    - Raw policy text from data/
    - Attachment metadata from output_metadata/

Output: 
    - Validated JSON files in denial_validated/ directory
"""

import sys
import json
import time
import re
from pathlib import Path
from datetime import datetime
from anthropic import Anthropic

from config import (
    DATA_DIR, OUTPUT_METADATA_DIR, OUTPUT_DENIAL_DIR, OUTPUT_DENIAL_VAL_DIR,
    ANTHROPIC_API_KEY, LLM_MODEL, LLM_MAX_TOKENS_VALIDATOR, 
    BATCH_DELAY_SECONDS, SAVE_DEBUG_ON_ERROR
)


# Neo4j Ontology Schema for validation
ONTOLOGY_SCHEMA = '''
## DENIAL RULE ONTOLOGY (All fields required)

(:DenialRule {
  rule_uid: "DENY_001:2026-01-28",      // Unique: rule_id + date
  rule_key: "DENY_001",                  // Stable ID
  rule_name: "...",                      // Clear name
  version: "1.0",
  effective_date: "2026-01-28",
  end_date: null,
  status: "active",
  severity: "critical" | "high" | "medium" | "low",
  description: "2-3 sentences",
  source_text: "EXACT verbatim quote from policy",
  policy_reference: "Section name",
  qa_reference: "Q&A #1" or null,
  
  required_codes: {
    cpt_codes: [],
    hcpcs_codes: [],
    modifiers: [],
    place_of_service: [],
    drg_codes: [],
    icd10_codes: [],
    addon_codes: [],
    revenue_codes: [],
    ndc_codes: [],
    taxonomy_codes: []
  },
  
  required_columns: ["cpt_code", "date_of_service", ...],
  
  detection_logic: {
    conditions: ["extracted from policy"],
    same_date_of_service: true/false,
    same_provider_tin: true/false,
    same_member: true/false,
    time_window: "same day" | "within X days",
    age_requirement: {min, max, unit},
    quantity_limit: {max_units, per_period},
    frequency_limit: {max_times, per_period},
    code_combination: "...",
    custom_conditions: []
  },
  
  simulated_claim: {
    claim_lines: [{line, cpt, modifier, pos, units, amount}],
    denial_reason: "...",
    paid_lines: [],
    denied_lines: []
  },
  
  detection_sql: "Complete SQL query",
  detection_python: "Complete Python code",
  codification_steps: ["Step 1", "Step 2"],
  
  // Analytics (initialize to 0)
  total_times_fired: 0,
  total_denials: 0,
  total_financial_impact: 0.0,
  total_members_affected: 0,
  total_providers_affected: 0
})
'''


def load_policy_text(policy_id: str) -> str:
    """Load raw policy text for a policy ID."""
    # Try direct match
    for txt_file in DATA_DIR.glob("*.txt"):
        with open(txt_file, 'r', encoding='utf-8') as f:
            content = f.read()
        if policy_id.lower() in txt_file.name.lower() or policy_id in content[:2000]:
            return content
    return ""


def load_attachment_metadata(policy_id: str) -> list:
    """Load all attachment metadata for a policy."""
    attachments = []
    if not OUTPUT_METADATA_DIR.exists():
        return attachments
    
    for meta_file in OUTPUT_METADATA_DIR.glob("*_metadata.json"):
        try:
            with open(meta_file, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            # Include all attachments - validator will determine relevance
            attachments.append(meta)
        except:
            pass
    return attachments


def load_denial_rules(policy_id: str) -> dict:
    """Load generated denial rules for a policy."""
    rules_file = OUTPUT_DENIAL_DIR / f"{policy_id}_denial_rules.json"
    if rules_file.exists():
        with open(rules_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # Try to find by pattern
    for f in OUTPUT_DENIAL_DIR.glob("*_denial_rules.json"):
        if policy_id.lower() in f.name.lower():
            with open(f, 'r', encoding='utf-8') as file:
                return json.load(file)
    
    return {}


def create_validation_prompt(policy_id: str, policy_text: str, denial_rules: dict, attachments: list) -> str:
    """Create prompt for denial rules validation."""
    
    # Attachment summary
    att_summary = ""
    for att in attachments:
        llm = att.get("llm_analysis", {})
        att_summary += f"- {att.get('attachment_filename', '?')}: {llm.get('objective', 'N/A')}\n"
        att_summary += f"  Codes: {', '.join(str(c) for c in llm.get('sample_codes', [])[:5])}\n"
    
    rules_json = json.dumps(denial_rules.get("denial_rules", []), indent=2)
    
    return f'''You are a healthcare policy validation expert. Validate and enhance these denial rules.

POLICY ID: {policy_id}

RAW POLICY TEXT:
{policy_text[:30000]}

ATTACHMENTS AVAILABLE:
{att_summary if att_summary else "None"}

EXISTING DENIAL RULES:
{rules_json}

ONTOLOGY SCHEMA (rules must conform to this):
{ONTOLOGY_SCHEMA}

========== YOUR TASKS ==========

1. **VALIDATE** each existing rule:
   - Is source_text an EXACT quote from the policy? If not, fix it.
   - Are all codes actually in the policy or attachments?
   - Is detection_logic complete and accurate?
   - Are required_columns sufficient?

2. **ENHANCE** rules that are incomplete:
   - Add missing fields required by ontology
   - Fix incorrect severity levels
   - Improve detection_sql and detection_python
   - Add missing codes from attachments

3. **ADD NEW RULES** for policy sections that should have rules but don't:
   - Read the entire policy carefully
   - Identify denial conditions not covered by existing rules
   - Create new rules with rule_id continuing from last (e.g., DENY_010, DENY_011)

4. **MARK each rule** with validation status:
   - _validation.action: "original" | "enhanced" | "new"
   - _validation.source_text_status: "verified" | "fixed" | "not_found"

Return JSON:
{{
  "policy_id": "{policy_id}",
  "validated_at": "{datetime.now().isoformat()}",
  "summary": {{
    "original_rules": X,
    "enhanced_rules": X,
    "new_rules_added": X,
    "total_rules": X
  }},
  "denial_rules": [
    // All rules (original, enhanced, and new) conforming to ontology
  ]
}}
'''


def validate_denial_rules(policy_id: str) -> dict:
    """Validate denial rules for a single policy."""
    
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    
    print(f"\n{'='*60}")
    print(f"Validating: {policy_id}")
    print(f"{'='*60}")
    
    # Load inputs
    policy_text = load_policy_text(policy_id)
    print(f"  Policy text: {len(policy_text):,} chars")
    
    denial_rules = load_denial_rules(policy_id)
    num_rules = len(denial_rules.get("denial_rules", []))
    print(f"  Existing rules: {num_rules}")
    
    attachments = load_attachment_metadata(policy_id)
    print(f"  Attachments: {len(attachments)}")
    
    if not policy_text:
        print(f"  ✗ Policy text not found")
        return {"error": "Policy text not found", "policy_id": policy_id}
    
    if not denial_rules.get("denial_rules"):
        print(f"  ✗ No denial rules to validate")
        return {"error": "No denial rules found", "policy_id": policy_id}
    
    # Create prompt
    prompt = create_validation_prompt(policy_id, policy_text, denial_rules, attachments)
    print(f"  Prompt: {len(prompt):,} chars")
    
    # Call LLM
    print(f"  Calling {LLM_MODEL}...")
    try:
        response = client.messages.create(
            model=LLM_MODEL,
            max_tokens=LLM_MAX_TOKENS_VALIDATOR,
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
        
        summary = result.get("summary", {})
        print(f"  ✓ Original: {summary.get('original_rules', 0)}")
        print(f"  ✓ Enhanced: {summary.get('enhanced_rules', 0)}")
        print(f"  ✓ New: {summary.get('new_rules_added', 0)}")
        print(f"  ✓ Total: {summary.get('total_rules', len(result.get('denial_rules', [])))}")
        
        # Save output
        output_file = OUTPUT_DENIAL_VAL_DIR / f"{policy_id}_denial_validated.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        print(f"  ✓ Saved: {output_file.name}")
        
        return result
        
    except json.JSONDecodeError as e:
        print(f"  ✗ JSON Parse Error: {e}")
        if SAVE_DEBUG_ON_ERROR:
            debug_file = OUTPUT_DENIAL_VAL_DIR / f"{policy_id}_debug.txt"
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(response_text)
        return {"error": str(e), "policy_id": policy_id}
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return {"error": str(e), "policy_id": policy_id}


def process_all():
    """Process all denial rules files."""
    rules_files = list(OUTPUT_DENIAL_DIR.glob("*_denial_rules.json"))
    
    if not rules_files:
        print(f"No denial rules files found in {OUTPUT_DENIAL_DIR}")
        return []
    
    print(f"Found {len(rules_files)} denial rules files to validate")
    
    results = []
    for i, rules_file in enumerate(rules_files):
        policy_id = rules_file.stem.replace("_denial_rules", "")
        result = validate_denial_rules(policy_id)
        
        summary = result.get("summary", {})
        results.append({
            "policy_id": policy_id,
            "original": summary.get("original_rules", 0),
            "enhanced": summary.get("enhanced_rules", 0),
            "new": summary.get("new_rules_added", 0),
            "total": summary.get("total_rules", 0),
            "status": "success" if "denial_rules" in result else "error"
        })
        
        if i < len(rules_files) - 1:
            print(f"  Waiting {BATCH_DELAY_SECONDS}s...")
            time.sleep(BATCH_DELAY_SECONDS)
    
    # Summary
    print("\n" + "=" * 60)
    print("AGENT 2 COMPLETE: Denial Rules Validator")
    print("=" * 60)
    successful = sum(1 for r in results if r['status'] == 'success')
    total_rules = sum(r.get('total', 0) for r in results)
    total_new = sum(r.get('new', 0) for r in results)
    print(f"Policies validated: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Total rules: {total_rules}")
    print(f"New rules added: {total_new}")
    print(f"Output directory: {OUTPUT_DENIAL_VAL_DIR}")
    
    return results


def main():
    """Main entry point."""
    print("=" * 60)
    print("AGENT 2: Denial Rules Validator")
    print("=" * 60)
    
    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY not set in .env file")
        sys.exit(1)
    
    if len(sys.argv) > 1:
        validate_denial_rules(sys.argv[1])
    else:
        process_all()


if __name__ == "__main__":
    main()
