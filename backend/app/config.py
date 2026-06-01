"""Application settings for the DRG Deep-Agent backend.

All values can be overridden via environment variables or a local ``.env`` file.
See ``.env.example`` for the template.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Absolute path to backend/.env so settings load regardless of the process CWD.
_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    """Runtime configuration, loaded from the environment / ``.env``."""

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- LLM -----------------------------------------------------------------
    # NOTE: the placeholder key is intentionally fake. Replace it in `.env`
    # (or the environment) with a real OpenAI key to get live answers.
    OPENAI_API_KEY: str = "sk-REPLACE_ME"
    # The project standard is GPT-5.5. Change this if your account exposes a
    # different model id (e.g. "gpt-5.5-preview").
    MODEL: str = "gpt-5.5"
    # Optional: point at an OpenAI-compatible gateway. Empty => default OpenAI.
    OPENAI_BASE_URL: str = ""

    # --- Server --------------------------------------------------------------
    FRONTEND_ORIGIN: str = "http://localhost:3000"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # --- Databricks Genie (Stage 2) -----------------------------------------
    # PAT auth: the databricks-sdk auto-detects these env vars. For Azure the
    # host looks like https://adb-XXXXXXXX.azuredatabricks.net
    DATABRICKS_HOST: str = ""
    DATABRICKS_TOKEN: str = ""

    # Registry of Genie spaces, as a JSON array string. Each entry:
    #   {"name": "drg_shift", "space_id": "01ef...", "agent": "drg",
    #    "description": "what this space can answer"}
    # `name` -> tool name `genie_<name>`; `agent` routes it to a subagent
    # (default "drg"). Leave blank to fall back to Stage-1 mock tools.
    GENIE_SPACES: str = ""

    # Max result rows returned to the LLM (keeps the context bounded).
    GENIE_MAX_ROWS: int = 50
    # Per-question wait budget for Genie (SQL generation + warehouse execution).
    GENIE_TIMEOUT_SECONDS: int = 180
    # SQL warehouse for executing approved/edited SQL. If blank, it's resolved
    # automatically from the Genie space's configured warehouse.
    GENIE_WAREHOUSE_ID: str = ""
    # Where approved (question -> SQL) "tools" are persisted so repeats skip HITL.
    SAVED_QUERIES_PATH: str = str(_ENV_FILE.parent / "data" / "saved_queries.json")

    @property
    def databricks_configured(self) -> bool:
        """True when PAT credentials are present."""
        return bool(self.DATABRICKS_HOST and self.DATABRICKS_TOKEN)


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
