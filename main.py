"""
Agentic Fraud Detection Framework - Main Entry Point
=====================================================
Run this script to execute the fraud detection workflow with human-in-the-loop.

Usage:
    python main.py
"""

import json
import sys
import os
from pathlib import Path

# Fix Windows encoding issues
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    os.environ['PYTHONIOENCODING'] = 'utf-8'

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config import load_config, validate_config
from genie_tool import create_genie_tool
from sql_executor import create_sql_executor
from sql_storage import SQLStorage
from workflow import FraudDetectionWorkflow


# Force UTF-8 for rich console
console = Console(force_terminal=True, legacy_windows=False)


def load_patterns(patterns_file: str = "patterns.json") -> dict:
    """Load patterns from JSON file."""
    patterns_path = Path(__file__).parent / patterns_file
    
    if not patterns_path.exists():
        print(f"[ERROR] Patterns file not found: {patterns_path}")
        sys.exit(1)
    
    with open(patterns_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def display_welcome():
    """Display welcome message."""
    print("\n" + "="*70)
    print("  AGENTIC FRAUD DETECTION FRAMEWORK")
    print("="*70)
    print("\nThis framework uses LangGraph to orchestrate fraud pattern detection")
    print("with Databricks Genie for SQL generation and human-in-the-loop approval.")
    print("="*70)


def display_pattern(pattern: dict):
    """Display pattern information."""
    print("\n" + "-"*50)
    print("PATTERN INFORMATION")
    print("-"*50)
    print(f"  Pattern ID:   {pattern.get('pattern_id', 'N/A')}")
    print(f"  Pattern Name: {pattern.get('pattern_name', 'N/A')}")
    print(f"  Severity:     {pattern.get('severity', 'N/A')}")
    
    desc = pattern.get("description", pattern.get("nlp_description", "N/A"))
    print(f"  Description:  {desc[:80]}...")
    
    detection_logic = pattern.get("detection_logic", {})
    # Handle both dict format (step1, step2, ...) and list format (steps: [...])
    if isinstance(detection_logic, dict):
        if "steps" in detection_logic:
            steps = detection_logic["steps"]
        else:
            # Get values from step1, step2, etc.
            steps = list(detection_logic.values())
    else:
        steps = []
    
    print(f"  Total Steps:  {len(steps)}")
    
    # Display steps
    if steps:
        print("\n  Detection Steps:")
        for i, step in enumerate(steps, 1):
            step_text = step[:70] if len(step) > 70 else step
            print(f"    Step {i}: {step_text}...")
    print("-"*50)


def main():
    """Main entry point."""
    display_welcome()
    
    # Load configuration
    print("\n[*] Loading configuration...")
    config = load_config()
    
    if not validate_config(config):
        print("[ERROR] Configuration validation failed. Please check your .env file.")
        print("[INFO] Copy env.template to .env and fill in your credentials.")
        sys.exit(1)
    
    print("[OK] Configuration loaded")
    
    # Load patterns
    print("\n[*] Loading patterns...")
    patterns_data = load_patterns()
    patterns = patterns_data.get("patterns", [])
    
    if not patterns:
        print("[ERROR] No patterns found in patterns.json")
        sys.exit(1)
    
    print(f"[OK] Loaded {len(patterns)} pattern(s)")
    
    # Display first pattern (we only have one)
    pattern = patterns[0]
    display_pattern(pattern)
    
    # Confirm to proceed
    print("\n" + "="*50)
    print("READY TO START THE AGENTIC WORKFLOW")
    print("="*50)
    print("This will:")
    print("  1. Break down the pattern into steps")
    print("  2. Generate SQL for each step using Genie")
    print("  3. Ask for your approval at each step")
    print("  4. Execute and validate each step")
    print("  5. Combine into a final function")
    print("  6. Insert the tool into the database")
    
    response = input("\nProceed? [yes/no]: ").strip().lower()
    if response not in ['yes', 'y']:
        print("[INFO] Aborted by user.")
        sys.exit(0)
    
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
    
    # Run workflow
    print("\n" + "="*60)
    print("STARTING WORKFLOW EXECUTION...")
    print("="*60 + "\n")
    
    try:
        final_state = workflow.run(pattern)
        
        # Display final result
        print("\n" + "="*60)
        print("WORKFLOW COMPLETE!")
        print("="*60)
        print(f"  Pattern:              {final_state['pattern_name']}")
        print(f"  Tool ID:              {final_state.get('tool_id', 'N/A')}")
        print(f"  Tool Inserted:        {final_state.get('tool_inserted', False)}")
        print(f"  Fraudulent Claims:    {len(final_state.get('final_result', []) or [])}")
        print(f"  SQL Code saved to:    {sql_storage.filepath}")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n[INFO] Workflow interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Workflow error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
