"""
Agent 0: Attachment Metadata Generator

Generates LLM-based metadata for attachment files (Excel/CSV).

Usage:
    python agent0_attachment_metadata.py                    # Process all attachments
    python agent0_attachment_metadata.py <attachment_file>  # Process single file

Input:  Attachment files in input/ directory
Output: JSON metadata files in output_metadata/ directory
"""

import sys
import json
import time
import pandas as pd
from pathlib import Path
from datetime import datetime
from anthropic import Anthropic

from config import (
    INPUT_DIR, OUTPUT_METADATA_DIR, ANTHROPIC_API_KEY,
    LLM_MODEL, BATCH_DELAY_SECONDS, SAVE_DEBUG_ON_ERROR
)


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
    """Generate metadata for a single attachment file."""
    print(f"\nProcessing: {file_path.name}")
    
    # Read preview
    columns, preview, error = read_attachment_preview(file_path)
    if error:
        print(f"  ✗ Error reading file: {error}")
        return {"error": error, "filename": file_path.name}
    
    print(f"  Columns: {columns}")
    print(f"  Preview rows: {len(preview)}")
    
    # Create prompt
    prompt = create_metadata_prompt(file_path.name, columns, preview)
    
    # Call LLM
    print(f"  Calling {LLM_MODEL}...")
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    
    try:
        response = client.messages.create(
            model=LLM_MODEL,
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = response.content[0].text
        
        # Parse JSON
        import re
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
        
        print(f"  ✓ Saved: {output_file.name}")
        return metadata
        
    except json.JSONDecodeError as e:
        print(f"  ✗ JSON Parse Error: {e}")
        if SAVE_DEBUG_ON_ERROR:
            debug_file = OUTPUT_METADATA_DIR / f"{file_path.stem}_debug.txt"
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(response_text)
            print(f"  Saved debug to: {debug_file.name}")
        return {"error": str(e), "filename": file_path.name}
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return {"error": str(e), "filename": file_path.name}


def process_all_attachments():
    """Process all attachment files in input directory."""
    # Find all attachment files
    extensions = ['*.xlsx', '*.xls', '*.csv']
    files = []
    for ext in extensions:
        files.extend(INPUT_DIR.glob(ext))
    
    if not files:
        print(f"No attachment files found in {INPUT_DIR}")
        return []
    
    print(f"Found {len(files)} attachment files")
    print("=" * 60)
    
    results = []
    for i, file_path in enumerate(files):
        result = generate_metadata(file_path)
        results.append({
            "file": file_path.name,
            "status": "success" if "llm_analysis" in result else "error"
        })
        
        # Delay between calls
        if i < len(files) - 1:
            time.sleep(BATCH_DELAY_SECONDS)
    
    # Summary
    print("\n" + "=" * 60)
    print("AGENT 0 COMPLETE: Attachment Metadata Generator")
    print("=" * 60)
    successful = sum(1 for r in results if r['status'] == 'success')
    print(f"Processed: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Output directory: {OUTPUT_METADATA_DIR}")
    
    return results


def main():
    """Main entry point."""
    print("=" * 60)
    print("AGENT 0: Attachment Metadata Generator")
    print("=" * 60)
    
    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY not set in .env file")
        sys.exit(1)
    
    if len(sys.argv) > 1:
        # Process single file
        file_path = Path(sys.argv[1])
        if not file_path.exists():
            file_path = INPUT_DIR / sys.argv[1]
        
        if file_path.exists():
            generate_metadata(file_path)
        else:
            print(f"File not found: {sys.argv[1]}")
            sys.exit(1)
    else:
        # Process all files
        process_all_attachments()


if __name__ == "__main__":
    main()
