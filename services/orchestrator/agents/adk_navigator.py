"""
TELOS ADK UI Navigator agent.

Defines the Gemini-powered ADK agent used for the UI Navigator submission path.
The tools bridge from ADK into the local Windows UIGraph and screenshot services.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
from google.adk import Agent

from services.orchestrator.config import get_settings

logger = logging.getLogger("telos.adk.navigator")

_settings = get_settings()
_UIGRAPH_BASE = f"http://{_settings.windows_mcp_host}:{_settings.windows_mcp_port}"
_CAPTURE_BASE = f"http://{_settings.screenshot_engine_host}:{_settings.screenshot_engine_port}"
_TIMEOUT = httpx.Timeout(connect=3.0, read=15.0, write=3.0, pool=3.0)


async def _uigraph_action(app_name: str, action: str, target: str, value: str = "") -> dict[str, Any]:
    payload = {
        "app_name": app_name,
        "action": action,
        "target": target,
        "value": value,
    }
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(f"{_UIGRAPH_BASE}/uigraph/action", json=payload)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict):
            data.setdefault("app_name", app_name)
            data.setdefault("target", target)
        return data


async def _uigraph_snapshot(app_name: str, detail: str = "") -> dict[str, Any]:
    payload = {
        "app_name": app_name,
        "detail": detail,
    }
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        resp = await client.post(f"{_UIGRAPH_BASE}/uigraph/snapshot", json=payload)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict):
            data.setdefault("app_name", app_name)
        return data


async def capture_screen() -> dict[str, Any]:
    """Capture the current screen and return a base64 PNG payload."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(f"{_CAPTURE_BASE}/capture/screen")
            resp.raise_for_status()
            data = resp.json()
            image_b64 = data.get("image", "")
            if not image_b64:
                return {"error": "Screenshot engine returned empty image"}
            return {
                "image_base64": image_b64,
                "format": "png",
                "description": "Screenshot captured successfully. Analyze the image to understand the current screen state.",
            }
    except Exception as exc:
        return {"error": f"Failed to capture screen: {exc}"}


async def click_element(app_name: str, element_name: str = "", automation_id: str = "") -> dict[str, Any]:
    """Click a UI element inside a specific application window."""
    target = automation_id or element_name
    if not app_name:
        return {"error": "app_name is required"}
    if not target:
        return {"error": "element_name or automation_id is required"}
    try:
        return await _uigraph_action(app_name, "click", target)
    except Exception as exc:
        return {"error": f"Click failed: {exc}"}


async def type_text(app_name: str, text: str, element_name: str) -> dict[str, Any]:
    """Write text into a named UI element inside an application window."""
    if not app_name:
        return {"error": "app_name is required"}
    if not element_name:
        return {"error": "element_name is required"}
    if not text:
        return {"error": "text is required"}
    try:
        return await _uigraph_action(app_name, "write_value", element_name, text)
    except Exception as exc:
        return {"error": f"Type text failed: {exc}"}


async def launch_app(app_name: str, hint_exe: str = "") -> dict[str, Any]:
    """Launch a Windows application by name, optionally with an executable hint."""
    if not app_name:
        return {"error": "app_name is required"}
    payload: dict[str, Any] = {"app_name": app_name}
    if hint_exe:
        payload["hint_exe"] = hint_exe
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(f"{_UIGRAPH_BASE}/uigraph/launch", json=payload)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, dict):
                data.setdefault("app_name", app_name)
            return data
    except Exception as exc:
        return {"error": f"Launch app failed: {exc}"}


async def read_element(app_name: str, element_name: str = "", automation_id: str = "") -> dict[str, Any]:
    """Read text from a named or automation-id-based element inside an application window."""
    target = automation_id or element_name
    if not app_name:
        return {"error": "app_name is required"}
    if not target:
        return {"error": "element_name or automation_id is required"}
    try:
        return await _uigraph_action(app_name, "read_text", target)
    except Exception as exc:
        return {"error": f"Read element failed: {exc}"}


async def list_windows() -> dict[str, Any]:
    """List the currently visible windows and process names on the desktop."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(f"{_UIGRAPH_BASE}/uigraph/windows")
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        return {"error": f"List windows failed: {exc}"}


async def get_ui_tree(app_name: str, detail: str = "") -> dict[str, Any]:
    """Return the accessible UI tree for a specific application window."""
    if not app_name:
        return {"error": "app_name is required"}
    try:
        return await _uigraph_snapshot(app_name, detail)
    except Exception as exc:
        return {"error": f"Get UI tree failed: {exc}"}


async def invoke_button(app_name: str, element_name: str = "", automation_id: str = "") -> dict[str, Any]:
    """Invoke a button element inside a specific application window."""
    target = automation_id or element_name
    if not app_name:
        return {"error": "app_name is required"}
    if not target:
        return {"error": "element_name or automation_id is required"}
    try:
        return await _uigraph_action(app_name, "invoke_button", target)
    except Exception as exc:
        return {"error": f"Invoke button failed: {exc}"}


async def expand_element(app_name: str, element_name: str) -> dict[str, Any]:
    """Expand or collapse a named UI element inside an application window."""
    if not app_name:
        return {"error": "app_name is required"}
    if not element_name:
        return {"error": "element_name is required"}
    try:
        return await _uigraph_action(app_name, "expand", element_name)
    except Exception as exc:
        return {"error": f"Expand failed: {exc}"}


async def select_item(app_name: str, item_name: str) -> dict[str, Any]:
    """Select a named item inside a list, combo box, or tree in an application window."""
    if not app_name:
        return {"error": "app_name is required"}
    if not item_name:
        return {"error": "item_name is required"}
    try:
        return await _uigraph_action(app_name, "select_item", item_name)
    except Exception as exc:
        return {"error": f"Select item failed: {exc}"}


NAVIGATOR_INSTRUCTION = """You are TELOS, a Windows UI Navigator agent built for the Gemini Live Agent Challenge.

WORKFLOW:
1. Always call capture_screen first to see the current desktop state.
2. Analyze the screenshot before acting. Never guess.
3. Use list_windows or get_ui_tree when you need to identify the target window or UI element names.
4. Use launch_app to open applications that are not already visible.
5. Use the UIGraph tools to act inside the correct app window.
6. Call capture_screen again after each meaningful action to verify the result.
7. Summarize what you changed and what is now visible on screen.

RULES:
- Every UIGraph tool except capture_screen, list_windows, and launch_app requires app_name.
- If click_element or read_element fails by name, retry with automation_id from get_ui_tree.
- Be explicit about the target app you are working inside.
- Never perform destructive actions without explicit confirmation.
"""


ui_navigator_agent = Agent(
    model=_settings.gemini_model,
    name="telos_ui_navigator",
    description="Gemini-powered Windows UI navigator that observes the screen, uses UI Automation tools, and verifies each action.",
    instruction=NAVIGATOR_INSTRUCTION,
    tools=[
        capture_screen,
        click_element,
        type_text,
        launch_app,
        read_element,
        list_windows,
        get_ui_tree,
        invoke_button,
        expand_element,
        select_item,
    ],
)
