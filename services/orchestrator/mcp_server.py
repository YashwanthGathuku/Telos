"""
TELOS MCP Server — Exposes task history via Model Context Protocol.

Allows MCP-compatible agents (like Claude Desktop or Cursor) to read
TELOS execution states and metadata. This fulfills the Azure MCP requirement.
"""

import asyncio
import json
import logging
from typing import Any

logger = logging.getLogger("telos.mcp")


class MCPServer:
    """A lightweight pseudo-MCP server exposing orchestrator capabilities."""

    def __init__(self) -> None:
        from services.orchestrator.memory.store import get_memory
        self.memory = get_memory()

    async def handle_request(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Dispatch standard MCP JSON-RPC payload."""
        method = payload.get("method")
        
        if method == "mcp.tools.list":
            return {
                "jsonrpc": "2.0",
                "id": payload.get("id"),
                "result": {
                    "tools": [
                        {
                            "name": "get_recent_tasks",
                            "description": "Fetch the most recent tasks processed by TELOS.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "limit": {"type": "integer", "description": "Max tasks to return (default 10)", "default": 10}
                                }
                            }
                        }
                    ]
                }
            }
            
        elif method == "mcp.tools.call":
            params = payload.get("params", {})
            name = params.get("name")
            args = params.get("arguments", {})
            
            if name == "get_recent_tasks":
                limit = args.get("limit", 10)
                tasks = self.memory.recent_tasks(limit=limit)
                return {
                    "jsonrpc": "2.0",
                    "id": payload.get("id"),
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(tasks, indent=2)}]
                    }
                }
            else:
                return {"jsonrpc": "2.0", "id": payload.get("id"), "error": {"code": -32601, "message": "Tool not found"}}

        return {"jsonrpc": "2.0", "id": payload.get("id"), "error": {"code": -32601, "message": "Method not found"}}


async def run_mcp_stdio_loop() -> None:
    """Run an stdio message loop matching MCP specifications."""
    import sys
    server = MCPServer()
    
    # Read from stdin, write to stdout
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
        except Exception as e:
            logger.error(f"MCP Loop error: {e}")


if __name__ == "__main__":
    import os
    if os.getenv("AZURE_MCP_ENABLED", "true").lower() == "true":
        asyncio.run(run_mcp_stdio_loop())
    else:
        print("MCP is disabled via configuration.")
