#!/usr/bin/env python3
"""MEOK AI Labs — expense-tracker-ai-mcp MCP Server. Track expenses, categorize spending, and generate reports."""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any
import uuid
import sys, os

sys.path.insert(0, os.path.expanduser("~/clawd/meok-labs-engine/shared"))
from auth_middleware import check_access
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource, Tool, TextContent
import mcp.types as types

_store = {
    "expenses": [],
    "categories": [
        "Food",
        "Transport",
        "Office",
        "Software",
        "Marketing",
        "Travel",
        "Utilities",
        "Other",
    ],
    "budgets": {},
}
server = Server("expense-tracker-ai-mcp")


def create_id():
    return str(uuid.uuid4())[:8]


@server.list_resources()
async def handle_list_resources():
    return [
        Resource(uri="expenses://all", name="All Expenses", mimeType="application/json")
    ]


@server.list_tools()
async def handle_list_tools():
    return [
        Tool(
            name="add_expense",
            description="Add new expense",
            inputSchema={
                "type": "object",
                "properties": {
                    "amount": {"type": "number"},
                    "category": {"type": "string"},
                    "description": {"type": "string"},
                    "date": {"type": "string"},
                    "vendor": {"type": "string"},
                },
            },
        ),
        Tool(
            name="get_expenses",
            description="Get expenses with filters",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                    "category": {"type": "string"},
                    "limit": {"type": "number"},
                },
            },
        ),
        Tool(
            name="set_budget",
            description="Set monthly budget",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {"type": "string"},
                    "amount": {"type": "number"},
                    "month": {"type": "string"},
                },
            },
        ),
        Tool(
            name="get_budget_status",
            description="Get budget status",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {"type": "string"},
                    "month": {"type": "string"},
                },
            },
        ),
        Tool(
            name="get_category_summary",
            description="Get spending by category",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                },
            },
        ),
        Tool(
            name="get_monthly_summary",
            description="Get monthly summary",
            inputSchema={"type": "object", "properties": {"month": {"type": "string"}}},
        ),
        Tool(
            name="delete_expense",
            description="Delete expense",
            inputSchema={
                "type": "object",
                "properties": {"expense_id": {"type": "string"}},
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: Any = None) -> list[types.TextContent]:
    args = arguments or {}
    api_key = args.get("api_key", "")
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {"error": msg, "upgrade_url": "https://meok.ai/pricing"}
                ),
            )
        ]

    if name == "add_expense":
        expense = {
            "id": create_id(),
            "amount": args["amount"],
            "category": args.get("category", "Other"),
            "description": args.get("description", ""),
            "date": args.get("date", datetime.now().strftime("%Y-%m-%d")),
            "vendor": args.get("vendor", ""),
            "created_at": datetime.now().isoformat(),
        }
        _store["expenses"].append(expense)
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "added": True,
                        "expense_id": expense["id"],
                        "amount": expense["amount"],
                    },
                    indent=2,
                ),
            )
        ]

    elif name == "get_expenses":
        start = args.get("start_date")
        end = args.get("end_date")
        category = args.get("category")
        limit = args.get("limit", 50)

        results = _store["expenses"]
        if start:
            results = [e for e in results if e.get("date", "") >= start]
        if end:
            results = [e for e in results if e.get("date", "") <= end]
        if category:
            results = [e for e in results if e.get("category") == category]

        return [
            TextContent(
                type="text",
                text=json.dumps({"expenses": results[-limit:], "count": len(results)}),
            )
        ]

    elif name == "set_budget":
        category = args.get("category", "Other")
        month = args.get("month", datetime.now().strftime("%Y-%m"))
        budget = {
            "category": category,
            "amount": args["amount"],
            "month": month,
            "set_at": datetime.now().isoformat(),
        }
        _store["budgets"][f"{category}:{month}"] = budget
        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {"set": True, "category": category, "budget": args["amount"]}
                ),
            )
        ]

    elif name == "get_budget_status":
        category = args.get("category", "Other")
        month = args.get("month", datetime.now().strftime("%Y-%m"))

        budget_key = f"{category}:{month}"
        budget = _store["budgets"].get(budget_key, {}).get("amount", 0)

        spent = sum(
            e["amount"]
            for e in _store["expenses"]
            if e.get("category") == category and e.get("date", "").startswith(month)
        )

        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "category": category,
                        "budget": budget,
                        "spent": spent,
                        "remaining": budget - spent,
                        "percent_used": round((spent / budget) * 100, 1)
                        if budget > 0
                        else 0,
                    }
                ),
            )
        ]

    elif name == "get_category_summary":
        start = args.get("start_date")
        end = args.get("end_date")

        expenses = _store["expenses"]
        if start:
            expenses = [e for e in expenses if e.get("date", "") >= start]
        if end:
            expenses = [e for e in expenses if e.get("date", "") <= end]

        by_category = {}
        for e in expenses:
            cat = e.get("category", "Other")
            by_category[cat] = by_category.get(cat, 0) + e.get("amount", 0)

        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {"by_category": by_category, "total": sum(by_category.values())}
                ),
            )
        ]

    elif name == "get_monthly_summary":
        month = args.get("month", datetime.now().strftime("%Y-%m"))

        expenses = [
            e for e in _store["expenses"] if e.get("date", "").startswith(month)
        ]

        total = sum(e.get("amount", 0) for e in expenses)

        return [
            TextContent(
                type="text",
                text=json.dumps(
                    {"month": month, "total": total, "expense_count": len(expenses)}
                ),
            )
        ]

    elif name == "delete_expense":
        exp_id = args.get("expense_id")
        _store["expenses"] = [e for e in _store["expenses"] if e.get("id") != exp_id]
        return [TextContent(type="text", text=json.dumps({"deleted": True}))]

    return [TextContent(type="text", text=json.dumps({"error": "Unknown tool"}))]


async def main():
    async with stdio_server(server._read_stream, server._write_stream) as (
        read_stream,
        write_stream,
    ):
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
