"""
Agent 0: Attachment Metadata Generator

Generates LLM-based metadata for attachment files (Excel/CSV).

Usage:
    python agent0_attachment_metadata.py                    # Process all attachments
    python agent0_attachment_metadata.py <attachment_file>  # Process single file
    python agent0_attachment_metadata.py --reset            # Clear checkpoint and reprocess all

Input:  Attachment files in input/ directory
Output: JSON metadata files in output_metadata/ directory
"""

import sys
import json
import time
import re
import pandas as pd
from pathlib import Path
from datetime import datetime
from anthropic import Anthropic

from config import (
    INPUT_DIR, OUTPUT_METADATA_DIR, ANTHROPIC_API_KEY,
    LLM_MODEL, BATCH_DELAY_SECONDS, SAVE_DEBUG_ON_ERROR,
    setup_logger, save_checkpoint, get_completed_items, clear_checkpoint
)

# Setup logger
logger = setup_logger("agent0")

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY = 5


def read_attachment_preview(file_path: Path, num_rows: int = 5) -> tuple:
    """Read first N rows of an attachment file."""
    try:
        if file_path.suffix.lower() in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path, nrows=num_rows)
        elif file_path.suffix.lower() == '.csv':
            df = pd.read_csv(file_path, nrows=num_rows)
        else:
            return None, None, f"Unsupported file type: {file_path.suffix}"
        
        columns = list(df.columns)
        preview = df.to_dict('records')
        return columns, preview, None
        
    except Exception as e:
        return None, None, str(e)


def create_metadata_prompt(filename: str, columns: list, preview: list) -> str:
    """Create prompt for metadata generation."""
    preview_str = json.dumps(preview, indent=2, default=str)
    
    return f'''You are a healthcare policy expert. Analyze this attachment file and generate metadata.

FILENAME: {filename}

COLUMNS: {columns}

SAMPLE DATA (first 5 rows):
{preview_str}

Generate metadata JSON with these fields:
{{
    "attachment_name": "Human-readable name for this attachment",
    "objective": "What is the purpose of this attachment in claim adjudication?",
    "description": "Detailed description of what this file contains",
    "code_types": ["CPT", "HCPCS", "Modifier", etc.] - what types of codes are in this file,
    "sample_codes": ["99213", "G0088", ...] - first 10 codes from the file,
    "key_fields": [
        {{"field": "column_name", "description": "what this column contains"}}
    ],
    "data_patterns": "Describe any patterns in the data (code ranges, categories, etc.)",
    "usage_in_policy": "How would this attachment be used during claim adjudication?",
    "total_rows_estimate": "Estimate based on sample",
    "validation_type": "code_list_check" | "age_range_check" | "modifier_allowed" | "bundled_codes" | "other"
}}

Return ONLY the JSON object, no other text.
'''


