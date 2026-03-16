"""
TELOS provider base contract.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from services.orchestrator.models import LLMRequest, LLMResponse


class ProviderBase(ABC):
    """Abstract LLM provider contract."""

    @abstractmethod
    async def complete(self, request: LLMRequest) -> LLMResponse:
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        ...

    @abstractmethod
    def provider_name(self) -> str:
        ...
