"""
Configuration file for the Policy Extraction Pipeline.

All paths and settings are centralized here.
"""
import os
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# =============================================================================
# BASE DIRECTORIES
# =============================================================================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"                          # Raw policy .txt files
INPUT_DIR = BASE_DIR / "input"                        # Attachment Excel/CSV files
LOGS_DIR = BASE_DIR / "logs"                          # Log files

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
                 OUTPUT_FRAUD_DIR, OUTPUT_FRAUD_VAL_DIR, OUTPUT_NEO4J_DIR, LOGS_DIR]:
    dir_path.mkdir(exist_ok=True)

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================
def setup_logger(agent_name: str) -> logging.Logger:
    """Setup logger for an agent with file and console handlers."""
    logger = logging.getLogger(agent_name)
    logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers
    logger.handlers = []
    
    # File handler - detailed logs
    log_file = LOGS_DIR / f"{agent_name}_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)
    
    # Console handler - info and above
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_format)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# =============================================================================
# CHECKPOINT/RESUME FUNCTIONALITY
# =============================================================================
CHECKPOINT_FILE = BASE_DIR / ".pipeline_checkpoint.json"

def load_checkpoint() -> dict:
    """Load checkpoint data for resume functionality."""
    if CHECKPOINT_FILE.exists():
        try:
            import json
            with open(CHECKPOINT_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_checkpoint(agent_name: str, completed_items: list, failed_items: list = None):
    """Save checkpoint data for an agent."""
    import json
    checkpoint = load_checkpoint()
    checkpoint[agent_name] = {
        "completed": completed_items,
        "failed": failed_items or [],
        "last_updated": datetime.now().isoformat()
    }
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(checkpoint, f, indent=2)

def get_completed_items(agent_name: str) -> list:
    """Get list of completed items for an agent."""
    checkpoint = load_checkpoint()
    return checkpoint.get(agent_name, {}).get("completed", [])

def clear_checkpoint(agent_name: str = None):
    """Clear checkpoint for an agent or all agents."""
    import json
    if agent_name:
        checkpoint = load_checkpoint()
        if agent_name in checkpoint:
            del checkpoint[agent_name]
            with open(CHECKPOINT_FILE, 'w') as f:
                json.dump(checkpoint, f, indent=2)
    else:
        if CHECKPOINT_FILE.exists():
            CHECKPOINT_FILE.unlink()

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
LLM_MAX_TOKENS_GENERATOR = 64000    # For generators (denial, fraud) - no limit
LLM_MAX_TOKENS_VALIDATOR = 64000    # For validators - no limit
LLM_MAX_TOKENS_FINALIZER = 64000    # For finalizer - no limit

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
