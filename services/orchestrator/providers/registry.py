"""
TELOS provider registry.

The submission build exposes a single Gemini provider but keeps the request-scoped
override flow in place so the HTTP contract stays stable.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar

from services.orchestrator.config import get_settings
from services.orchestrator.models import ProviderName
from services.orchestrator.providers.gemini_provider import GeminiProvider
from services.orchestrator.providers.provider_base import ProviderBase


_provider_override: ContextVar[ProviderName | None] = ContextVar("telos_provider_override", default=None)


def coerce_provider_name(value: ProviderName | str | None) -> ProviderName | None:
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
        raise ValueError("Unknown provider override. Valid: gemini") from exc


def get_provider_name(value: ProviderName | str | None = None) -> ProviderName:
    explicit = coerce_provider_name(value)
    if explicit is not None:
        return explicit

    override = _provider_override.get()
    if override is not None:
        return override

    return get_settings().telos_provider


@contextmanager
def provider_override(value: ProviderName | str | None):
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
    name = get_provider_name(value)
    if name != ProviderName.GEMINI:
        raise ValueError("Unknown provider override. Valid: gemini")
    return GeminiProvider()
