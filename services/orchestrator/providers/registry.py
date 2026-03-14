"""
TELOS Provider Registry — factory for provider selection.

Reads TELOS_PROVIDER from the environment and returns the matching adapter.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar

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

_provider_override: ContextVar[ProviderName | None] = ContextVar("telos_provider_override", default=None)


def coerce_provider_name(value: ProviderName | str | None) -> ProviderName | None:
    """Normalize a provider override from headers/UI state."""
    if value is None:
        return None
    if isinstance(value, ProviderName):
        return value

    raw = value.strip().lower()
    if not raw:
        return None
    try:
        return ProviderName(raw)
    except ValueError as exc:
        valid = ", ".join(name.value for name in ProviderName)
        raise ValueError(f"Unknown provider override {value!r}. Valid: {valid}") from exc


def get_provider_name(value: ProviderName | str | None = None) -> ProviderName:
    """Resolve the active provider, honoring request-scoped overrides."""
    explicit = coerce_provider_name(value)
    if explicit is not None:
        return explicit

    override = _provider_override.get()
    if override is not None:
        return override

    return get_settings().telos_provider


@contextmanager
def provider_override(value: ProviderName | str | None):
    """Temporarily override provider selection for a single request/task."""
    override = coerce_provider_name(value)
    if override is None:
        yield
        return

    token = _provider_override.set(override)
    try:
        yield
    finally:
        _provider_override.reset(token)


def get_provider(value: ProviderName | str | None = None) -> ProviderBase:
    """Instantiate the provider selected by TELOS_PROVIDER env var."""
    name = get_provider_name(value)
    cls = _REGISTRY.get(name)
    if cls is None:
        raise ValueError(f"Unknown provider: {name!r}. Valid: {list(_REGISTRY)}")
    return cls()
