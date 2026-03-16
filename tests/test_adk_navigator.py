import httpx
import pytest

from services.orchestrator.agents.adk_navigator import (
    click_element,
    get_ui_tree,
    read_element,
    type_text,
)


@pytest.mark.asyncio
async def test_click_element_includes_app_name(monkeypatch):
    async def mock_post(self_client, url, *, json=None, **kwargs):
        assert str(url).endswith("/uigraph/action")
        assert json == {
            "app_name": "Calculator",
            "action": "click",
            "target": "7",
            "value": "",
        }
        return httpx.Response(
            200,
            json={"success": True},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    result = await click_element("Calculator", element_name="7")

    assert result["success"] is True
    assert result["app_name"] == "Calculator"


@pytest.mark.asyncio
async def test_type_text_uses_write_value(monkeypatch):
    async def mock_post(self_client, url, *, json=None, **kwargs):
        assert json == {
            "app_name": "Notepad",
            "action": "write_value",
            "target": "Text Editor",
            "value": "Hello Gemini",
        }
        return httpx.Response(
            200,
            json={"success": True},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    result = await type_text("Notepad", "Hello Gemini", "Text Editor")

    assert result["success"] is True
    assert result["target"] == "Text Editor"


@pytest.mark.asyncio
async def test_get_ui_tree_uses_snapshot_post(monkeypatch):
    async def mock_post(self_client, url, *, json=None, **kwargs):
        assert str(url).endswith("/uigraph/snapshot")
        assert json == {
            "app_name": "Notepad",
            "detail": "main editor",
        }
        return httpx.Response(
            200,
            json={"snapshot": {"window_title": "Untitled - Notepad", "process_name": "notepad", "process_id": 123, "elements": []}},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    result = await get_ui_tree("Notepad", "main editor")

    assert result["app_name"] == "Notepad"
    assert "snapshot" in result


@pytest.mark.asyncio
async def test_read_element_requires_target():
    result = await read_element("Notepad")

    assert result["error"] == "element_name or automation_id is required"
