"""
TELOS Provider Registry — factory for provider selection.

Reads TELOS_PROVIDER from the environment and returns the matching adapter.
"""

from __future__ import annotations

from services.orchestrator.models import ProviderName
from services.orchestrator.providers.provider_base import ProviderBase
from services.orchestrator.providers.azure_provider import AzureProvider
from services.orchestrator.providers.gemini_provider import GeminiProvider
from services.orchestrator.providers.semantic_kernel_provider import SemanticKernelProvider
from services.orchestrator.config import get_settings


_REGISTRY: dict[ProviderName, type[ProviderBase]] = {
    ProviderName.AZURE: AzureProvider,
    ProviderName.AZURE_SK: SemanticKernelProvider,
    ProviderName.GEMINI: GeminiProvider,
}


def get_provider() -> ProviderBase:
    """Instantiate the provider selected by TELOS_PROVIDER env var."""
    name = get_settings().telos_provider
    cls = _REGISTRY.get(name)
    if cls is None:
        raise ValueError(f"Unknown provider: {name!r}. Valid: {list(_REGISTRY)}")
    return cls()
