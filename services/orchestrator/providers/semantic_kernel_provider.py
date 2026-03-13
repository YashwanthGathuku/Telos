"""
TELOS Provider — Microsoft Semantic Kernel adapter.

Uses the official semantic-kernel Python SDK to interact with Azure OpenAI.
This satisfies the "Microsoft Agent Framework" hero technology requirement
for the AI Dev Days hackathon.
"""

from __future__ import annotations

import logging
from typing import Any

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import AzureChatPromptExecutionSettings
from semantic_kernel.contents.utils.author_role import AuthorRole

from services.orchestrator.models import LLMRequest, LLMResponse, ProviderName
from services.orchestrator.providers.provider_base import ProviderBase
from services.orchestrator.config import get_settings

logger = logging.getLogger("telos.provider.semantic_kernel")


class SemanticKernelProvider(ProviderBase):
    """Answers via Azure OpenAI, routed through Microsoft Semantic Kernel."""

    def __init__(self) -> None:
        s = get_settings()
        if not s.azure_openai_api_key or not s.azure_openai_endpoint:
            raise ValueError("AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT required for SK Provider")

        self.deployment = s.azure_openai_deployment

        # Initialize Semantic Kernel
        self.kernel = Kernel()

        # Add Azure OpenAI Chat Completion service
        service_id = "default"
        chat_service = AzureChatCompletion(
            service_id=service_id,
            deployment_name=self.deployment,
            endpoint=s.azure_openai_endpoint,
            api_key=s.azure_openai_api_key,
        )
        self.kernel.add_service(chat_service)

    def provider_name(self) -> str:
        return ProviderName.AZURE_SK.value

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Execute the prompt using Semantic Kernel."""
        chat_service: ChatCompletionClientBase = self.kernel.get_service("default")

        # Configure execution settings
        settings = AzureChatPromptExecutionSettings(
            service_id="default",
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        # Build Chat History
        history = ChatHistory()
        if request.system_prompt:
            history.add_system_message(request.system_prompt)

        # Handle multimodal vs text-only
        if request.image_data and request.image_mime:
            from semantic_kernel.contents import TextContent, ImageContent
            history.add_user_message([
                TextContent(text=request.user_prompt),
                ImageContent(
                    data=request.image_data, 
                    data_format=request.image_mime.split("/")[-1], # e.g. "png"
                )
            ])
        else:
            history.add_user_message(request.user_prompt)

        # Invoke semantic kernel chat
        try:
            response_contents = await chat_service.get_chat_message_contents(
                chat_history=history,
                settings=settings,
                kernel=self.kernel,
            )

            if not response_contents:
                raise ValueError("Semantic Kernel returned empty response")

            reply = response_contents[0].content
            # SK doesn't expose usage metadata as directly in the standard response as raw httpx,
            # but we estimate or extract if present. For the hackathon, we pass through simple mocked metrics.
            
            return LLMResponse(
                content=reply or "",
                provider=self.provider_name(),
                bytes_sent=len(request.user_prompt),
                bytes_received=len(reply) if reply else 0,
                usage_prompt_tokens=0,      # Requires deeper extraction from SK inner context
                usage_completion_tokens=0,
            )

        except Exception as exc:
            logger.exception("Semantic Kernel completion failed")
            raise ConnectionError(f"SK provider failed: {exc}")

    async def health_check(self) -> bool:
        """Verify the service is reachable by sending a tiny test ping."""
        try:
            req = LLMRequest(user_prompt="ping", max_tokens=2, temperature=0.0)
            resp = await self.complete(req)
            return len(resp.content) > 0
        except Exception:
            return False
