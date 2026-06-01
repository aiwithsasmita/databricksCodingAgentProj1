"""Standalone Genie connectivity check — run this on a machine that can reach
your Databricks workspace (VPN/PrivateLink as needed) to confirm credentials,
the space ID, and result extraction before wiring it into the agent.

Usage (from the backend/ dir, with .venv active and .env filled in):

    python scripts/genie_smoke.py <SPACE_ID> "How many DRG 871 cases by year?"

It reads DATABRICKS_HOST/DATABRICKS_TOKEN from your environment / .env.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make `app` importable when run directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from app.genie.client import get_genie_client  # noqa: E402


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    space_id = sys.argv[1]
    question = " ".join(sys.argv[2:])

    client = get_genie_client()
    if not client.available():
        print(
            "ERROR: DATABRICKS_HOST / DATABRICKS_TOKEN not set. Fill them in .env "
            "or the environment first."
        )
        return 1

    print(f"Asking Genie space {space_id!r}:\n  {question}\n")
    result = client.ask(space_id, question, space_name="smoke")

    print(f"status        : {result.status}")
    print(f"conversation  : {result.conversation_id}")
    print(f"message_id    : {result.message_id}")
    if result.error:
        print(f"ERROR         : {result.error}")
        return 1
    if result.description:
        print(f"description   : {result.description}")
    if result.sql:
        print("\n--- generated SQL ---")
        print(result.sql)
    if result.text:
        print("\n--- text answer ---")
        print(result.text)
    if result.columns:
        print(f"\n--- rows ({result.row_count}{'+' if result.truncated else ''}) ---")
        print(" | ".join(result.columns))
        for row in result.rows[:20]:
            print(" | ".join(str(c) for c in row))
    if result.note:
        print(f"\nnote          : {result.note}")
    print("\nOK: Genie round-trip succeeded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
