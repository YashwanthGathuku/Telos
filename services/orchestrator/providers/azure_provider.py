"""
TELOS Azure OpenAI Provider — adapter for Azure OpenAI Service.

Uses httpx with explicit timeouts. Credentials loaded from environment only.
"""

from __future__ import annotations

import json
import logging

import httpx

from services.orchestrator.models import LLMRequest, LLMResponse, ProviderName
from services.orchestrator.providers.provider_base import ProviderBase
from services.orchestrator.config import get_settings

logger = logging.getLogger("telos.provider.azure")

_TIMEOUT = httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=10.0)


class AzureProvider(ProviderBase):
    """Azure OpenAI chat completions adapter."""

    def __init__(self) -> None:
        s = get_settings()
        self._endpoint = s.azure_openai_endpoint.rstrip("/")
        self._api_key = s.azure_openai_api_key
        self._deployment = s.azure_openai_deployment
        self._api_version = s.azure_openai_api_version
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=_TIMEOUT)
        return self._client

    async def complete(self, request: LLMRequest) -> LLMResponse:
        url = (
            f"{self._endpoint}/openai/deployments/{self._deployment}"
            f"/chat/completions?api-version={self._api_version}"
        )
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})

        if request.image_data and request.image_mime:
            import base64
            b64_img = base64.b64encode(request.image_data).decode()
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": request.user_prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{request.image_mime};base64,{b64_img}"}
                    }
                ]
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
                    provider=ProviderName.AZURE,
                    model=self._deployment,
                    usage_prompt_tokens=usage.get("prompt_tokens", 0),
                    usage_completion_tokens=usage.get("completion_tokens", 0),
                    bytes_sent=len(payload_bytes),
                    bytes_received=response_bytes,
                )
            except (httpx.HTTPStatusError, httpx.ConnectError, httpx.ReadTimeout) as exc:
                last_err = exc
                logger.warning("Azure attempt %d failed: %s", attempt + 1, exc)
                if attempt < retries - 1:
                    import asyncio
                    await asyncio.sleep(2 ** attempt)

        raise ConnectionError(f"Azure provider failed after {retries} attempts: {last_err}")

    async def health_check(self) -> bool:
        if not self._endpoint or not self._api_key:
            return False
        try:
            client = await self._get_client()
            resp = await client.get(
                f"{self._endpoint}/openai/deployments?api-version={self._api_version}",
                headers={"api-key": self._api_key},
            )
            return resp.status_code < 500
        except Exception:
            return False

    def provider_name(self) -> str:
        return ProviderName.AZURE.value
