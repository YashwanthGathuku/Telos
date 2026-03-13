"""
TELOS Provider Base — abstract contract for all LLM providers.

Every provider adapter (Azure, Gemini) must implement this interface.
Provider selection is controlled by the TELOS_PROVIDER environment variable.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from services.orchestrator.models import LLMRequest, LLMResponse


class ProviderBase(ABC):
    """Abstract LLM provider contract."""

    @abstractmethod
    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Send a completion request and return a normalized response."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if the provider is reachable and authenticated."""
        ...

    @abstractmethod
    def provider_name(self) -> str:
        """Return the canonical provider identifier."""
        ...
