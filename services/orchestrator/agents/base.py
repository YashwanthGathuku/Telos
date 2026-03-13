"""
TELOS Agent Base — abstract contract for specialist agents.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from services.orchestrator.models import AgentRole


class AgentBase(ABC):
    """Base class for all TELOS specialist agents."""

    @abstractmethod
    def role(self) -> AgentRole:
        ...

    @abstractmethod
    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """Execute the agent's responsibility and return results."""
        ...
