"""
TELOS Tests — FastAPI application endpoint tests.

Uses the ASGI lifespan protocol to ensure app.state is properly
initialized before exercising endpoints.
"""

import os
import pytest
from contextlib import asynccontextmanager
from httpx import AsyncClient, ASGITransport

from services.orchestrator.app import app
from services.orchestrator.config import get_settings


@asynccontextmanager
async def lifespan_client():
    """Create an AsyncClient that triggers the FastAPI lifespan."""
    transport = ASGITransport(app=app)
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
    os.environ.pop("TELOS_API_TOKEN", None)
    os.environ.pop("TELOS_INTERNAL_TOKEN", None)


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_tasks_endpoint():
    async with lifespan_client() as client:
        resp = await client.get("/tasks")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_task_not_found():
    async with lifespan_client() as client:
        resp = await client.get("/task/nonexistent")
        assert resp.status_code == 404


@pytest.mark.asyncio
async def test_privacy_summary():
    async with lifespan_client() as client:
        resp = await client.get("/privacy/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_calls" in data


@pytest.mark.asyncio
async def test_privacy_egress():
    async with lifespan_client() as client:
        resp = await client.get("/privacy/egress")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_history_endpoint():
    async with lifespan_client() as client:
        resp = await client.get("/history")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_system_state():
    async with lifespan_client() as client:
        resp = await client.get("/system/state")
        assert resp.status_code == 200
        data = resp.json()
        assert "provider" in data
        assert "services" in data


@pytest.mark.asyncio
async def test_submit_task_validation():
    async with lifespan_client() as client:
        resp = await client.post("/task", json={"task": ""})
        assert resp.status_code == 422


@pytest.mark.asyncio
async def test_system_state_provider_override():
    async with lifespan_client() as client:
        resp = await client.get("/system/state", headers={"X-Telos-Provider": "gemini"})
        assert resp.status_code == 200
        assert resp.json()["provider"] == "gemini"


@pytest.mark.asyncio
async def test_protected_routes_require_token(monkeypatch):
    monkeypatch.setenv("TELOS_API_TOKEN", "secret-token")
    get_settings.cache_clear()

    async with lifespan_client() as client:
        resp = await client.get("/tasks")
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_protected_routes_accept_bearer_token(monkeypatch):
    monkeypatch.setenv("TELOS_API_TOKEN", "secret-token")
    get_settings.cache_clear()

    async with lifespan_client() as client:
        resp = await client.get("/tasks", headers={"Authorization": "Bearer secret-token"})
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_query_token_is_accepted(monkeypatch):
    monkeypatch.setenv("TELOS_API_TOKEN", "secret-token")
    get_settings.cache_clear()

    async with lifespan_client() as client:
        resp = await client.get("/system/state?access_token=secret-token")
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_ready_endpoint():
    async with lifespan_client() as client:
        resp = await client.get("/ready")
        assert resp.status_code == 200
        data = resp.json()
        assert data["service"] == "orchestrator"
        assert data["memory_ok"] is True
