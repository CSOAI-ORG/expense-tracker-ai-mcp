#!/usr/bin/env python3
"""MEOK AI Labs — expense-tracker-ai-mcp MCP Server. Track expenses, categorize spending, and generate reports."""

import json
from datetime import datetime, timedelta, timezone
from typing import Any
import uuid
import sys, os

sys.path.insert(0, os.path.expanduser("~/clawd/meok-labs-engine/shared"))
from auth_middleware import check_access
from mcp.server.fastmcp import FastMCP
from collections import defaultdict

FREE_DAILY_LIMIT = 15
_usage = defaultdict(list)
def _rl(c="anon"):
    now = datetime.now(timezone.utc)
    _usage[c] = [t for t in _usage[c] if (now-t).total_seconds() < 86400]
    if len(_usage[c]) >= FREE_DAILY_LIMIT: return json.dumps({"error": f"Limit {FREE_DAILY_LIMIT}/day"})
    _usage[c].append(now); return None


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
mcp = FastMCP("expense-tracker-ai", instructions="Track expenses, categorize spending, and generate reports.")


def create_id():
    return str(uuid.uuid4())[:8]


@mcp.tool()
def add_expense(amount: float, category: str = "Other", description: str = "", date: str = "", vendor: str = "", api_key: str = "") -> str:
    """Add new expense"""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    expense = {
        "id": create_id(),
        "amount": amount,
        "category": category,
        "description": description,
        "date": date or datetime.now().strftime("%Y-%m-%d"),
        "vendor": vendor,
        "created_at": datetime.now().isoformat(),
    }
    _store["expenses"].append(expense)
    return json.dumps(
        {"added": True, "expense_id": expense["id"], "amount": expense["amount"]},
        indent=2,
    )


@mcp.tool()
def get_expenses(start_date: str = "", end_date: str = "", category: str = "", limit: int = 50, api_key: str = "") -> str:
    """Get expenses with filters"""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    results = _store["expenses"]
    if start_date:
        results = [e for e in results if e.get("date", "") >= start_date]
    if end_date:
        results = [e for e in results if e.get("date", "") <= end_date]
    if category:
        results = [e for e in results if e.get("category") == category]

    return json.dumps({"expenses": results[-limit:], "count": len(results)})


@mcp.tool()
def set_budget(amount: float, category: str = "Other", month: str = "", api_key: str = "") -> str:
    """Set monthly budget"""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    if not month:
        month = datetime.now().strftime("%Y-%m")
    budget = {
        "category": category,
        "amount": amount,
        "month": month,
        "set_at": datetime.now().isoformat(),
    }
    _store["budgets"][f"{category}:{month}"] = budget
    return json.dumps({"set": True, "category": category, "budget": amount})


@mcp.tool()
def get_budget_status(category: str = "Other", month: str = "", api_key: str = "") -> str:
    """Get budget status"""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    if not month:
        month = datetime.now().strftime("%Y-%m")

    budget_key = f"{category}:{month}"
    budget = _store["budgets"].get(budget_key, {}).get("amount", 0)

    spent = sum(
        e["amount"]
        for e in _store["expenses"]
        if e.get("category") == category and e.get("date", "").startswith(month)
    )

    return json.dumps({
        "category": category,
        "budget": budget,
        "spent": spent,
        "remaining": budget - spent,
        "percent_used": round((spent / budget) * 100, 1) if budget > 0 else 0,
    })


@mcp.tool()
def get_category_summary(start_date: str = "", end_date: str = "", api_key: str = "") -> str:
    """Get spending by category"""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    expenses = _store["expenses"]
    if start_date:
        expenses = [e for e in expenses if e.get("date", "") >= start_date]
    if end_date:
        expenses = [e for e in expenses if e.get("date", "") <= end_date]

    by_category = {}
    for e in expenses:
        cat = e.get("category", "Other")
        by_category[cat] = by_category.get(cat, 0) + e.get("amount", 0)

    return json.dumps({"by_category": by_category, "total": sum(by_category.values())})


@mcp.tool()
def get_monthly_summary(month: str = "", api_key: str = "") -> str:
    """Get monthly summary"""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    if not month:
        month = datetime.now().strftime("%Y-%m")

    expenses = [
        e for e in _store["expenses"] if e.get("date", "").startswith(month)
    ]

    total = sum(e.get("amount", 0) for e in expenses)

    return json.dumps({"month": month, "total": total, "expense_count": len(expenses)})


@mcp.tool()
def delete_expense(expense_id: str, api_key: str = "") -> str:
    """Delete expense"""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    _store["expenses"] = [e for e in _store["expenses"] if e.get("id") != expense_id]
    return json.dumps({"deleted": True})


if __name__ == "__main__":
    mcp.run()
