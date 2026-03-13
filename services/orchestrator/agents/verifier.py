"""
TELOS Verifier Agent — confirms that actions were executed correctly.

Re-reads the target application state after writes and compares
against expected values.
"""

from __future__ import annotations

import logging
from typing import Any

from services.orchestrator.agents.base import AgentBase
from services.orchestrator.agents.reader import ReaderAgent
from services.orchestrator.models import AgentRole

logger = logging.getLogger("telos.agent.verifier")


class VerifierAgent(AgentBase):
    """Verifies that a write action produced the expected result."""

    def __init__(self) -> None:
        self._reader = ReaderAgent()

    def role(self) -> AgentRole:
        return AgentRole.VERIFIER

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        app_name: str = context.get("app", "")
        expected_value: str = context.get("expected_value", "")
        detail: str = context.get("detail", "")

        if not app_name or not expected_value:
            return {"verified": False, "error": "Missing app or expected value"}

        # Re-read the target field
        read_result = await self._reader.execute({
            "app": app_name,
            "detail": detail,
            "action": "read_field",
        })

        actual_value = read_result.get("value")
        if actual_value is None:
            return {
                "verified": False,
                "reason": "Could not re-read target field",
                "read_result": read_result,
            }

        # Normalize for comparison
        match = str(actual_value).strip() == str(expected_value).strip()
        return {
            "verified": match,
            "expected": expected_value,
            "actual": actual_value,
            "app": app_name,
            "field": detail,
        }
