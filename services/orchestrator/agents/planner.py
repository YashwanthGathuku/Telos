"""
TELOS Planner Agent — decomposes a natural-language task into an execution plan.

Uses the LLM provider to analyze the task and produce ordered steps for
the reader, writer, and verifier agents.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from services.orchestrator.agents.base import AgentBase
from services.orchestrator.models import AgentRole, LLMRequest
from services.orchestrator.providers.provider_base import ProviderBase
from services.orchestrator.privacy.filter import filter_for_egress

logger = logging.getLogger("telos.agent.planner")

_SYSTEM_PROMPT = """You are the TELOS Planner Agent. Your job is to decompose a user's desktop automation task into concrete, ordered steps.

Each step must specify:
- "agent": one of "reader", "writer", "verifier"
- "action": a short description of what to do
- "app": the target application name
- "detail": specifics (field name, cell reference, value to look for, etc.)

Return a JSON array of step objects. Nothing else.

Example:
[
  {"agent": "reader", "action": "read_field", "app": "QuickBooks", "detail": "Q1 sales total from the Sales Summary report"},
  {"agent": "writer", "action": "write_cell", "app": "Excel", "detail": "Write the extracted value into cell B4"},
  {"agent": "verifier", "action": "verify_write", "app": "Excel", "detail": "Confirm cell B4 contains the expected value"}
]"""


class PlannerAgent(AgentBase):
    """Decomposes tasks into multi-step execution plans."""

    def __init__(self, provider: ProviderBase) -> None:
        self._provider = provider

    def role(self) -> AgentRole:
        return AgentRole.PLANNER

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        task: str = context.get("task", "")
        if not task:
            return {"error": "No task provided", "steps": []}

        # Apply privacy filter before sending to LLM
        fr = filter_for_egress(task)
        filtered_task = fr.filtered_text

        request = LLMRequest(
            system_prompt=_SYSTEM_PROMPT,
            user_prompt=f"Task: {filtered_task}",
            temperature=0.1,
            max_tokens=1024,
        )

        try:
            response = await self._provider.complete(request)
            # Parse the JSON array from the response
            text = response.content.strip()
            # Handle markdown code fences
            if text.startswith("```"):
                text = text.split("\n", 1)[1] if "\n" in text else text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()
            if text.startswith("json"):
                text = text[4:].strip()

            steps = json.loads(text)
            if not isinstance(steps, list):
                steps = [steps]

            return {
                "steps": steps,
                "privacy": {
                    "fields_masked": fr.fields_masked,
                    "pii_blocked": fr.pii_blocked,
                },
                "provider_usage": {
                    "bytes_sent": response.bytes_sent,
                    "bytes_received": response.bytes_received,
                    "model": response.model,
                },
            }
        except json.JSONDecodeError:
            logger.warning("Planner returned non-JSON, using raw text")
            return {
                "steps": [{"agent": "reader", "action": "interpret", "app": "unknown", "detail": task}],
                "raw_response": response.content if 'response' in dir() else "",
            }
        except Exception as exc:
            logger.exception("Planner execution failed")
            return {"error": str(exc), "steps": []}
