"""
Configuration file for the Policy Extraction Pipeline.

All paths and settings are centralized here.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# =============================================================================
# BASE DIRECTORIES
# =============================================================================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"                          # Raw policy .txt files
INPUT_DIR = BASE_DIR / "input"                        # Attachment Excel/CSV files

# =============================================================================
# OUTPUT DIRECTORIES (Created automatically)
# =============================================================================
OUTPUT_METADATA_DIR = BASE_DIR / "output_metadata"    # Agent 0: Attachment metadata
OUTPUT_DENIAL_DIR = BASE_DIR / "denial_rules_output"  # Agent 1: Raw denial rules
OUTPUT_DENIAL_VAL_DIR = BASE_DIR / "denial_validated" # Agent 2: Validated denial rules
OUTPUT_FRAUD_DIR = BASE_DIR / "fraud_tactics_output"  # Agent 3: Raw fraud tactics
OUTPUT_FRAUD_VAL_DIR = BASE_DIR / "fraud_validated"   # Agent 4: Validated fraud tactics
OUTPUT_NEO4J_DIR = BASE_DIR / "neo4j_ready"           # Agent 5: Final Neo4j-ready JSON

# Create all output directories
for dir_path in [OUTPUT_METADATA_DIR, OUTPUT_DENIAL_DIR, OUTPUT_DENIAL_VAL_DIR,
                 OUTPUT_FRAUD_DIR, OUTPUT_FRAUD_VAL_DIR, OUTPUT_NEO4J_DIR]:
    dir_path.mkdir(exist_ok=True)

# =============================================================================
# API KEYS
# =============================================================================
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# =============================================================================
# NEO4J CONNECTION
# =============================================================================
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

# Legacy alias
NEO4J_USER = NEO4J_USERNAME

# =============================================================================
# LLM SETTINGS
# =============================================================================
LLM_MODEL = "claude-sonnet-4-20250514"
LLM_MAX_TOKENS_GENERATOR = 16000    # For generators (denial, fraud)
LLM_MAX_TOKENS_VALIDATOR = 20000    # For validators (more output needed)
LLM_MAX_TOKENS_FINALIZER = 25000    # For finalizer (largest output)

# =============================================================================
# PIPELINE SETTINGS
# =============================================================================
BATCH_DELAY_SECONDS = 2             # Delay between API calls to avoid rate limits
SAVE_DEBUG_ON_ERROR = True          # Save raw LLM response on JSON parse error

# =============================================================================
# VALIDATION
# =============================================================================
def validate_config():
    """Validate that required configuration is present."""
    errors = []
    
    if not ANTHROPIC_API_KEY:
        errors.append("ANTHROPIC_API_KEY is not set in .env file")
    
    if not DATA_DIR.exists():
        errors.append(f"DATA_DIR does not exist: {DATA_DIR}")
    
    if not INPUT_DIR.exists():
        errors.append(f"INPUT_DIR does not exist: {INPUT_DIR}")
    
    if errors:
        print("Configuration Errors:")
        for e in errors:
            print(f"  - {e}")
        return False
    
    return True

def print_config():
    """Print current configuration."""
    print("=" * 60)
    print("PIPELINE CONFIGURATION")
    print("=" * 60)
    print(f"BASE_DIR: {BASE_DIR}")
    print(f"DATA_DIR: {DATA_DIR} (exists: {DATA_DIR.exists()})")
    print(f"INPUT_DIR: {INPUT_DIR} (exists: {INPUT_DIR.exists()})")
    print(f"")
    print("Output Directories:")
    print(f"  Metadata: {OUTPUT_METADATA_DIR}")
    print(f"  Denial Rules: {OUTPUT_DENIAL_DIR}")
    print(f"  Denial Validated: {OUTPUT_DENIAL_VAL_DIR}")
    print(f"  Fraud Tactics: {OUTPUT_FRAUD_DIR}")
    print(f"  Fraud Validated: {OUTPUT_FRAUD_VAL_DIR}")
    print(f"  Neo4j Ready: {OUTPUT_NEO4J_DIR}")
    print(f"")
    print(f"ANTHROPIC_API_KEY: {'✓ Set' if ANTHROPIC_API_KEY else '✗ Missing'}")
    print(f"NEO4J_URI: {NEO4J_URI}")
    print(f"NEO4J_DATABASE: {NEO4J_DATABASE}")
    print(f"LLM_MODEL: {LLM_MODEL}")
    print("=" * 60)


if __name__ == "__main__":
    print_config()
    validate_config()
