"""
TELOS Tests — Provider contract tests.

Verifies that all providers implement ProviderBase correctly
and that the registry selects the right adapter.
"""

import pytest
from services.orchestrator.providers.provider_base import ProviderBase
from services.orchestrator.providers.azure_provider import AzureProvider
from services.orchestrator.providers.gemini_provider import GeminiProvider
from services.orchestrator.providers.semantic_kernel_provider import SemanticKernelProvider
from services.orchestrator.providers.registry import get_provider, _REGISTRY
from services.orchestrator.models import LLMRequest, ProviderName


class TestProviderContract:
    """Verify all providers implement the base contract."""

    @pytest.mark.parametrize("cls", [AzureProvider, GeminiProvider, SemanticKernelProvider])
    def test_is_subclass_of_base(self, cls):
        assert issubclass(cls, ProviderBase)

    @pytest.mark.parametrize("cls", [AzureProvider, GeminiProvider, SemanticKernelProvider])
    def test_has_complete_method(self, cls):
        assert hasattr(cls, "complete")
        assert callable(getattr(cls, "complete"))

    @pytest.mark.parametrize("cls", [AzureProvider, GeminiProvider, SemanticKernelProvider])
    def test_has_health_check_method(self, cls):
        assert hasattr(cls, "health_check")
        assert callable(getattr(cls, "health_check"))

    @pytest.mark.parametrize("cls", [AzureProvider, GeminiProvider, SemanticKernelProvider])
    def test_has_provider_name_method(self, cls):
        assert hasattr(cls, "provider_name")

    def test_azure_provider_name(self):
        provider = AzureProvider()
        assert provider.provider_name() == "azure"

    def test_gemini_provider_name(self):
        provider = GeminiProvider()
        assert provider.provider_name() == "gemini"

    def test_azure_sk_provider_name(self, monkeypatch):
        # SK requires env vars on init
        monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test")
        monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://test.openai.azure.com")
        from services.orchestrator.config import get_settings
        get_settings.cache_clear()
        provider = SemanticKernelProvider()
        assert provider.provider_name() == "azure_sk"
        get_settings.cache_clear()


class TestProviderRegistry:
    def test_registry_has_both_providers(self):
        assert ProviderName.AZURE in _REGISTRY
        assert ProviderName.GEMINI in _REGISTRY

    def test_get_provider_returns_instance(self, monkeypatch):
        monkeypatch.setenv("TELOS_PROVIDER", "azure")
        # Clear cached settings
        from services.orchestrator.config import get_settings
        get_settings.cache_clear()
        provider = get_provider()
        assert isinstance(provider, ProviderBase)
        get_settings.cache_clear()

    def test_get_provider_gemini(self, monkeypatch):
        monkeypatch.setenv("TELOS_PROVIDER", "gemini")
        from services.orchestrator.config import get_settings
        get_settings.cache_clear()
        provider = get_provider()
        assert isinstance(provider, GeminiProvider)
        get_settings.cache_clear()


class TestLLMRequest:
    def test_request_validation(self):
        req = LLMRequest(user_prompt="Test prompt")
        assert req.user_prompt == "Test prompt"
        assert req.temperature == 0.2
        assert req.max_tokens == 2048

    def test_request_with_system_prompt(self):
        req = LLMRequest(system_prompt="You are helpful", user_prompt="Hello")
        assert req.system_prompt == "You are helpful"


# ── Retry / Exponential Backoff Tests ────────────────────────────────────

class TestAzureRetry:
    """Verify Azure provider retry with exponential backoff."""

    @pytest.fixture
    def azure_provider(self, monkeypatch):
        monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://test.openai.azure.com")
        monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4")
        from services.orchestrator.config import get_settings
        get_settings.cache_clear()
        p = AzureProvider()
        get_settings.cache_clear()
        return p

    @pytest.mark.asyncio
    async def test_retry_then_succeed(self, azure_provider, monkeypatch):
        """Fail twice then succeed on third attempt."""
        import httpx

        call_count = 0

        async def mock_post(self_client, url, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.ConnectError("connection refused")
            # Simulate success on 3rd call
            return httpx.Response(
                200,
                json={
                    "choices": [{"message": {"content": "Hello!"}}],
                    "usage": {"prompt_tokens": 5, "completion_tokens": 3},
                },
                request=httpx.Request("POST", url),
            )

        monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)
        # Speed up sleeps
        import asyncio

        async def noop_sleep(_): pass
        monkeypatch.setattr(asyncio, "sleep", noop_sleep)

        req = LLMRequest(user_prompt="test")
        resp = await azure_provider.complete(req)

        assert resp.content == "Hello!"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_exhausted(self, azure_provider, monkeypatch):
        """All 3 attempts fail → ConnectionError."""
        import httpx

        async def mock_post(self_client, url, **kwargs):
            raise httpx.ConnectError("connection refused")

        monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)
        import asyncio

        async def noop_sleep(_): pass
        monkeypatch.setattr(asyncio, "sleep", noop_sleep)

        req = LLMRequest(user_prompt="test")
        with pytest.raises(ConnectionError, match="Azure provider failed after 3 attempts"):
            await azure_provider.complete(req)


class TestGeminiRetry:
    """Verify Gemini provider retry with exponential backoff using google-genai SDK."""

    @pytest.fixture
    def gemini_provider(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")
        monkeypatch.setenv("GEMINI_MODEL", "gemini-2.0-flash")
        from services.orchestrator.config import get_settings
        get_settings.cache_clear()
        p = GeminiProvider()
        get_settings.cache_clear()
        return p

    @pytest.mark.asyncio
    async def test_retry_then_succeed(self, gemini_provider, monkeypatch):
        """Fail twice then succeed on third attempt."""
        from google import genai
        import google.api_core.exceptions

        call_count = 0

        class MockModels:
            def generate_content(self, *args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count < 3:
                    raise google.api_core.exceptions.ServiceUnavailable("API down")
                    
                class MockUsage:
                    prompt_token_count = 5
                    candidates_token_count = 3
                    
                class MockResponse:
                    text = "Success!"
                    usage_metadata = MockUsage()
                    
                return MockResponse()

        class MockClient:
            def __init__(self, *args, **kwargs):
                self.models = MockModels()

        monkeypatch.setattr(genai, "Client", MockClient)
        import asyncio

        async def noop_sleep(_): pass
        monkeypatch.setattr(asyncio, "sleep", noop_sleep)

        req = LLMRequest(user_prompt="test")
        resp = await gemini_provider.complete(req)

        assert resp.content == "Success!"
        assert call_count == 3
        assert resp.usage_prompt_tokens == 5
        assert resp.usage_completion_tokens == 3

    @pytest.mark.asyncio
    async def test_retry_exhausted(self, gemini_provider, monkeypatch):
        """All 3 attempts fail → ConnectionError."""
        from google import genai
        import google.api_core.exceptions

        class MockModels:
            def generate_content(self, *args, **kwargs):
                raise google.api_core.exceptions.ServiceUnavailable("API down")

        class MockClient:
            def __init__(self, *args, **kwargs):
                self.models = MockModels()

        monkeypatch.setattr(genai, "Client", MockClient)
        import asyncio

        async def noop_sleep(_): pass
        monkeypatch.setattr(asyncio, "sleep", noop_sleep)

        req = LLMRequest(user_prompt="test")
        with pytest.raises(ConnectionError, match="Gemini provider failed after 3 attempts"):
            await gemini_provider.complete(req)
