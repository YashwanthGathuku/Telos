"""
TELOS Gemini Provider — adapter using official Google GenAI SDK.

Uses the google-genai SDK for Gemini API access, supporting both text
and multimodal (image) requests. Credentials loaded from environment only.
"""

from __future__ import annotations

import logging

from google import genai
from google.genai import types

from services.orchestrator.models import LLMRequest, LLMResponse, ProviderName
from services.orchestrator.providers.provider_base import ProviderBase
from services.orchestrator.config import get_settings

logger = logging.getLogger("telos.provider.gemini")


class GeminiProvider(ProviderBase):
    """Google Gemini adapter using official GenAI SDK."""

    def __init__(self) -> None:
        s = get_settings()
        self._api_key = s.gemini_api_key
        self._model = s.gemini_model
        self._client: genai.Client | None = None

    def _get_client(self) -> genai.Client:
        if self._client is None:
            self._client = genai.Client(api_key=self._api_key)
        return self._client

    async def complete(self, request: LLMRequest) -> LLMResponse:
        client = self._get_client()

        # Build contents — supports text-only and multimodal (text + image)
        parts: list[types.Part] = []
        if request.system_prompt:
            parts.append(types.Part.from_text(text=f"[System] {request.system_prompt}\n\n"))
        parts.append(types.Part.from_text(text=request.user_prompt))

        # Multimodal: attach image if provided
        if request.image_data and request.image_mime:
            parts.append(types.Part.from_bytes(
                data=request.image_data,
                mime_type=request.image_mime,
            ))

        config = types.GenerateContentConfig(
            temperature=request.temperature,
            max_output_tokens=request.max_tokens,
        )

        # Estimate bytes sent
        prompt_text = request.user_prompt + (request.system_prompt or "")
        bytes_sent = len(prompt_text.encode()) + len(request.image_data or b"")

        retries = 3
        last_err: Exception | None = None
        for attempt in range(retries):
            try:
                response = client.models.generate_content(
                    model=self._model,
                    contents=parts,
                    config=config,
                )
                content = response.text or ""
                bytes_received = len(content.encode())

                # Extract usage from response metadata
                usage_prompt = 0
                usage_completion = 0
                if hasattr(response, "usage_metadata") and response.usage_metadata:
                    usage_prompt = getattr(response.usage_metadata, "prompt_token_count", 0) or 0
                    usage_completion = getattr(response.usage_metadata, "candidates_token_count", 0) or 0

                return LLMResponse(
                    content=content,
                    provider=ProviderName.GEMINI,
                    model=self._model,
                    usage_prompt_tokens=usage_prompt,
                    usage_completion_tokens=usage_completion,
                    bytes_sent=bytes_sent,
                    bytes_received=bytes_received,
                )
            except Exception as exc:
                last_err = exc
                logger.warning("Gemini attempt %d failed: %s", attempt + 1, exc)
                if attempt < retries - 1:
                    import asyncio
                    await asyncio.sleep(2 ** attempt)

        raise ConnectionError(f"Gemini provider failed after {retries} attempts: {last_err}")

    async def health_check(self) -> bool:
        if not self._api_key:
            return False
        try:
            client = self._get_client()
            # List models to verify connectivity
            models = client.models.list()
            return True
        except Exception:
            return False

    def provider_name(self) -> str:
        return ProviderName.GEMINI.value
