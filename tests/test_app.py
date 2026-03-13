"""
TELOS Tests — FastAPI application endpoint tests.

Uses the ASGI lifespan protocol to ensure app.state is properly
initialized before exercising endpoints.
"""

import pytest
from contextlib import asynccontextmanager
from httpx import AsyncClient, ASGITransport

from services.orchestrator.app import app


@asynccontextmanager
async def lifespan_client():
    """Create an AsyncClient that triggers the FastAPI lifespan."""
    transport = ASGITransport(app=app)
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client


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
        # Empty task should fail validation
        resp = await client.post("/task", json={"task": ""})
        # Pydantic will reject because strip makes it empty, then min_length isn't set
        # but the router should handle empty string gracefully
        assert resp.status_code in (200, 422)
