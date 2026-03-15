"""
TELOS Orchestrator — configuration loader.

Reads settings from environment variables and .env files.
All secrets come from env vars only; never hardcoded.
"""

from __future__ import annotations

import os
from pathlib import Path
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings

from services.orchestrator.models import ProviderName


_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Provider
    telos_provider: ProviderName = ProviderName.AZURE

    # Azure OpenAI
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_deployment: str = "gpt-4o"
    azure_openai_api_version: str = "2024-12-01-preview"

    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # Azure AI Foundry (hero tech for AI Dev Days hackathon)
    azure_foundry_endpoint: str = ""
    azure_foundry_api_key: str = ""
    azure_foundry_model: str = ""

    # Google Cloud (Firestore / GCP services)
    google_cloud_project: str = ""
    firestore_collection: str = "telos_tasks"

    # Memory backend: "sqlite" or "firestore"
    telos_memory_backend: str = "sqlite"

    # Orchestrator
    orchestrator_host: str = "127.0.0.1"
    orchestrator_port: int = 8080

    # Scheduler
    scheduler_host: str = "127.0.0.1"
    scheduler_port: int = 8081

    # Windows MCP / UIGraph
    windows_mcp_host: str = "127.0.0.1"
    windows_mcp_port: int = 8083

    # Go Screenshot Engine (screenshot capture)
    screenshot_engine_host: str = "127.0.0.1"
    screenshot_engine_port: int = 8085

    # Rust Delta Engine (visual diff)
    delta_engine_host: str = "127.0.0.1"
    delta_engine_port: int = 8084

    # Privacy
    telos_privacy_mode: str = "strict"
    telos_egress_log: str = "./logs/egress.jsonl"
    telos_allow_image_egress: bool = False
    telos_egress_cache_size: int = 1000

    # Database
    telos_db_path: str = "./telos_memory_db/telos.db"

    # API security
    telos_api_token: str = ""
    telos_internal_token: str = ""

    # Microsoft integrations
    semantic_kernel_enabled: bool = False
    azure_mcp_enabled: bool = False

    # Logging
    telos_log_level: str = "info"

    model_config = {
        "env_file": str(_ENV_FILE) if _ENV_FILE.exists() else None,
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Singleton settings accessor."""
    return Settings()
