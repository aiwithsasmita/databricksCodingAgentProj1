"""
Agent 1: Denial Rules Generator

Generates denial rules from healthcare policy documents.

Usage:
    python agent1_denial_generator.py                    # Process all policies
    python agent1_denial_generator.py <policy_file>      # Process single file
    python agent1_denial_generator.py --reset            # Clear checkpoint and reprocess all

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
    LLM_MODEL, LLM_MAX_TOKENS_GENERATOR, BATCH_DELAY_SECONDS, SAVE_DEBUG_ON_ERROR,
    setup_logger, save_checkpoint, get_completed_items, clear_checkpoint
)

# Setup logger
logger = setup_logger("agent1")

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY = 5


def extract_policy_id(text: str, filename: str) -> str:
    """Extract policy ID from text or filename."""
    patterns = [
        r'Policy\s*Number\s+(\d{4}R\d{4}[A-Z]?)',  # "Policy Number 2026R0005A"
        r'(\d{4}R\d{4}[A-Z]?)',  # Just the pattern anywhere
        r'Policy\s*(?:Number|#|No\.?)?[:\s]+([A-Z0-9]{8,})',  # Generic policy number
    ]
    for pattern in patterns:
        match = re.search(pattern, text[:3000], re.IGNORECASE)
        if match:
            return match.group(1)
    # Fallback to filename-based ID
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


def load_attachment_metadata(policy_id: str, policy_name: str, policy_filename: str = "") -> list:
    """Load attachment metadata for a policy."""
    attachments = []
    if not OUTPUT_METADATA_DIR.exists():
        return attachments
    
    # Create search patterns from policy name and filename
    name_parts = policy_name.lower().replace('_', ' ').replace('-', ' ').replace(',', ' ').split()
    key_words = [w for w in name_parts if len(w) > 3 and w not in ['policy', 'commercial', 'reimbursement', 'professional']]
    
    # Also extract keywords from policy filename (e.g., "UHC_Global_Days_Policy_Raw.txt" -> ["global", "days"])
    if policy_filename:
        filename_parts = policy_filename.lower().replace('_', ' ').replace('-', ' ').split()
        filename_keywords = [w for w in filename_parts if len(w) > 3 and w not in ['uhc', 'policy', 'raw', 'txt']]
        key_words.extend(filename_keywords)
    
    # Remove duplicates
    key_words = list(set(key_words))
    logger.debug(f"Attachment search keywords: {key_words}")
    
    for meta_file in OUTPUT_METADATA_DIR.glob("*_metadata.json"):
        try:
            with open(meta_file, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            filename_lower = meta_file.name.lower()
            
            # Match by policy ID
            if policy_id.lower() in filename_lower:
                attachments.append(meta)
                logger.debug(f"Matched attachment by policy_id: {meta_file.name}")
            # Match by keywords (at least 2 keywords must match)
            elif sum(1 for kw in key_words if kw in filename_lower) >= 1:
                attachments.append(meta)
                logger.debug(f"Matched attachment by keywords: {meta_file.name}")
        except Exception as e:
            logger.warning(f"Could not load {meta_file.name}: {e}")
    
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
    """Generate denial rules for a single policy with retry logic."""
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Processing: {policy_file.name}")
    logger.info(f"{'='*60}")
    
    # Load policy
    policy_text, policy_id, policy_name = load_policy_text(policy_file)
    logger.info(f"Policy ID: {policy_id}")
    logger.info(f"Policy Name: {policy_name[:50]}...")
    logger.debug(f"Text Length: {len(policy_text):,} chars")
    
    # Load attachments (pass filename for better matching)
    attachments = load_attachment_metadata(policy_id, policy_name, policy_file.name)
    logger.info(f"Attachments: {len(attachments)}")
    
    # Create prompt
    prompt = create_denial_rules_prompt(policy_text, policy_id, policy_name, attachments)
    logger.debug(f"Prompt Length: {len(prompt):,} chars")
    
    # Initialize client
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    
    # Call LLM with retry (using streaming for long requests)
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"Calling {LLM_MODEL} (attempt {attempt}/{MAX_RETRIES})...")
            
            # Use streaming to handle long requests
            response_text = ""
            with client.messages.stream(
                model=LLM_MODEL,
                max_tokens=LLM_MAX_TOKENS_GENERATOR,
                messages=[{"role": "user", "content": prompt}]
            ) as stream:
                for text in stream.text_stream:
                    response_text += text
            
            logger.debug(f"Response Length: {len(response_text):,} chars")
            
            # Extract JSON
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(response_text)
            
            num_rules = len(result.get('denial_rules', []))
            logger.info(f"✓ Generated {num_rules} denial rules")
            
            # Save output
            output_file = OUTPUT_DENIAL_DIR / f"{policy_id}_denial_rules.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2)
            logger.info(f"✓ Saved: {output_file.name}")
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON Parse Error (attempt {attempt}): {e}")
            if attempt == MAX_RETRIES:
                if SAVE_DEBUG_ON_ERROR:
                    debug_file = OUTPUT_DENIAL_DIR / f"{policy_id}_debug.txt"
                    with open(debug_file, 'w', encoding='utf-8') as f:
                        f.write(response_text)
                    logger.debug(f"Saved debug: {debug_file.name}")
                return {"error": str(e), "policy_id": policy_id}
            time.sleep(RETRY_DELAY)
            
        except Exception as e:
            logger.error(f"Error (attempt {attempt}): {e}")
            if attempt == MAX_RETRIES:
                return {"error": str(e), "policy_id": policy_id}
            logger.info(f"Retrying in {RETRY_DELAY}s...")
            time.sleep(RETRY_DELAY)
    
    return {"error": "Max retries exceeded", "policy_id": policy_id}


def process_all_policies(reset: bool = False):
    """Process all policy files with checkpoint/resume."""
    
    # Handle reset
    if reset:
        logger.info("Clearing checkpoint - will reprocess all files")
        clear_checkpoint("agent1")
    
    # Get completed items
    completed = get_completed_items("agent1")
    if completed:
        logger.info(f"Resuming from checkpoint - {len(completed)} files already processed")
    
    policy_files = list(DATA_DIR.glob("*.txt"))
    
    if not policy_files:
        logger.warning(f"No policy files found in {DATA_DIR}")
        return []
    
    # Filter out completed files
    pending_files = [f for f in policy_files if f.name not in completed]
    
    logger.info("=" * 60)
    logger.info("AGENT 1: Denial Rules Generator")
    logger.info("=" * 60)
    logger.info(f"Total files: {len(policy_files)}")
    logger.info(f"Already completed: {len(completed)}")
    logger.info(f"Pending: {len(pending_files)}")
    logger.info("=" * 60)
    
    if not pending_files:
        logger.info("All files already processed. Use --reset to reprocess.")
        return []
    
    results = []
    failed = []
    
    for i, policy_file in enumerate(pending_files):
        logger.info(f"\n[{i+1}/{len(pending_files)}] Processing: {policy_file.name}")
        
        result = generate_denial_rules(policy_file)
        
        if "denial_rules" in result:
            completed.append(policy_file.name)
            results.append({
                "file": policy_file.name,
                "policy_id": result.get("policy_id", "unknown"),
                "num_rules": len(result.get("denial_rules", [])),
                "status": "success"
            })
            save_checkpoint("agent1", completed, failed)
        else:
            failed.append(policy_file.name)
            results.append({
                "file": policy_file.name,
                "status": "error",
                "error": result.get("error", "Unknown error")
            })
            logger.error(f"✗ Failed: {policy_file.name}")
            save_checkpoint("agent1", completed, failed)
        
        if i < len(pending_files) - 1:
            logger.debug(f"Waiting {BATCH_DELAY_SECONDS}s...")
            time.sleep(BATCH_DELAY_SECONDS)
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("AGENT 1 COMPLETE: Denial Rules Generator")
    logger.info("=" * 60)
    total_rules = sum(r.get('num_rules', 0) for r in results if r['status'] == 'success')
    successful = sum(1 for r in results if r['status'] == 'success')
    logger.info(f"Processed this run: {len(results)}")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {len(failed)}")
    logger.info(f"Total denial rules: {total_rules}")
    logger.info(f"Output directory: {OUTPUT_DENIAL_DIR}")
    
    if failed:
        logger.warning(f"Failed files: {failed}")
        logger.info("Run again to retry failed files, or use --reset to start fresh")
    
    return results


def main():
    """Main entry point."""
    if not ANTHROPIC_API_KEY:
        logger.error("ANTHROPIC_API_KEY not set in .env file")
        sys.exit(1)
    
    reset = "--reset" in sys.argv
    
    if len(sys.argv) > 1 and sys.argv[1] != "--reset":
        # Process single file
        file_path = Path(sys.argv[1])
        if not file_path.exists():
            file_path = DATA_DIR / sys.argv[1]
        
        if file_path.exists():
            generate_denial_rules(file_path)
        else:
            logger.error(f"File not found: {sys.argv[1]}")
            sys.exit(1)
    else:
        process_all_policies(reset=reset)


if __name__ == "__main__":
    main()
