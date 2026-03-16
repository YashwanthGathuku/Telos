"""
TELOS Orchestrator FastAPI application.

Endpoints:
- POST /task
- GET /task/{id}
- GET /tasks
- GET /events
- GET /privacy/summary
- GET /privacy/egress
- GET /system/state
- GET /models
- POST /navigate
- GET /navigate/stream
- GET /health
- GET /ready
- GET /history
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from services.orchestrator.agents.adk_live import router as adk_live_router
from services.orchestrator.bus.a2a import get_bus
from services.orchestrator.config import get_settings
from services.orchestrator.memory.store import get_memory
from services.orchestrator.middleware.auth import auth_dependency
from services.orchestrator.middleware.rate_limit import rate_limit_dependency
from services.orchestrator.models import TaskRequest, TelosEvent
from services.orchestrator.privacy.egress import get_egress_logger
from services.orchestrator.providers.registry import (
    get_provider,
    get_provider_name,
    provider_override,
)
from services.orchestrator.router import TaskRouter

logger = logging.getLogger("telos.app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.telos_log_level.upper(), logging.INFO)
    )
    logger.info(
        "TELOS Orchestrator starting on %s:%d",
        settings.orchestrator_host,
        settings.orchestrator_port,
    )
    logger.info("Provider: %s", settings.telos_provider.value)

    app.state.router = TaskRouter()
    app.state.bus = get_bus()
    app.state.egress = get_egress_logger()
    app.state.memory = get_memory()

    yield

    logger.info("TELOS Orchestrator shutting down")


app = FastAPI(
    title="TELOS Orchestrator",
    version="0.1.0",
    description="Desktop operations orchestrator for task routing and agent coordination.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Telos-Provider",
        "X-Telos-Api-Token",
    ],
)

app.include_router(adk_live_router)


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
    return [task.model_dump() for task in task_router.active_tasks()]


@app.get("/events", dependencies=[Depends(auth_dependency)])
async def event_stream(request: Request):
    """Server-sent events stream for the mission-control dashboard."""
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
                    yield "event: heartbeat\ndata: {}\n\n"
        finally:
            bus.unsubscribe(None, handler)

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/privacy/summary", dependencies=[Depends(auth_dependency)])
async def privacy_summary():
    """Aggregate privacy and egress metrics."""
    egress = app.state.egress
    return egress.summary()


@app.get("/privacy/egress", dependencies=[Depends(auth_dependency)])
async def privacy_egress():
    """Return recent egress records."""
    egress = app.state.egress
    return [record.model_dump() for record in egress.recent()]


@app.get("/system/state", dependencies=[Depends(auth_dependency)])
async def system_state(request: Request):
    """Return the current service and task state for the dashboard."""
    import httpx

    settings = get_settings()
    task_router: TaskRouter = app.state.router
    egress = app.state.egress
    provider_header = request.headers.get("x-telos-provider")
    try:
        active_provider_name = get_provider_name(provider_header)
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"error": str(exc)})

    async def check_service(url: str) -> bool:
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(1.0)) as client:
                response = await client.get(url)
                return response.status_code == 200
        except Exception:
            return False

    with provider_override(provider_header):
        provider = get_provider()
        provider_healthy = False
        try:
            provider_healthy = await provider.health_check()
        except Exception:
            provider_healthy = False

    scheduler_ok, uigraph_ok, screenshot_ok, delta_ok = await asyncio.gather(
        check_service(
            f"http://{settings.scheduler_host}:{settings.scheduler_port}/health"
        ),
        check_service(
            f"http://{settings.windows_mcp_host}:{settings.windows_mcp_port}/health"
        ),
        check_service(
            f"http://{settings.screenshot_engine_host}:{settings.screenshot_engine_port}/health"
        ),
        check_service(
            f"http://{settings.delta_engine_host}:{settings.delta_engine_port}/health"
        ),
    )

    active = task_router.active_tasks()
    total = task_router.all_tasks()
    return {
        "provider": active_provider_name.value,
        "provider_healthy": provider_healthy,
        "privacy_mode": settings.telos_privacy_mode,
        "active_tasks": len(active),
        "total_tasks": len(total),
        "egress": egress.summary(),
        "services": {
            "orchestrator": True,
            "scheduler": scheduler_ok,
            "uigraph": uigraph_ok,
            "capture_engine": screenshot_ok,
            "delta_engine": delta_ok,
        },
    }


@app.get("/models", dependencies=[Depends(auth_dependency)])
async def list_available_models(request: Request):
    """List the configured Gemini model exposed by the orchestrator."""
    settings = get_settings()
    provider_header = request.headers.get("x-telos-provider")
    try:
        active_provider_name = get_provider_name(provider_header)
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"error": str(exc)})

    return [
        {
            "id": settings.gemini_model,
            "name": settings.gemini_model,
            "publisher": active_provider_name.value,
            "rate_tier": "1x",
        }
    ]


@app.post("/navigate", dependencies=[Depends(auth_dependency)])
async def navigate(req: TaskRequest):
    """Execute a UI navigation command via the ADK agent."""
    from services.orchestrator.agents.adk_runner import run_navigator_task

    try:
        return await run_navigator_task(user_message=req.task)
    except Exception as exc:
        logger.exception("Navigator task failed")
        return JSONResponse(status_code=500, content={"error": str(exc)})


@app.get("/navigate/stream", dependencies=[Depends(auth_dependency)])
async def navigate_stream(request: Request, message: str = ""):
    """SSE stream for ADK navigator events."""
    del request
    from services.orchestrator.agents.adk_runner import stream_navigator_events

    if not message:
        return JSONResponse(status_code=400, content={"error": "message query param required"})

    async def generate():
        async for event in stream_navigator_events(user_message=message):
            import json

            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


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

    ready_state = all(
        [
            hasattr(app.state, "router"),
            hasattr(app.state, "bus"),
            hasattr(app.state, "egress"),
            memory_ok,
        ]
    )

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


@app.get("/history", dependencies=[Depends(auth_dependency)])
async def task_history():
    """Recent task history from the local memory store."""
    memory = app.state.memory
    return memory.recent_tasks()
