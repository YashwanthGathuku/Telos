"""
TELOS Orchestrator — FastAPI application.

MCP port 8080. Provides:
- POST /task — submit a new task
- GET  /task/{id} — get task status
- GET  /tasks — list all tasks
- GET  /events — SSE event stream for the frontend
- GET  /privacy/summary — egress summary
- GET  /privacy/egress — recent egress records
- GET  /health — service health check
- GET  /system/state — current system state for dashboard
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

from services.orchestrator.models import (
    TaskRequest, TelosEvent, EventType,
)
from services.orchestrator.config import get_settings
from services.orchestrator.router import TaskRouter
from services.orchestrator.bus.a2a import get_bus
from services.orchestrator.privacy.egress import get_egress_logger
from services.orchestrator.providers.registry import get_provider
from services.orchestrator.providers.registry import get_provider_name, provider_override
from services.orchestrator.memory.store import get_memory
from services.orchestrator.middleware.auth import auth_dependency
from services.orchestrator.middleware.rate_limit import rate_limit_dependency

logger = logging.getLogger("telos.app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    s = get_settings()
    logging.basicConfig(level=getattr(logging, s.telos_log_level.upper(), logging.INFO))
    logger.info("TELOS Orchestrator starting on %s:%d", s.orchestrator_host, s.orchestrator_port)
    logger.info("Provider: %s", s.telos_provider.value)

    app.state.router = TaskRouter()
    app.state.bus = get_bus()
    app.state.egress = get_egress_logger()
    app.state.memory = get_memory()

    yield

    logger.info("TELOS Orchestrator shutting down")


app = FastAPI(
    title="TELOS Orchestrator",
    version="0.1.0",
    description="Desktop operations orchestrator — task routing, agent coordination, privacy enforcement.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:1420", "http://127.0.0.1:1420", "tauri://localhost"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Task Endpoints ───────────────────────────────────────────────────────

@app.post("/task", dependencies=[Depends(auth_dependency), Depends(rate_limit_dependency)])
async def submit_task(req: TaskRequest, request: Request):
    """Submit a natural-language task for execution."""
    task_router: TaskRouter = app.state.router
    provider_name = request.headers.get("x-telos-provider")
    try:
        with provider_override(provider_name):
            record = await task_router.submit(req.task)
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"error": str(exc)})
    return {
        "task_id": record.id,
        "status": record.status.value,
        "task": record.task,
    }


@app.get("/task/{task_id}", dependencies=[Depends(auth_dependency)])
async def get_task(task_id: str):
    """Get the status and details of a specific task."""
    task_router: TaskRouter = app.state.router
    record = task_router.get_task(task_id)
    if record is None:
        return JSONResponse(status_code=404, content={"error": "Task not found"})
    return record.model_dump()


@app.get("/tasks", dependencies=[Depends(auth_dependency)])
async def list_tasks():
    """List all active tasks."""
    task_router: TaskRouter = app.state.router
    return [t.model_dump() for t in task_router.active_tasks()]


# ── SSE Event Stream ─────────────────────────────────────────────────────

@app.get("/events", dependencies=[Depends(auth_dependency)])
async def event_stream(request: Request):
    """Server-Sent Events stream for the mission-control dashboard."""
    bus = app.state.bus
    queue: asyncio.Queue[TelosEvent] = asyncio.Queue()

    async def handler(event: TelosEvent) -> None:
        await queue.put(event)

    bus.subscribe(None, handler)

    async def generate():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                    data = event.model_dump_json()
                    yield f"event: {event.event_type.value}\ndata: {data}\n\n"
                except asyncio.TimeoutError:
                    yield f"event: heartbeat\ndata: {{}}\n\n"
        finally:
            bus.unsubscribe(None, handler)

    return StreamingResponse(generate(), media_type="text/event-stream")


# ── Privacy Endpoints ────────────────────────────────────────────────────

@app.get("/privacy/summary", dependencies=[Depends(auth_dependency)])
async def privacy_summary():
    """Aggregate privacy / egress metrics."""
    egress = app.state.egress
    return egress.summary()


@app.get("/privacy/egress", dependencies=[Depends(auth_dependency)])
async def privacy_egress():
    """Recent egress records."""
    egress = app.state.egress
    return [r.model_dump() for r in egress.recent()]


# ── System State ─────────────────────────────────────────────────────────

@app.get("/system/state", dependencies=[Depends(auth_dependency)])
async def system_state(request: Request):
    """Current system snapshot for the dashboard."""
    import httpx

    s = get_settings()
    task_router: TaskRouter = app.state.router
    egress = app.state.egress
    provider_header = request.headers.get("x-telos-provider")
    try:
        active_provider_name = get_provider_name(provider_header)
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"error": str(exc)})

    async def check_service(url: str) -> bool:
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(1.0)) as hc:
                r = await hc.get(url)
                return r.status_code == 200
        except Exception:
            return False

    with provider_override(provider_header):
        provider = get_provider()
        provider_healthy = False
        try:
            provider_healthy = await provider.health_check()
        except Exception:
            pass

    scheduler_ok, uigraph_ok, capture_ok = await asyncio.gather(
        check_service(f"http://{s.scheduler_host}:{s.scheduler_port}/health"),
        check_service(f"http://{s.windows_mcp_host}:{s.windows_mcp_port}/health"),
        check_service(f"http://{s.capture_engine_host}:{s.capture_engine_port}/health"),
    )

    active = task_router.active_tasks()
    total = task_router.all_tasks()
    return {
        "provider": active_provider_name.value,
        "provider_healthy": provider_healthy,
        "privacy_mode": s.telos_privacy_mode,
        "active_tasks": len(active),
        "total_tasks": len(total),
        "egress": egress.summary(),
        "services": {
            "orchestrator": True,
            "scheduler": scheduler_ok,
            "uigraph": uigraph_ok,
            "capture_engine": capture_ok,
        },
    }


# ── Health ───────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "service": "orchestrator"}


@app.get("/ready")
async def ready():
    memory = app.state.memory
    provider = get_provider()

    memory_ok = True
    try:
        memory.recent_tasks(1)
    except Exception:
        memory_ok = False

    provider_healthy = False
    try:
        provider_healthy = await provider.health_check()
    except Exception:
        provider_healthy = False

    ready_state = all([
        hasattr(app.state, "router"),
        hasattr(app.state, "bus"),
        hasattr(app.state, "egress"),
        memory_ok,
    ])

    status_code = 200 if ready_state else 503
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if ready_state else "degraded",
            "service": "orchestrator",
            "memory_ok": memory_ok,
            "provider_healthy": provider_healthy,
        },
    )


# ── Task History ─────────────────────────────────────────────────────────

@app.get("/history", dependencies=[Depends(auth_dependency)])
async def task_history():
    """Recent task history from the local memory store."""
    memory = app.state.memory
    return memory.recent_tasks()
