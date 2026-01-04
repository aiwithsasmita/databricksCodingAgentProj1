"""
Configuration for Agentic Fraud Detection Framework
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    """Configuration settings."""
    
    # Databricks settings
    databricks_host: str = os.getenv("DATABRICKS_HOST", "")
    databricks_token: str = os.getenv("DATABRICKS_TOKEN", "")
    
    # Genie settings
    genie_space_id: str = os.getenv("GENIE_SPACE_ID", "")
    
    # SQL Warehouse settings
    dbsql_server_hostname: str = os.getenv("DBSQL_SERVER_HOSTNAME", "")
    dbsql_http_path: str = os.getenv("DBSQL_HTTP_PATH", "")
    
    # Anthropic settings (for LangGraph orchestration)
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    anthropic_model: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
    
    # Legacy OpenAI settings (optional fallback)
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    
    # LLM Provider: "anthropic" or "openai"
    llm_provider: str = os.getenv("LLM_PROVIDER", "anthropic")
    
    # Output settings
    output_dir: str = os.getenv("OUTPUT_DIR", "./output")
    sql_code_file: str = os.getenv("SQL_CODE_FILE", "sqlcode.md")
    
    # Database tables
    claims_table: str = "fraud_detection.test_data.claims"
    tools_table: str = "fraud_detection.policies.sql_tools"
    patterns_table: str = "fraud_detection.policies.patterns"
    policies_table: str = "fraud_detection.policies.policies"


def load_config() -> Config:
    """Load configuration from environment variables."""
    return Config()


def validate_config(config: Config) -> bool:
    """Validate required configuration."""
    required = [
        ("DATABRICKS_HOST", config.databricks_host),
        ("DATABRICKS_TOKEN", config.databricks_token),
        ("GENIE_SPACE_ID", config.genie_space_id),
    ]
    
    # Check LLM provider
    if config.llm_provider == "anthropic":
        required.append(("ANTHROPIC_API_KEY", config.anthropic_api_key))
    else:
        required.append(("OPENAI_API_KEY", config.openai_api_key))
    
    missing = [name for name, value in required if not value]
    
    if missing:
        print(f"Missing required configuration: {', '.join(missing)}")
        return False
    
    return True

