"""
TELOS GitHub Models Provider — adapter for GitHub Models (models.inference.ai.azure.com).

GitHub Models provides free-tier access to GPT-4o and other models using a GitHub PAT.
The API is OpenAI-compatible, so this adapter follows the same pattern as AzureProvider.
"""

from __future__ import annotations

import json
import logging

import httpx

from services.orchestrator.models import LLMRequest, LLMResponse, ProviderName
from services.orchestrator.providers.provider_base import ProviderBase
from services.orchestrator.config import get_settings

logger = logging.getLogger("telos.provider.github_models")

_TIMEOUT = httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=10.0)
_BASE_URL = "https://models.inference.ai.azure.com"


class GitHubModelsProvider(ProviderBase):
    """GitHub Models chat completions adapter (OpenAI-compatible)."""

    def __init__(self) -> None:
        s = get_settings()
        self._token = s.github_models_token
        self._model = s.github_models_model
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=_TIMEOUT)
        return self._client

    async def complete(self, request: LLMRequest) -> LLMResponse:
        url = f"{_BASE_URL}/chat/completions"
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
            "model": self._model,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._token}",
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
                    provider=ProviderName.GITHUB_MODELS,
                    model=self._model,
                    usage_prompt_tokens=usage.get("prompt_tokens", 0),
                    usage_completion_tokens=usage.get("completion_tokens", 0),
                    bytes_sent=len(payload_bytes),
                    bytes_received=response_bytes,
                )
            except (httpx.HTTPStatusError, httpx.ConnectError, httpx.ReadTimeout) as exc:
                last_err = exc
                logger.warning("GitHub Models attempt %d failed: %s", attempt + 1, exc)
                if attempt < retries - 1:
                    import asyncio
                    await asyncio.sleep(2 ** attempt)

        raise ConnectionError(f"GitHub Models provider failed after {retries} attempts: {last_err}")

    async def health_check(self) -> bool:
        if not self._token:
            return False
        try:
            client = await self._get_client()
            resp = await client.get(
                f"{_BASE_URL}/models",
                headers={"Authorization": f"Bearer {self._token}"},
            )
            return resp.status_code < 500
        except Exception:
            return False

    def provider_name(self) -> str:
        return ProviderName.GITHUB_MODELS.value
