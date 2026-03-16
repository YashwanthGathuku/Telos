"""
TELOS MCP server for exposing orchestrator tools over JSON-RPC.
"""

import asyncio
import json
import logging
from typing import Any

from services.orchestrator.providers.mcp_tools import MCPToolProvider

logger = logging.getLogger("telos.mcp")


class MCPServer:
    """A lightweight pseudo-MCP server exposing orchestrator capabilities."""

    def __init__(self) -> None:
        self.tools = MCPToolProvider()

    async def handle_request(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Dispatch standard MCP JSON-RPC payloads."""
        method = payload.get("method")

        if method == "mcp.tools.list":
            return {
                "jsonrpc": "2.0",
                "id": payload.get("id"),
                "result": {"tools": self.tools.list_tools()},
            }

        if method == "mcp.tools.call":
            params = payload.get("params", {})
            name = params.get("name")
            args = params.get("arguments", {})
            tool_result = self.tools.call_tool(name, args)
            if tool_result is None:
                return {
                    "jsonrpc": "2.0",
                    "id": payload.get("id"),
                    "error": {"code": -32601, "message": "Tool not found"},
                }

            return {
                "jsonrpc": "2.0",
                "id": payload.get("id"),
                "result": {
                    "content": [{"type": "text", "text": json.dumps(tool_result, indent=2)}]
                },
            }

        return {
            "jsonrpc": "2.0",
            "id": payload.get("id"),
            "error": {"code": -32601, "message": "Method not found"},
        }


async def run_mcp_stdio_loop() -> None:
    """Run a stdio message loop matching MCP expectations."""
    import sys

    server = MCPServer()
    loop = asyncio.get_running_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)

    while True:
        try:
            line = await reader.readline()
            if not line:
                break

            payload = json.loads(line)
            response = await server.handle_request(payload)
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
        except Exception as exc:
            logger.error("MCP loop error: %s", exc)


if __name__ == "__main__":
    import os

    if os.getenv("TELOS_MCP_ENABLED", "true").lower() == "true":
        asyncio.run(run_mcp_stdio_loop())
    else:
        print("MCP is disabled via configuration.")
