"""
TELOS Provider — Azure AI Foundry adapter.

Uses the Azure AI Foundry SDK (azure-ai-projects) to interact with models
deployed through Azure AI Foundry, satisfying the hackathon's "Best Use of
Microsoft Foundry" hero technology requirement.

This provider connects to an Azure AI Foundry project and uses its
inference endpoint for chat completions, with full support for multimodal
(text + image) requests.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
from typing import Any

import httpx

from services.orchestrator.models import LLMRequest, LLMResponse, ProviderName
from services.orchestrator.providers.provider_base import ProviderBase
from services.orchestrator.config import get_settings

logger = logging.getLogger("telos.provider.foundry")

_TIMEOUT = httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=10.0)


class FoundryProvider(ProviderBase):
    """Azure AI Foundry adapter.

    Connects to an Azure AI Foundry project and uses the chat completions
    inference endpoint.  Supports text-only and multimodal (image) requests.

    Required environment variables:
        AZURE_FOUNDRY_ENDPOINT  — your Foundry project endpoint
                                  (e.g. https://<project>.services.ai.azure.com)
        AZURE_FOUNDRY_API_KEY   — API key for the project
        AZURE_FOUNDRY_MODEL     — deployed model name (default: gpt-4o)
    """

    def __init__(self) -> None:
        s = get_settings()
        self._endpoint = s.azure_foundry_endpoint.rstrip("/")
        self._api_key = s.azure_foundry_api_key
        self._model = s.azure_foundry_model or s.azure_openai_deployment or "gpt-4o"
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=_TIMEOUT)
        return self._client

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Send a chat completion request through Azure AI Foundry."""
        if not self._endpoint or not self._api_key:
            raise ConnectionError(
                "Azure Foundry provider requires AZURE_FOUNDRY_ENDPOINT and "
                "AZURE_FOUNDRY_API_KEY environment variables."
            )

        url = f"{self._endpoint}/openai/deployments/{self._model}/chat/completions?api-version=2024-12-01-preview"

        messages: list[dict[str, Any]] = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})

        # Multimodal support — send image inline
        if request.image_data and request.image_mime:
            b64_img = base64.b64encode(request.image_data).decode()
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": request.user_prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{request.image_mime};base64,{b64_img}"},
                    },
                ],
            })
        else:
            messages.append({"role": "user", "content": request.user_prompt})

        body = {
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }
        headers = {
            "Content-Type": "application/json",
            "api-key": self._api_key,
        }

        payload_bytes = json.dumps(body).encode()
        client = await self._get_client()

        retries = 3
        last_err: Exception | None = None
        for attempt in range(retries):
            try:
                resp = await client.post(url, content=payload_bytes, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                response_bytes = len(resp.content)

                return LLMResponse(
                    content=content,
                    provider=ProviderName.AZURE_FOUNDRY,
                    model=self._model,
                    usage_prompt_tokens=usage.get("prompt_tokens", 0),
                    usage_completion_tokens=usage.get("completion_tokens", 0),
                    bytes_sent=len(payload_bytes),
                    bytes_received=response_bytes,
                )
            except (httpx.HTTPStatusError, httpx.ConnectError, httpx.ReadTimeout) as exc:
                last_err = exc
                logger.warning("Foundry attempt %d failed: %s", attempt + 1, exc)
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)

        raise ConnectionError(f"Azure Foundry provider failed after {retries} attempts: {last_err}")

    async def health_check(self) -> bool:
        """Check that the Foundry endpoint is reachable."""
        if not self._endpoint or not self._api_key:
            return False
        try:
            client = await self._get_client()
            resp = await client.get(
                f"{self._endpoint}/openai/deployments?api-version=2024-12-01-preview",
                headers={"api-key": self._api_key},
            )
            return resp.status_code < 500
        except Exception:
            return False

    def provider_name(self) -> str:
        return ProviderName.AZURE_FOUNDRY.value
