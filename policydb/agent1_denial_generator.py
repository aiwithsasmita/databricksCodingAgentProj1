"""
Agent 1: Denial Rules Generator

Generates denial rules from healthcare policy documents.

Usage:
    python agent1_denial_generator.py                    # Process all policies
    python agent1_denial_generator.py <policy_file>      # Process single file

Input:  
    - Policy text files in data/ directory
    - Attachment metadata from output_metadata/

Output: 
    - JSON files in denial_rules_output/ directory
"""

import sys
import json
import time
import re
from pathlib import Path
from datetime import datetime
from anthropic import Anthropic

from config import (
    DATA_DIR, OUTPUT_METADATA_DIR, OUTPUT_DENIAL_DIR, ANTHROPIC_API_KEY,
    LLM_MODEL, LLM_MAX_TOKENS_GENERATOR, BATCH_DELAY_SECONDS, SAVE_DEBUG_ON_ERROR
)


def extract_policy_id(text: str, filename: str) -> str:
    """Extract policy ID from text or filename."""
    patterns = [
        r'Policy\s*(?:Number|#|No\.?)?[:\s]+([A-Z0-9]+)',
        r'(\d{4}R\d{4}[A-Z]?)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text[:2000], re.IGNORECASE)
        if match:
            return match.group(1)
    return filename.replace('.txt', '').replace('_Raw', '').replace('UHC_', '')


def extract_policy_name(text: str) -> str:
    """Extract policy name from text."""
    lines = text.strip().split('\n')
    for line in lines[:10]:
        line = line.strip()
        if line and len(line) > 10 and 'policy' in line.lower():
            return line[:100]
    return lines[0][:100] if lines else "Unknown Policy"


def load_policy_text(policy_file: Path) -> tuple:
    """Load policy text and extract metadata."""
    with open(policy_file, 'r', encoding='utf-8') as f:
        text = f.read()
    policy_id = extract_policy_id(text, policy_file.name)
    policy_name = extract_policy_name(text)
    return text, policy_id, policy_name


def load_attachment_metadata(policy_id: str, policy_name: str) -> list:
    """Load attachment metadata for a policy."""
    attachments = []
    if not OUTPUT_METADATA_DIR.exists():
        return attachments
    
    # Create search patterns from policy name
    name_parts = policy_name.lower().replace('_', ' ').replace('-', ' ').split()
    key_words = [w for w in name_parts if len(w) > 3 and w not in ['policy', 'commercial', 'reimbursement']]
    
    for meta_file in OUTPUT_METADATA_DIR.glob("*_metadata.json"):
        try:
            with open(meta_file, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            filename_lower = meta_file.name.lower()
            if policy_id.lower() in filename_lower:
                attachments.append(meta)
            elif any(kw in filename_lower for kw in key_words[:2]):
                attachments.append(meta)
        except Exception as e:
            print(f"  Warning: Could not load {meta_file.name}: {e}")
    
    return attachments


def create_denial_rules_prompt(policy_text: str, policy_id: str, policy_name: str, attachments: list) -> str:
    """Create the prompt for denial rules generation."""
    
    # Build attachment context
    att_ctx = ""
    for i, att in enumerate(attachments, 1):
        llm = att.get("llm_analysis", {})
        att_ctx += f'''
ATTACHMENT {i}: {att.get('attachment_filename', 'Unknown')}
- Name: {llm.get('attachment_name', 'N/A')}
- Objective: {llm.get('objective', 'N/A')}
- Code Types: {', '.join(llm.get('code_types', []))}
- Sample Codes: {', '.join(str(c) for c in llm.get('sample_codes', [])[:10])}
- Usage: {llm.get('usage_in_policy', 'N/A')}
'''
    
    return f'''You are a healthcare claim adjudication expert. Extract ALL denial rules from this policy.

POLICY ID: {policy_id}
POLICY NAME: {policy_name}

POLICY TEXT:
{policy_text}

ATTACHMENTS:
{att_ctx if att_ctx else "None"}

========== GENERATE ALL DENIAL RULES ==========

For each rule provide:

1. rule_id: "DENY_001", "DENY_002", etc.
2. rule_name: Clear descriptive name
3. severity: "critical", "high", "medium", "low"
4. description: 2-3 sentences

5. required_codes: Extract ALL code types mentioned
   - cpt_codes: [] - 5-digit procedure codes
   - hcpcs_codes: [] - Letter + 4 digits
   - modifiers: [] - 2-character modifiers
   - place_of_service: [] - 2-digit POS codes
   - drg_codes: [] - DRG codes
   - icd10_codes: [] - ICD-10 diagnosis codes
   - addon_codes: [] - Add-on CPT codes
   - revenue_codes: [] - 4-digit revenue codes
   - ndc_codes: [] - National Drug Codes
   - taxonomy_codes: [] - Provider taxonomy

6. required_columns: Database fields needed
   ["claim_id", "cpt_code", "modifier", "date_of_service", "provider_tin", "member_id", ...]

7. attachment_reference: If rule uses attachment
   - attachment_file: "filename.xlsx"
   - validation_type: "code_list_check", "age_range_check", etc.
   - description: "How attachment is used"

8. detection_logic: **EXTRACT FROM POLICY - DO NOT HARDCODE**
   - conditions: [List ALL conditions from policy text]
   - same_date_of_service: true/false
   - same_provider_tin: true/false
   - same_member: true/false
   - time_window: "same day" / "within X days" / "global period"
   - age_requirement: {{"min": X, "max": Y, "unit": "years"}}
   - quantity_limit: {{"max_units": X, "per_period": "day"}}
   - frequency_limit: {{"max_times": X, "per_period": "day"}}
   - code_combination: "description"
   - custom_conditions: [Any other policy-specific conditions]

9. source_text: EXACT verbatim quote from policy (2-3 sentences)

10. simulated_claim_example:
    - claim_lines: [{{"line": 1, "cpt": "99213", "modifier": "25", "pos": "11", "units": 1, "amount": 75.00}}]
    - denial_reason: "Specific reason"
    - paid_lines: [1]
    - denied_lines: [2]

11. detection_query:
    - sql: "Complete SQL query"
    - python: "Complete Python code"

12. codification_steps: ["Step 1", "Step 2", ...]
13. policy_reference: "Section name"
14. qa_reference: "Q&A #1" or null

IMPORTANT: Extract ALL rules. Be comprehensive. Use exact quotes for source_text.

Return JSON:
{{
  "policy_id": "{policy_id}",
  "policy_name": "{policy_name}",
  "generated_at": "{datetime.now().isoformat()}",
  "denial_rules": [...]
}}
'''


def generate_denial_rules(policy_file: Path) -> dict:
    """Generate denial rules for a single policy."""
    
    # Initialize fresh client
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    
    print(f"\n{'='*60}")
    print(f"Processing: {policy_file.name}")
    print(f"{'='*60}")
    
    # Load policy
    policy_text, policy_id, policy_name = load_policy_text(policy_file)
    print(f"  Policy ID: {policy_id}")
    print(f"  Policy Name: {policy_name[:50]}...")
    print(f"  Text Length: {len(policy_text):,} chars")
    
    # Load attachments
    attachments = load_attachment_metadata(policy_id, policy_name)
    print(f"  Attachments: {len(attachments)}")
    
    # Create prompt
    prompt = create_denial_rules_prompt(policy_text, policy_id, policy_name, attachments)
    print(f"  Prompt Length: {len(prompt):,} chars")
    
    # Call LLM
    print(f"  Calling {LLM_MODEL}...")
    try:
        response = client.messages.create(
            model=LLM_MODEL,
            max_tokens=LLM_MAX_TOKENS_GENERATOR,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = response.content[0].text
        print(f"  Response Length: {len(response_text):,} chars")
        
        # Extract JSON
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = json.loads(response_text)
        
        num_rules = len(result.get('denial_rules', []))
        print(f"  ✓ Generated {num_rules} denial rules")
        
        # Save output
        output_file = OUTPUT_DENIAL_DIR / f"{policy_id}_denial_rules.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        print(f"  ✓ Saved: {output_file.name}")
        
        return result
        
    except json.JSONDecodeError as e:
        print(f"  ✗ JSON Parse Error: {e}")
        if SAVE_DEBUG_ON_ERROR:
            debug_file = OUTPUT_DENIAL_DIR / f"{policy_id}_debug.txt"
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(response_text)
            print(f"  Saved debug: {debug_file.name}")
        return {"error": str(e), "policy_id": policy_id}
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return {"error": str(e), "policy_id": policy_id}


def process_all_policies():
    """Process all policy files."""
    policy_files = list(DATA_DIR.glob("*.txt"))
    
    if not policy_files:
        print(f"No policy files found in {DATA_DIR}")
        return []
    
    print(f"Found {len(policy_files)} policy files")
    
    results = []
    for i, policy_file in enumerate(policy_files):
        result = generate_denial_rules(policy_file)
        results.append({
            "file": policy_file.name,
            "policy_id": result.get("policy_id", "unknown"),
            "num_rules": len(result.get("denial_rules", [])),
            "status": "success" if "denial_rules" in result else "error"
        })
        
        if i < len(policy_files) - 1:
            print(f"  Waiting {BATCH_DELAY_SECONDS}s...")
            time.sleep(BATCH_DELAY_SECONDS)
    
    # Summary
    print("\n" + "=" * 60)
    print("AGENT 1 COMPLETE: Denial Rules Generator")
    print("=" * 60)
    total_rules = sum(r.get('num_rules', 0) for r in results)
    successful = sum(1 for r in results if r['status'] == 'success')
    print(f"Policies processed: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Total denial rules: {total_rules}")
    print(f"Output directory: {OUTPUT_DENIAL_DIR}")
    
    return results


def main():
    """Main entry point."""
    print("=" * 60)
    print("AGENT 1: Denial Rules Generator")
    print("=" * 60)
    
    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY not set in .env file")
        sys.exit(1)
    
    if len(sys.argv) > 1:
        # Process single file
        file_path = Path(sys.argv[1])
        if not file_path.exists():
            file_path = DATA_DIR / sys.argv[1]
        
        if file_path.exists():
            generate_denial_rules(file_path)
        else:
            print(f"File not found: {sys.argv[1]}")
            sys.exit(1)
    else:
        process_all_policies()


if __name__ == "__main__":
    main()
