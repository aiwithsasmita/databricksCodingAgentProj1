"""
Auto-Run Script for Agentic Fraud Detection
============================================
Runs the workflow automatically with simulated user approvals.
Use this for testing without manual interaction.

Usage:
    python run_auto.py
"""

import json
import sys
import os
from pathlib import Path
from unittest.mock import patch

# Fix Windows encoding issues
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    os.environ['PYTHONIOENCODING'] = 'utf-8'

from config import load_config, validate_config
from genie_tool import create_genie_tool
from sql_executor import create_sql_executor
from sql_storage import SQLStorage
from workflow import FraudDetectionWorkflow


def load_patterns(patterns_file: str = "patterns.json") -> dict:
    """Load patterns from JSON file."""
    patterns_path = Path(__file__).parent / patterns_file
    
    if not patterns_path.exists():
        print(f"[ERROR] Patterns file not found: {patterns_path}")
        sys.exit(1)
    
    with open(patterns_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def display_pattern(pattern: dict):
    """Display pattern information."""
    print("\n" + "-"*60)
    print("PATTERN INFORMATION")
    print("-"*60)
    print(f"  Pattern ID:   {pattern.get('pattern_id', 'N/A')}")
    print(f"  Pattern Name: {pattern.get('pattern_name', 'N/A')}")
    print(f"  Severity:     {pattern.get('severity', 'N/A')}")
    
    detection_logic = pattern.get("detection_logic", {})
    if isinstance(detection_logic, dict):
        if "steps" in detection_logic:
            steps = detection_logic["steps"]
        else:
            steps = list(detection_logic.values())
    else:
        steps = []
    
    print(f"  Total Steps:  {len(steps)}")
    
    if steps:
        print("\n  Detection Steps:")
        for i, step in enumerate(steps, 1):
            step_text = step[:60] if len(step) > 60 else step
            print(f"    {i}. {step_text}...")
    print("-"*60)


def auto_input_generator():
    """Generate automatic responses for input prompts."""
    responses = ['yes']  # Always approve
    idx = 0
    while True:
        yield 'yes'


auto_inputs = auto_input_generator()


def mock_input(prompt):
    """Mock input that auto-approves."""
    print(f"{prompt}yes (auto)")
    return "yes"


def main():
    """Main entry point with auto-approval."""
    print("\n" + "="*70)
    print("  AGENTIC FRAUD DETECTION - AUTO RUN MODE")
    print("="*70)
    print("\n[INFO] Running in auto-approval mode for testing")
    print("="*70)
    
    # Load configuration
    print("\n[*] Loading configuration...")
    config = load_config()
    
    if not validate_config(config):
        print("[ERROR] Configuration validation failed!")
        print("[INFO] Make sure your .env file has:")
        print("  - DATABRICKS_HOST")
        print("  - DATABRICKS_TOKEN")
        print("  - GENIE_SPACE_ID")
        print("  - DBSQL_SERVER_HOSTNAME")
        print("  - DBSQL_HTTP_PATH")
        print("  - OPENAI_API_KEY")
        sys.exit(1)
    
    print("[OK] Configuration loaded")
    print(f"  - Databricks Host: {config.databricks_host[:30]}...")
    print(f"  - Genie Space ID: {config.genie_space_id}")
    
    # Load patterns
    print("\n[*] Loading patterns...")
    patterns_data = load_patterns()
    patterns = patterns_data.get("patterns", [])
    
    if not patterns:
        print("[ERROR] No patterns found in patterns.json")
        sys.exit(1)
    
    print(f"[OK] Loaded {len(patterns)} pattern(s)")
    
    # Display first pattern
    pattern = patterns[0]
    display_pattern(pattern)
    
    # Initialize components
    print("\n[*] Initializing components...")
    
    try:
        genie = create_genie_tool(config)
        print("[OK] Genie tool initialized")
    except Exception as e:
        print(f"[ERROR] Failed to initialize Genie: {e}")
        sys.exit(1)
    
    try:
        sql_executor = create_sql_executor(config)
        print("[OK] SQL executor initialized")
    except Exception as e:
        print(f"[ERROR] Failed to initialize SQL executor: {e}")
        sys.exit(1)
    
    sql_storage = SQLStorage(output_dir=config.output_dir, filename=config.sql_code_file)
    print("[OK] SQL storage initialized")
    
    # Create workflow
    print("\n[*] Creating workflow...")
    workflow = FraudDetectionWorkflow(
        config=config,
        genie=genie,
        sql_executor=sql_executor,
        sql_storage=sql_storage
    )
    print("[OK] Workflow created")
    
    # Run workflow with mocked input
    print("\n" + "="*60)
    print("STARTING WORKFLOW (AUTO-APPROVAL MODE)")
    print("="*60 + "\n")
    
    try:
        # Patch input to auto-approve
        with patch('builtins.input', mock_input):
            final_state = workflow.run(pattern)
        
        # Display final result
        print("\n" + "="*60)
        print("WORKFLOW COMPLETE!")
        print("="*60)
        print(f"  Pattern:              {final_state['pattern_name']}")
        print(f"  Pattern ID:           {final_state['pattern_id']}")
        print(f"  Tool ID:              {final_state.get('tool_id', 'N/A')}")
        print(f"  Tool Inserted:        {final_state.get('tool_inserted', False)}")
        print(f"  Steps Completed:      {final_state.get('total_steps', 0)}")
        print(f"  SQL Queries Stored:   {len(final_state.get('step_sql_queries', []))}")
        print(f"  Fraudulent Claims:    {len(final_state.get('final_result', []) or [])}")
        print(f"  SQL Code saved to:    {sql_storage.filepath}")
        print("="*60)
        
        # Show sample results
        if final_state.get('final_result'):
            print("\nSample Fraudulent Claims Found:")
            for i, row in enumerate(final_state['final_result'][:5], 1):
                print(f"  {i}. {row}")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n[INFO] Workflow interrupted by user.")
        return 1
    except Exception as e:
        print(f"\n[ERROR] Workflow error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