def generate_metadata(file_path: Path) -> dict:
    """Generate metadata for a single attachment file with retry logic."""
    logger.info(f"Processing: {file_path.name}")
    
    # Read preview
    columns, preview, error = read_attachment_preview(file_path)
    if error:
        logger.error(f"Error reading file {file_path.name}: {error}")
        return {"error": error, "filename": file_path.name}
    
    logger.debug(f"Columns: {columns}")
    logger.debug(f"Preview rows: {len(preview)}")
    
    # Create prompt
    prompt = create_metadata_prompt(file_path.name, columns, preview)
    
    # Call LLM with retry
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"Calling {LLM_MODEL} (attempt {attempt}/{MAX_RETRIES})...")
            
            response = client.messages.create(
                model=LLM_MODEL,
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response.content[0].text
            logger.debug(f"Response length: {len(response_text)} chars")
            
            # Parse JSON
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                llm_analysis = json.loads(json_match.group())
            else:
                llm_analysis = json.loads(response_text)
            
            # Build full metadata
            metadata = {
                "attachment_filename": file_path.name,
                "attachment_path": str(file_path.relative_to(file_path.parent.parent)),
                "columns": columns,
                "sample_data": preview,
                "llm_analysis": llm_analysis,
                "created_date": datetime.now().isoformat(),
                "generated_at": datetime.now().isoformat()
            }
            
            # Save output
            output_file = OUTPUT_METADATA_DIR / f"{file_path.stem}_metadata.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, default=str)
            
            logger.info(f"✓ Saved: {output_file.name}")
            return metadata
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON Parse Error (attempt {attempt}): {e}")
            if attempt == MAX_RETRIES:
                if SAVE_DEBUG_ON_ERROR:
                    debug_file = OUTPUT_METADATA_DIR / f"{file_path.stem}_debug.txt"
                    with open(debug_file, 'w', encoding='utf-8') as f:
                        f.write(response_text)
                    logger.debug(f"Saved debug to: {debug_file.name}")
                return {"error": str(e), "filename": file_path.name}
            time.sleep(RETRY_DELAY)
            
        except Exception as e:
            logger.error(f"Error (attempt {attempt}): {e}")
            if attempt == MAX_RETRIES:
                return {"error": str(e), "filename": file_path.name}
            logger.info(f"Retrying in {RETRY_DELAY}s...")
            time.sleep(RETRY_DELAY)
    
    return {"error": "Max retries exceeded", "filename": file_path.name}


def process_all_attachments(reset: bool = False):
    """Process all attachment files in input directory with checkpoint/resume."""
    
    # Handle reset
    if reset:
        logger.info("Clearing checkpoint - will reprocess all files")
        clear_checkpoint("agent0")
    
    # Get completed items
    completed = get_completed_items("agent0")
    if completed:
        logger.info(f"Resuming from checkpoint - {len(completed)} files already processed")
    
    # Find all attachment files
    extensions = ['*.xlsx', '*.xls', '*.csv']
    files = []
    for ext in extensions:
        files.extend(INPUT_DIR.glob(ext))
    
    if not files:
        logger.warning(f"No attachment files found in {INPUT_DIR}")
        return []
    
    # Filter out already completed files
    pending_files = [f for f in files if f.name not in completed]
    
    logger.info("=" * 60)
    logger.info("AGENT 0: Attachment Metadata Generator")
    logger.info("=" * 60)
    logger.info(f"Total files: {len(files)}")
    logger.info(f"Already completed: {len(completed)}")
    logger.info(f"Pending: {len(pending_files)}")
    logger.info("=" * 60)
    
    if not pending_files:
        logger.info("All files already processed. Use --reset to reprocess.")
        return []
    
    results = []
    failed = []
    
    for i, file_path in enumerate(pending_files):
        logger.info(f"\n[{i+1}/{len(pending_files)}] Processing: {file_path.name}")
        
        result = generate_metadata(file_path)
        
        if "llm_analysis" in result:
            completed.append(file_path.name)
            results.append({
                "file": file_path.name,
                "status": "success"
            })
            # Save checkpoint after each success
            save_checkpoint("agent0", completed, failed)
        else:
            failed.append(file_path.name)
            results.append({
                "file": file_path.name,
                "status": "error",
                "error": result.get("error", "Unknown error")
            })
            logger.error(f"✗ Failed: {file_path.name}")
            # Save checkpoint with failed items
            save_checkpoint("agent0", completed, failed)
        
        # Delay between calls
        if i < len(pending_files) - 1:
            logger.debug(f"Waiting {BATCH_DELAY_SECONDS}s before next file...")
            time.sleep(BATCH_DELAY_SECONDS)
    
    # Final summary
    logger.info("\n" + "=" * 60)
    logger.info("AGENT 0 COMPLETE: Attachment Metadata Generator")
    logger.info("=" * 60)
    successful = sum(1 for r in results if r['status'] == 'success')
    logger.info(f"Processed this run: {len(results)}")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {len(failed)}")
    logger.info(f"Total completed: {len(completed)}")
    logger.info(f"Output directory: {OUTPUT_METADATA_DIR}")
    
    if failed:
        logger.warning(f"Failed files: {failed}")
        logger.info("Run again to retry failed files, or use --reset to start fresh")
    
    return results


def main():
    """Main entry point."""
    if not ANTHROPIC_API_KEY:
        logger.error("ANTHROPIC_API_KEY not set in .env file")
        sys.exit(1)
    
    # Check for reset flag
    reset = "--reset" in sys.argv
    
    if len(sys.argv) > 1 and sys.argv[1] != "--reset":
        # Process single file
        file_path = Path(sys.argv[1])
        if not file_path.exists():
            file_path = INPUT_DIR / sys.argv[1]
        
        if file_path.exists():
            generate_metadata(file_path)
        else:
            logger.error(f"File not found: {sys.argv[1]}")
            sys.exit(1)
    else:
        # Process all files
        process_all_attachments(reset=reset)


if __name__ == "__main__":
    main()
