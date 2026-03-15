"""
TELOS Writer Agent — writes values into target applications via UIGraph.

Communicates with the Windows UIA subsystem to focus windows,
locate target fields, and write values.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
from httpx import AsyncClient

from services.orchestrator.agents.base import AgentBase
from services.orchestrator.models import AgentRole
from services.orchestrator.config import get_settings
from services.orchestrator.privacy.egress import get_egress_logger

logger = logging.getLogger("telos.agent.writer")

_TIMEOUT = httpx.Timeout(connect=5.0, read=15.0, write=5.0, pool=5.0)


class WriterAgent(AgentBase):
    """Writes values into target application fields via UIGraph."""

    def role(self) -> AgentRole:
        return AgentRole.WRITER

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        app_name: str = context.get("app", "")
        detail: str = context.get("detail", "")
        value: str = context.get("value", "")

        if not app_name or not value:
            return {"error": "Missing app or value for write operation"}

        s = get_settings()
        egress = get_egress_logger()
        base_url = f"http://{s.windows_mcp_host}:{s.windows_mcp_port}"

        try:
            async with AsyncClient(timeout=_TIMEOUT) as client:
                # Focus the target application window
                focus_payload = {"app_name": app_name}
                await client.post(
                    f"{base_url}/uigraph/focus",
                    json=focus_payload,
                )

                # Execute the write action with retry logic
                import asyncio
                last_exc = None
                action_payload = {
                    "app_name": app_name,
                    "action": "write_value",
                    "target": detail,
                    "value": value,
                }
                bytes_sent = len(str(action_payload).encode("utf-8"))
                for attempt in range(3):
                    try:
                        resp = await client.post(
                            f"{base_url}/uigraph/action",
                            json=action_payload,
                        )
                        resp.raise_for_status()
                        result = resp.json()
                        egress.record(
                            destination=f"uigraph/{s.windows_mcp_host}:{s.windows_mcp_port}",
                            bytes_sent=bytes_sent,
                            bytes_received=len(resp.content),
                            provider="uigraph",
                            task_id=str(context.get("task_id", "")),
                        )
                        if result.get("success", False):
                            return {
                                "app": app_name,
                                "action": "write_value",
                                "target": detail,
                                "value": value,
                                "success": True,
                                "source": "uia",
                            }
                    except httpx.HTTPError as exc:
                        logger.warning(f"Write failure on attempt {attempt+1}: {exc}")
                        last_exc = exc

                    await asyncio.sleep(min(1.0 * (2 ** attempt), 4.0))

                if last_exc:
                    raise last_exc
                return {"error": "Write action failed after 3 retries", "success": False}
        except httpx.ConnectError:
            logger.warning("UIGraph service not available for write")
            return {
                "app": app_name,
                "target": detail,
                "value": value,
                "error": "UIGraph service unavailable",
                "success": False,
            }
        except Exception as exc:
            logger.exception("Writer agent failed")
            return {"error": str(exc), "success": False}
