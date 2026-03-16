"""
TELOS Orchestrator configuration loader.

This submission build is Gemini-first and keeps the local .env out of tests.
"""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings

from services.orchestrator.models import ProviderName


_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


def _env_file_for_runtime() -> str | None:
    if not _ENV_FILE.exists():
        return None
    if "pytest" in sys.modules or "_pytest" in sys.modules:
        return None
    return str(_ENV_FILE)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    telos_provider: ProviderName = ProviderName.GEMINI

    gemini_api_key: str = ""
    google_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    google_cloud_project: str = ""
    firestore_collection: str = "telos_tasks"
    telos_memory_backend: str = "sqlite"

    orchestrator_host: str = "127.0.0.1"
    orchestrator_port: int = 8080

    scheduler_host: str = "127.0.0.1"
    scheduler_port: int = 8081

    windows_mcp_host: str = "127.0.0.1"
    windows_mcp_port: int = 8083

    screenshot_engine_host: str = "127.0.0.1"
    screenshot_engine_port: int = 8085

    delta_engine_host: str = "127.0.0.1"
    delta_engine_port: int = 8084

    telos_privacy_mode: str = "strict"
    telos_egress_log: str = "./logs/egress.jsonl"
    telos_allow_image_egress: bool = False
    telos_egress_cache_size: int = 1000

    telos_db_path: str = "./telos_memory_db/telos.db"

    telos_api_token: str = ""
    telos_internal_token: str = ""

    telos_mcp_enabled: bool = False
    telos_log_level: str = "info"

    model_config = {
        "env_file": _env_file_for_runtime(),
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
