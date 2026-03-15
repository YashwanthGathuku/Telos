"""
TELOS Tests — VisionAgent tests.

Verifies the VisionAgent can capture screenshots from the Go screenshot engine
and send them successfully to the multimodal Gemini endpoint.
"""

import base64
import asyncio
import pytest
from services.orchestrator.agents.vision import VisionAgent
from services.orchestrator.models import AgentRole, LLMRequest


@pytest.fixture
def vision_agent(monkeypatch):
    monkeypatch.setenv("SCREENSHOT_ENGINE_HOST", "127.0.0.1")
    monkeypatch.setenv("SCREENSHOT_ENGINE_PORT", "8085")
    monkeypatch.setenv("TELOS_PRIVACY_MODE", "balanced")
    from services.orchestrator.config import get_settings
    get_settings.cache_clear()
    return VisionAgent()


def test_vision_role(vision_agent):
    assert vision_agent.role() == AgentRole.VISION


@pytest.mark.asyncio
async def test_vision_execute_success(vision_agent, monkeypatch):
    import httpx
    
    # 1. Mock Go screenshot engine
    fake_png = base64.b64encode(b"fake_png_data").decode()
    
    async def mock_post(self_client, url, **kwargs):
        if "capture/screen" in str(url):
            return httpx.Response(
                200, 
                json={"image": fake_png},
                request=httpx.Request("POST", url)
            )
        raise ValueError("Unexpected URL")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)
    
    # 2. Mock LLM Provider
    class MockProvider:
        def provider_name(self):
            return "gemini"

        async def complete(self, request: LLMRequest):
            assert request.image_data == b"fake_png_data"
            assert request.image_mime == "image/png"
            assert "Find the login button" in request.user_prompt
            
            class MockResponse:
                content = "The login button is at (100, 200)"
                bytes_received = 35
            return MockResponse()

    vision_agent._provider = MockProvider()
    
    # 3. Execute
    result = await vision_agent.execute({"detail": "Find the login button"})
    
    assert "error" not in result
    assert result["value"] == "The login button is at (100, 200)"
    assert result["bytes_received"] == 35


@pytest.mark.asyncio
async def test_vision_capture_failure(vision_agent, monkeypatch):
    import httpx
    
    async def mock_post_fail(self_client, url, **kwargs):
        raise httpx.ConnectError("Connection refused")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post_fail)
    
    result = await vision_agent.execute({"detail": "Find the login button"})
    assert "error" in result
    assert "failed to capture screen" in result["error"]


def test_vision_blocked_in_strict_mode(monkeypatch):
    monkeypatch.setenv("SCREENSHOT_ENGINE_HOST", "127.0.0.1")
    monkeypatch.setenv("SCREENSHOT_ENGINE_PORT", "8085")
    monkeypatch.setenv("TELOS_PRIVACY_MODE", "strict")
    monkeypatch.delenv("TELOS_ALLOW_IMAGE_EGRESS", raising=False)
    from services.orchestrator.config import get_settings
    get_settings.cache_clear()

    agent = VisionAgent()
    result = asyncio.run(agent.execute({"detail": "Read the screen"}))
    assert "error" in result
    assert "blocked by privacy mode" in result["error"]
