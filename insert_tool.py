"""
Insert the generated tool into Databricks
=========================================
Run this to insert the final SQL function into the sql_tools table.
"""

import sys
import os
from pathlib import Path

# Fix Windows encoding issues
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    os.environ['PYTHONIOENCODING'] = 'utf-8'

from config import load_config, validate_config
from sql_executor import create_sql_executor


def main():
    """Insert the tool into Databricks."""
    print("\n" + "="*60)
    print("INSERTING TOOL INTO DATABRICKS")
    print("="*60)

    # Load configuration
    print("\n[*] Loading configuration...")
    config = load_config()

    if not validate_config(config):
        print("[ERROR] Configuration validation failed!")
        sys.exit(1)

    print("[OK] Configuration loaded")

    # Initialize SQL executor
    try:
        sql_executor = create_sql_executor(config)
        print("[OK] SQL executor initialized")
    except Exception as e:
        print(f"[ERROR] Failed to initialize SQL executor: {e}")
        sys.exit(1)

    # Read the final SQL from the generated file
    sql_file = Path("output/sqlcode.md")
    if not sql_file.exists():
        print("[ERROR] SQL file not found: output/sqlcode.md")
        sys.exit(1)

    print("\n[*] Reading generated SQL...")

    with open(sql_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract the final SQL function (it's the last code block)
    import re
    sql_blocks = re.findall(r'```sql\n(.*?)\n```', content, re.DOTALL)

    if not sql_blocks:
        print("[ERROR] No SQL blocks found in the file")
        sys.exit(1)

    final_sql = sql_blocks[-1].strip()  # Last SQL block is the final function

    print(f"[OK] Found final SQL function ({len(final_sql)} characters)")

    # Tool details
    tool_id = "tool_FP-GD-001"
    pattern_id = "FP-GD-001"
    policy_id = "UHC-POL-2026-0005A"

    print("\n[*] Inserting tool...")
    print(f"  Tool ID: {tool_id}")
    print(f"  Pattern ID: {pattern_id}")
    print(f"  Policy ID: {policy_id}")

    # Insert the tool
    success, error = sql_executor.insert_tool(
        tool_id=tool_id,
        pattern_id=pattern_id,
        policy_id=policy_id,
        sql_query=final_sql,
        tools_table=config.tools_table
    )

    if error:
        print(f"\n[ERROR] Failed to insert tool: {error}")
        print("\nTroubleshooting:")
        print("1. Check Databricks permissions")
        print("2. Ensure sql_tools table exists")
        print("3. Verify table schema")
        print(f"\nTable: {config.tools_table}")
        sys.exit(1)

    print("\n[OK] Tool inserted successfully!")

    # Update pattern with tool_id
    print("\n[*] Updating pattern reference...")
    success, error = sql_executor.update_pattern_tool(
        pattern_id=pattern_id,
        tool_id=tool_id,
        patterns_table=config.patterns_table
    )

    if error:
        print(f"[WARNING] Failed to update pattern: {error}")
    else:
        print("[OK] Pattern updated with tool reference")

    print("\n" + "="*60)
    print("TOOL INSERTION COMPLETE!")
    print("="*60)
    print(f"  Tool ID: {tool_id}")
    print(f"  Pattern ID: {pattern_id}")
    print(f"  Status: Inserted and Active")
    print(f"  SQL Length: {len(final_sql)} characters")
    print("="*60)


if __name__ == "__main__":
    main()

