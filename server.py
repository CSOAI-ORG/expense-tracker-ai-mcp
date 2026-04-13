#!/usr/bin/env python3
"""MEOK AI Labs — expense-tracker-ai-mcp MCP Server. Track expenses, categorize spending, and generate reports."""

import asyncio
import json
from datetime import datetime
from typing import Any

from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
)
import mcp.types as types

# In-memory store (replace with DB in production)
_store = {}

server = Server("expense-tracker-ai-mcp")

@server.list_resources()
async def handle_list_resources() -> list[Resource]:
    return []

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return [
        Tool(name="add_expense", description="Add an expense", inputSchema={"type":"object","properties":{"amount":{"type":"number"},"category":{"type":"string"}},"required":["amount","category"]}),
        Tool(name="get_summary", description="Get expense summary", inputSchema={"type":"object","properties":{}}),
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Any | None) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    args = arguments or {}
    if name == "add_expense":
        _store.setdefault("expenses", []).append({"amount": args["amount"], "category": args["category"], "date": datetime.now().isoformat()})
        return [TextContent(type="text", text=json.dumps({"status": "added"}, indent=2))]
    if name == "get_summary":
        total = sum(e["amount"] for e in _store.get("expenses", []))
        return [TextContent(type="text", text=json.dumps({"total": total, "count": len(_store.get("expenses", []))}, indent=2))]
    return [TextContent(type="text", text=json.dumps({"error": "Unknown tool"}, indent=2))]

async def main():
    async with stdio_server(server._read_stream, server._write_stream) as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="expense-tracker-ai-mcp",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
