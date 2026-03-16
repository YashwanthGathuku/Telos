"""
TELOS ADK Runner — execute the UI Navigator agent via ADK.

Provides both single-turn execution (for REST API) and streaming
session management (for WebSocket/Live API bidi).
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, AsyncGenerator

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from services.orchestrator.agents.adk_navigator import ui_navigator_agent
from services.orchestrator.config import get_settings

logger = logging.getLogger("telos.adk.runner")

# Singleton session service — survives across requests
_session_service = InMemorySessionService()
_runner: Runner | None = None


def _get_runner() -> Runner:
    """Lazy-init the ADK Runner singleton."""
    global _runner
    if _runner is None:
        _runner = Runner(
            agent=ui_navigator_agent,
            app_name="telos_navigator",
            session_service=_session_service,
        )
    return _runner


async def run_navigator_task(
    user_message: str,
    user_id: str = "default_user",
    session_id: str | None = None,
) -> dict[str, Any]:
    """Execute a single-turn UI navigation task.

    This is the REST API entry point: user sends a text command,
    the agent captures the screen, interprets, acts, and returns results.
    """
    runner = _get_runner()

    # Create or reuse session
    if session_id is None:
        import uuid
        session_id = uuid.uuid4().hex[:12]

    session = await _session_service.get_session(
        app_name="telos_navigator",
        user_id=user_id,
        session_id=session_id,
    )
    if session is None:
        session = await _session_service.create_session(
            app_name="telos_navigator",
            user_id=user_id,
            session_id=session_id,
        )

    # Build the user content
    content = types.Content(
        role="user",
        parts=[types.Part.from_text(text=user_message)],
    )

    # Run the agent — collect all events
    all_text_parts: list[str] = []
    tool_calls: list[dict[str, Any]] = []

    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=content,
    ):
        # Collect text responses
        if event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    all_text_parts.append(part.text)
                if hasattr(part, "function_call") and part.function_call:
                    tool_calls.append({
                        "name": part.function_call.name,
                        "args": dict(part.function_call.args) if part.function_call.args else {},
                    })

    return {
        "session_id": session_id,
        "response": "\n".join(all_text_parts) if all_text_parts else "Agent completed with no text response.",
        "tool_calls": tool_calls,
        "status": "completed",
    }


async def stream_navigator_events(
    user_message: str,
    user_id: str = "default_user",
    session_id: str | None = None,
) -> AsyncGenerator[dict[str, Any], None]:
    """Stream ADK events as they happen — for SSE/WebSocket consumers."""
    runner = _get_runner()

    if session_id is None:
        import uuid
        session_id = uuid.uuid4().hex[:12]

    session = await _session_service.get_session(
        app_name="telos_navigator",
        user_id=user_id,
        session_id=session_id,
    )
    if session is None:
        session = await _session_service.create_session(
            app_name="telos_navigator",
            user_id=user_id,
            session_id=session_id,
        )

    content = types.Content(
        role="user",
        parts=[types.Part.from_text(text=user_message)],
    )

    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=content,
    ):
        event_data: dict[str, Any] = {
            "author": getattr(event, "author", "agent"),
        }

        if event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    event_data["type"] = "text"
                    event_data["text"] = part.text
                    yield event_data
                elif hasattr(part, "function_call") and part.function_call:
                    event_data["type"] = "tool_call"
                    event_data["tool"] = part.function_call.name
                    event_data["args"] = dict(part.function_call.args) if part.function_call.args else {}
                    yield event_data
                elif hasattr(part, "function_response") and part.function_response:
                    event_data["type"] = "tool_response"
                    event_data["tool"] = part.function_response.name
                    yield event_data

    yield {"type": "done", "author": "system"}
