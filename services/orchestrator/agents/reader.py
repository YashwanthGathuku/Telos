"""
TELOS Reader Agent — reads structured data from source applications via UIGraph.

Communicates with the Windows UIA subsystem to extract field values
from desktop applications.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
from httpx import AsyncClient

from services.orchestrator.agents.base import AgentBase
from services.orchestrator.models import AgentRole, UISnapshot
from services.orchestrator.config import get_settings
from services.orchestrator.privacy.egress import get_egress_logger

logger = logging.getLogger("telos.agent.reader")

_TIMEOUT = httpx.Timeout(connect=5.0, read=15.0, write=5.0, pool=5.0)


class ReaderAgent(AgentBase):
    """Reads structured state from Windows applications via the UIGraph service."""

    def role(self) -> AgentRole:
        return AgentRole.READER

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        app_name: str = context.get("app", "")
        field_detail: str = context.get("detail", "")
        action: str = context.get("action", "read_field")

        if not app_name:
            return {"error": "No target application specified"}

        s = get_settings()
        egress = get_egress_logger()
        base_url = f"http://{s.windows_mcp_host}:{s.windows_mcp_port}"

        try:
            async with AsyncClient(timeout=_TIMEOUT) as client:
                # Request UI snapshot from the Windows MCP service
                payload = {"app_name": app_name, "detail": field_detail}
                bytes_sent = len(str(payload).encode("utf-8"))
                resp = await client.post(
                    f"{base_url}/uigraph/snapshot",
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                bytes_received = len(resp.content)

                egress.record(
                    destination=f"uigraph/{s.windows_mcp_host}:{s.windows_mcp_port}",
                    bytes_sent=bytes_sent,
                    bytes_received=bytes_received,
                    provider="uigraph",
                    task_id=str(context.get("task_id", "")),
                )

                snapshot = UISnapshot(**data.get("snapshot", data))
                # Search for the relevant value in the UI tree
                value = self._extract_value(snapshot, field_detail)

                return {
                    "app": app_name,
                    "field": field_detail,
                    "value": value,
                    "snapshot_element_count": self._count_elements(snapshot),
                    "source": "uia",
                }
        except httpx.ConnectError:
            logger.warning("UIGraph service not available, using fallback")
            return {
                "app": app_name,
                "field": field_detail,
                "value": None,
                "error": "UIGraph service unavailable",
                "source": "unavailable",
            }
        except Exception as exc:
            logger.exception("Reader agent failed")
            return {"error": str(exc)}

    def _extract_value(self, snapshot: UISnapshot, detail: str) -> str | None:
        """Search the UI tree for elements matching the detail description."""
        detail_lower = detail.lower()
        for elem in self._flatten_elements(snapshot.elements):
            if elem.is_password:
                continue  # Never expose password field values
            name_lower = elem.name.lower()
            if any(kw in name_lower for kw in detail_lower.split() if len(kw) > 2):
                if elem.value:
                    return elem.value
        return None

    def _flatten_elements(self, elements: list) -> list:
        """Flatten nested UI element tree."""
        result = []
        for elem in elements:
            result.append(elem)
            if elem.children:
                result.extend(self._flatten_elements(elem.children))
        return result

    def _count_elements(self, snapshot: UISnapshot) -> int:
        return len(self._flatten_elements(snapshot.elements))
