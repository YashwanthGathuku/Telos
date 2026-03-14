"""
TELOS Vision Agent — screen capture and multimodal interpretation.

Fetches a screenshot from the Rust capture engine, then sends it to
the configured LLM provider (using multimodal capabilities) to extract
information or summarize the screen state.
"""

from __future__ import annotations

import base64
import logging
from typing import Any

import httpx

from services.orchestrator.models import AgentRole, LLMRequest
from services.orchestrator.agents.base import AgentBase
from services.orchestrator.providers.registry import get_provider
from services.orchestrator.config import get_settings
from services.orchestrator.privacy.egress import get_egress_logger
from services.orchestrator.providers.provider_base import ProviderBase

logger = logging.getLogger("telos.agent.vision")


class VisionAgent(AgentBase):
    """Agent that sees the screen and extracts information."""

    def __init__(self, provider: ProviderBase | None = None) -> None:
        s = get_settings()
        self._provider = provider or get_provider()
        self._capture_url = f"http://{s.capture_engine_host}:{s.capture_engine_port}/capture/screen"
        self._timeout = httpx.Timeout(connect=2.0, read=10.0, write=2.0, pool=2.0)
        self._egress = get_egress_logger()
        self._allow_image_egress = s.telos_allow_image_egress or s.telos_privacy_mode.lower() != "strict"

    def role(self) -> AgentRole:
        return AgentRole.VISION

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Capture screen and ask LLM about it.
        context["detail"] bounds what we ask the LLM to look for.
        """
        detail = context.get("detail", "Describe what is on the screen.")
        logger.info("VisionAgent executing: %s", detail)

        if not self._allow_image_egress:
            return {
                "error": (
                    "VisionAgent blocked by privacy mode. "
                    "Set TELOS_ALLOW_IMAGE_EGRESS=true or use a non-strict privacy mode to allow screenshot uploads."
                )
            }

        # 1. Capture screenshot from Rust engine
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(self._capture_url)
                resp.raise_for_status()
                data = resp.json()
                base64_png = data.get("image")
                if not base64_png:
                    raise ValueError("Rust engine returned empty image")
                image_bytes = base64.b64decode(base64_png)
        except Exception as exc:
            msg = f"VisionAgent failed to capture screen: {exc}"
            logger.error(msg)
            return {"error": msg}

        # 2. Send to LLM
        prompt = (
            f"You are a computer vision agent. Look at this screenshot and answer the user's request.\n"
            f"Request: {detail}\n"
            f"Be precise and concise. Only answer the request."
        )

        req = LLMRequest(
            user_prompt=prompt,
            image_data=image_bytes,
            image_mime="image/png",
            temperature=0.1,
            max_tokens=500,
        )
        bytes_sent = len(prompt.encode("utf-8")) + len(image_bytes)

        try:
            response = await self._provider.complete(req)
            self._egress.record(
                destination=f"llm/{self._provider.provider_name()}",
                bytes_sent=bytes_sent,
                bytes_received=response.bytes_received,
                provider=self._provider.provider_name(),
                task_id=str(context.get("task_id", "")),
            )
            return {
                "value": response.content.strip(),
                "bytes_sent": bytes_sent,
                "bytes_received": response.bytes_received,
            }
        except Exception as exc:
            msg = f"VisionAgent LLM call failed: {exc}"
            logger.error(msg)
            return {"error": msg}
