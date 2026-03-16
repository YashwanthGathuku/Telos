"""
TELOS ADK live session endpoint.

This WebSocket route streams text responses and tool activity from the
Gemini-powered UI Navigator in real time.
"""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from services.orchestrator.agents.adk_navigator import ui_navigator_agent
from services.orchestrator.config import get_settings

logger = logging.getLogger("telos.adk.live")

router = APIRouter(prefix="/adk", tags=["adk-live"])

_live_session_service = InMemorySessionService()


def _create_live_runner() -> Runner:
    return Runner(
        agent=ui_navigator_agent,
        app_name="telos_live",
        session_service=_live_session_service,
    )


@router.websocket("/live")
async def websocket_live_agent(ws: WebSocket):
    """Text-based WebSocket session for the ADK navigator."""
    await ws.accept()
    logger.info("Live WebSocket connection established")

    runner = _create_live_runner()

    import uuid

    user_id = f"live_{uuid.uuid4().hex[:8]}"
    session_id = uuid.uuid4().hex[:12]

    await _live_session_service.create_session(
        app_name="telos_live",
        user_id=user_id,
        session_id=session_id,
    )

    try:
        await ws.send_json(
            {
                "type": "connected",
                "session_id": session_id,
                "message": "TELOS UI Navigator connected. Send text commands to control the desktop.",
            }
        )

        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await ws.send_json({"type": "error", "message": "Invalid JSON"})
                continue

            msg_type = msg.get("type", "text")

            if msg_type == "text":
                user_text = msg.get("message", "")
                if not user_text:
                    continue

                content = types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=user_text)],
                )

                try:
                    async for event in runner.run_async(
                        user_id=user_id,
                        session_id=session_id,
                        new_message=content,
                    ):
                        if event.content and event.content.parts:
                            for part in event.content.parts:
                                if hasattr(part, "text") and part.text:
                                    await ws.send_json(
                                        {
                                            "type": "text",
                                            "text": part.text,
                                            "author": getattr(event, "author", "agent"),
                                        }
                                    )
                                elif hasattr(part, "function_call") and part.function_call:
                                    await ws.send_json(
                                        {
                                            "type": "tool_call",
                                            "tool": part.function_call.name,
                                            "args": dict(part.function_call.args) if part.function_call.args else {},
                                        }
                                    )
                                elif hasattr(part, "function_response") and part.function_response:
                                    await ws.send_json(
                                        {
                                            "type": "tool_response",
                                            "tool": part.function_response.name,
                                        }
                                    )

                    await ws.send_json({"type": "turn_complete"})

                except Exception as exc:
                    logger.exception("Error during agent execution")
                    await ws.send_json({"type": "error", "message": f"Agent error: {exc}"})

            elif msg_type == "audio":
                await ws.send_json(
                    {
                        "type": "error",
                        "message": "Audio input is not enabled in this build.",
                    }
                )

            elif msg_type == "ping":
                await ws.send_json({"type": "pong"})

            else:
                await ws.send_json(
                    {
                        "type": "error",
                        "message": f"Unsupported message type: {msg_type}",
                    }
                )

    except WebSocketDisconnect:
        logger.info("Live WebSocket disconnected: session=%s", session_id)
    except Exception as exc:
        logger.exception("Live WebSocket error")
        try:
            await ws.send_json({"type": "error", "message": str(exc)})
        except Exception:
            pass


@router.get("/health")
async def adk_health():
    return {
        "status": "ok",
        "service": "adk-live",
        "agent": "telos_ui_navigator",
        "model": get_settings().gemini_model,
        "input_mode": "text",
    }
