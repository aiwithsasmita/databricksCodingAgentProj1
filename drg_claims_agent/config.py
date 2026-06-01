"""
Configuration for the DRG Claims Agent.
Reads from environment variables; falls back to dummy defaults for local demo only.
"""

import os
from dotenv import load_dotenv

load_dotenv()

DATABRICKS_HOST = os.getenv(
    "DATABRICKS_HOST", "https://your-workspace.cloud.databricks.com"
)
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN", "dapi_dummy_token_replace_me")

GENIE_SPACE_ID = os.getenv("GENIE_SPACE_ID", "01f0abcd1234567890abcdef")

LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "databricks-meta-llama-3-3-70b-instruct")

# Set to 1 / true in production so missing or placeholder Databricks creds fail fast
DRG_AGENT_STRICT = os.getenv("DRG_AGENT_STRICT", "0").lower() in (
    "1",
    "true",
    "yes",
)


def _is_placeholder_databricks_config() -> bool:
    host = (DATABRICKS_HOST or "").lower()
    tok = (DATABRICKS_TOKEN or "").strip()
    space = (GENIE_SPACE_ID or "").lower()
    if "your-workspace" in host:
        return True
    if "01f0abcd" in space:
        return True
    tl = tok.lower()
    if (
        not tok
        or tl == "dapi_dummy_token_replace_me"
        or "dummy" in tl
        or "replace_me" in tl
    ):
        return True
    if not tok.startswith("dapi"):
        return True
    return False


def validate_production_settings() -> None:
    """Raise ValueError if Databricks settings are missing or look like template values.

    Enable by setting environment variable ``DRG_AGENT_STRICT=1`` before
    creating the agent (recommended for any deployed environment).
    """
    if not DATABRICKS_HOST.startswith("https://"):
        raise ValueError("DATABRICKS_HOST must be an https:// workspace URL")
    if _is_placeholder_databricks_config():
        raise ValueError(
            "Databricks configuration looks unset or still uses .env.example placeholders. "
            "Set DATABRICKS_HOST, DATABRICKS_TOKEN, GENIE_SPACE_ID, and LLM_ENDPOINT "
            "to real values, or do not set DRG_AGENT_STRICT=1 for local mock runs."
        )


def verify_bundled_reference_data() -> None:
    """Fail fast if shipped CMS JSON files are missing or clearly wrong (deployment check)."""
    import json

    base = os.path.join(os.path.dirname(__file__), "tools")
    must = {
        "drg_reference_data.json": lambda d: len(d) == 770,
        "mce_reference.json": lambda d: d.get("mce_version") == "43.1",
        "v43_1_new_pcs_codes.json": lambda d: d.get("count") == 80,
        "icd_to_drg.json": lambda d: len(d) > 50_000,
        "cc_mcc_list.json": lambda d: len(d) > 15_000,
    }
    for fname, check in must.items():
        path = os.path.join(base, fname)
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Missing reference data file: {path}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not check(data):
            raise ValueError(f"Reference data failed sanity check: {fname}")


if __name__ == "__main__":
    verify_bundled_reference_data()
    print("Bundled reference data: OK")
