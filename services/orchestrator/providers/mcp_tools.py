"""
TELOS MCP tool provider.

Exposes read-only tools used by the lightweight MCP server so tool metadata and
call behavior live in one place instead of being duplicated in the transport.
"""

from __future__ import annotations

from typing import Any

from services.orchestrator.memory.store import get_memory


class MCPToolProvider:
    """Read-only MCP tools backed by the TELOS memory layer."""

    def __init__(self, memory=None) -> None:
        self.memory = memory or get_memory()

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "get_recent_tasks",
                "description": "Fetch the most recent tasks processed by TELOS.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Max tasks to return (default 10)",
                            "default": 10,
                        }
                    },
                },
            },
            {
                "name": "get_task",
                "description": "Fetch a specific task record by id.",
                "inputSchema": {
                    "type": "object",
                    "required": ["task_id"],
                    "properties": {
                        "task_id": {
                            "type": "string",
                            "description": "Task identifier returned by the orchestrator.",
                        }
                    },
                },
            },
        ]

    def call_tool(self, name: str | None, arguments: dict[str, Any] | None = None) -> Any:
        args = arguments or {}
        if name == "get_recent_tasks":
            limit = int(args.get("limit", 10))
            return self.memory.recent_tasks(limit=limit)

        if name == "get_task":
            task_id = str(args.get("task_id", "")).strip()
            if not task_id:
                return {"error": "task_id is required"}
            return self.memory.get_task(task_id)

        return None
