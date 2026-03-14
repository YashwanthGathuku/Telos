"""
TELOS Tests — MCP tool provider and transport tests.
"""

import pytest

from services.orchestrator.mcp_server import MCPServer
from services.orchestrator.providers.mcp_tools import MCPToolProvider


class FakeMemory:
    def __init__(self):
        self._tasks = {
            "t1": {"task_id": "t1", "task": "Test task", "status": "completed"},
        }

    def recent_tasks(self, limit: int = 10):
        return list(self._tasks.values())[:limit]

    def get_task(self, task_id: str):
        return self._tasks.get(task_id)


def test_mcp_tools_list():
    tools = MCPToolProvider(FakeMemory()).list_tools()
    names = {tool["name"] for tool in tools}
    assert "get_recent_tasks" in names
    assert "get_task" in names


def test_mcp_tool_get_task():
    provider = MCPToolProvider(FakeMemory())
    task = provider.call_tool("get_task", {"task_id": "t1"})
    assert task["status"] == "completed"


@pytest.mark.asyncio
async def test_mcp_server_tools_call(monkeypatch):
    fake_memory = FakeMemory()
    monkeypatch.setattr("services.orchestrator.providers.mcp_tools.get_memory", lambda: fake_memory)
    server = MCPServer()

    response = await server.handle_request({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "mcp.tools.call",
        "params": {"name": "get_recent_tasks", "arguments": {"limit": 1}},
    })

    assert response["result"]["content"]
