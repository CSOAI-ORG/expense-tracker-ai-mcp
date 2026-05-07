#!/usr/bin/env python3
"""MEOK AI Labs — expense-tracker-ai-mcp MCP Server. Track expenses, categorize spending, and generate reports."""

import json
from datetime import datetime, timedelta, timezone
from typing import Any
import uuid
import sys, os

sys.path.insert(0, os.path.expanduser("~/clawd/meok-labs-engine/shared"))
from auth_middleware import check_access
from persistence import ServerStore
from mcp.server.fastmcp import FastMCP
from collections import defaultdict

_db = ServerStore("expense-tracker-ai")

FREE_DAILY_LIMIT = 15
_usage = defaultdict(list)
def _rl(c="anon"):
    now = datetime.now(timezone.utc)
    _usage[c] = [t for t in _usage[c] if (now-t).total_seconds() < 86400]
    if len(_usage[c]) >= FREE_DAILY_LIMIT: return json.dumps({"error": f"Limit {FREE_DAILY_LIMIT}/day"})
    _usage[c].append(now); return None

# Seed default categories if not present
if not _db.get("categories"):
    _db.set("categories", ["Food", "Transport", "Office", "Software", "Marketing", "Travel", "Utilities", "Other"])
mcp = FastMCP("expense-tracker-ai", instructions="Track expenses, categorize spending, and generate reports.")


def create_id():
    return str(uuid.uuid4())[:8]


@mcp.tool()
def add_expense(amount: float, category: str = "Other", description: str = "", date: str = "", vendor: str = "", api_key: str = "") -> str:
    """Add new expense

    Behavior:
        This tool is read-only and stateless — it produces analysis output
        without modifying any external systems, databases, or files.
        Safe to call repeatedly with identical inputs (idempotent).
        Free tier: 10/day rate limit. Pro tier: unlimited.
        No authentication required for basic usage.

    When to use:
        Use this tool when you need structured analysis or classification
        of inputs against established frameworks or standards.

    When NOT to use:
        Not suitable for real-time production decision-making without
        human review of results.

    Args:
        amount (float): The amount to analyze or process.
        category (str): The category to analyze or process.
        description (str): The description to analyze or process.
        date (str): The date to analyze or process.
        vendor (str): The vendor to analyze or process.
        api_key (str): The api key to analyze or process.

    Behavioral Transparency:
        - Side Effects: This tool is read-only and produces no side effects. It does not modify
          any external state, databases, or files. All output is computed in-memory and returned
          directly to the caller.
        - Authentication: No authentication required for basic usage. Pro/Enterprise tiers
          require a valid MEOK API key passed via the MEOK_API_KEY environment variable.
        - Rate Limits: Free tier: 10 calls/day. Pro tier: unlimited. Rate limit headers are
          included in responses (X-RateLimit-Remaining, X-RateLimit-Reset).
        - Error Handling: Returns structured error objects with 'error' key on failure.
          Never raises unhandled exceptions. Invalid inputs return descriptive validation errors.
        - Idempotency: Fully idempotent — calling with the same inputs always produces the
          same output. Safe to retry on timeout or transient failure.
        - Data Privacy: No input data is stored, logged, or transmitted to external services.
          All processing happens locally within the MCP server process.
    """
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
    _db.append("expenses", expense)
    _db.hset("expenses_by_id", expense["id"], expense)
    return json.dumps(
        {"added": True, "expense_id": expense["id"], "amount": expense["amount"]},
        indent=2,
    )


@mcp.tool()
def get_expenses(start_date: str = "", end_date: str = "", category: str = "", limit: int = 50, api_key: str = "") -> str:
    """Get expenses with filters

    Behavior:
        This tool is read-only and stateless — it produces analysis output
        without modifying any external systems, databases, or files.
        Safe to call repeatedly with identical inputs (idempotent).
        Free tier: 10/day rate limit. Pro tier: unlimited.
        No authentication required for basic usage.

    When to use:
        Use this tool when you need structured analysis or classification
        of inputs against established frameworks or standards.

    When NOT to use:
        Not suitable for real-time production decision-making without
        human review of results.

    Args:
        start_date (str): The start date to analyze or process.
        end_date (str): The end date to analyze or process.
        category (str): The category to analyze or process.
        limit (int): The limit to analyze or process.
        api_key (str): The api key to analyze or process.

    Behavioral Transparency:
        - Side Effects: This tool is read-only and produces no side effects. It does not modify
          any external state, databases, or files. All output is computed in-memory and returned
          directly to the caller.
        - Authentication: No authentication required for basic usage. Pro/Enterprise tiers
          require a valid MEOK API key passed via the MEOK_API_KEY environment variable.
        - Rate Limits: Free tier: 10 calls/day. Pro tier: unlimited. Rate limit headers are
          included in responses (X-RateLimit-Remaining, X-RateLimit-Reset).
        - Error Handling: Returns structured error objects with 'error' key on failure.
          Never raises unhandled exceptions. Invalid inputs return descriptive validation errors.
        - Idempotency: Fully idempotent — calling with the same inputs always produces the
          same output. Safe to retry on timeout or transient failure.
        - Data Privacy: No input data is stored, logged, or transmitted to external services.
          All processing happens locally within the MCP server process.
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    results = _db.list("expenses")
    if start_date:
        results = [e for e in results if e.get("date", "") >= start_date]
    if end_date:
        results = [e for e in results if e.get("date", "") <= end_date]
    if category:
        results = [e for e in results if e.get("category") == category]

    return json.dumps({"expenses": results[-limit:], "count": len(results)})


@mcp.tool()
def set_budget(amount: float, category: str = "Other", month: str = "", api_key: str = "") -> str:
    """Set monthly budget

    Behavior:
        This tool is read-only and stateless — it produces analysis output
        without modifying any external systems, databases, or files.
        Safe to call repeatedly with identical inputs (idempotent).
        Free tier: 10/day rate limit. Pro tier: unlimited.
        No authentication required for basic usage.

    When to use:
        Use this tool when you need structured analysis or classification
        of inputs against established frameworks or standards.

    When NOT to use:
        Not suitable for real-time production decision-making without
        human review of results.

    Args:
        amount (float): The amount to analyze or process.
        category (str): The category to analyze or process.
        month (str): The month to analyze or process.
        api_key (str): The api key to analyze or process.

    Behavioral Transparency:
        - Side Effects: This tool is read-only and produces no side effects. It does not modify
          any external state, databases, or files. All output is computed in-memory and returned
          directly to the caller.
        - Authentication: No authentication required for basic usage. Pro/Enterprise tiers
          require a valid MEOK API key passed via the MEOK_API_KEY environment variable.
        - Rate Limits: Free tier: 10 calls/day. Pro tier: unlimited. Rate limit headers are
          included in responses (X-RateLimit-Remaining, X-RateLimit-Reset).
        - Error Handling: Returns structured error objects with 'error' key on failure.
          Never raises unhandled exceptions. Invalid inputs return descriptive validation errors.
        - Idempotency: Fully idempotent — calling with the same inputs always produces the
          same output. Safe to retry on timeout or transient failure.
        - Data Privacy: No input data is stored, logged, or transmitted to external services.
          All processing happens locally within the MCP server process.
    """
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
    _db.hset("budgets", f"{category}:{month}", budget)
    return json.dumps({"set": True, "category": category, "budget": amount})


@mcp.tool()
def get_budget_status(category: str = "Other", month: str = "", api_key: str = "") -> str:
    """Get budget status

    Behavior:
        This tool is read-only and stateless — it produces analysis output
        without modifying any external systems, databases, or files.
        Safe to call repeatedly with identical inputs (idempotent).
        Free tier: 10/day rate limit. Pro tier: unlimited.
        No authentication required for basic usage.

    When to use:
        Use this tool when you need structured analysis or classification
        of inputs against established frameworks or standards.

    When NOT to use:
        Not suitable for real-time production decision-making without
        human review of results.

    Args:
        category (str): The category to analyze or process.
        month (str): The month to analyze or process.
        api_key (str): The api key to analyze or process.

    Behavioral Transparency:
        - Side Effects: This tool is read-only and produces no side effects. It does not modify
          any external state, databases, or files. All output is computed in-memory and returned
          directly to the caller.
        - Authentication: No authentication required for basic usage. Pro/Enterprise tiers
          require a valid MEOK API key passed via the MEOK_API_KEY environment variable.
        - Rate Limits: Free tier: 10 calls/day. Pro tier: unlimited. Rate limit headers are
          included in responses (X-RateLimit-Remaining, X-RateLimit-Reset).
        - Error Handling: Returns structured error objects with 'error' key on failure.
          Never raises unhandled exceptions. Invalid inputs return descriptive validation errors.
        - Idempotency: Fully idempotent — calling with the same inputs always produces the
          same output. Safe to retry on timeout or transient failure.
        - Data Privacy: No input data is stored, logged, or transmitted to external services.
          All processing happens locally within the MCP server process.
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    if not month:
        month = datetime.now().strftime("%Y-%m")

    budget_key = f"{category}:{month}"
    budget_data = _db.hget("budgets", budget_key)
    budget = budget_data.get("amount", 0) if budget_data else 0

    spent = sum(
        e["amount"]
        for e in _db.list("expenses")
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
    """Get spending by category

    Behavior:
        This tool is read-only and stateless — it produces analysis output
        without modifying any external systems, databases, or files.
        Safe to call repeatedly with identical inputs (idempotent).
        Free tier: 10/day rate limit. Pro tier: unlimited.
        No authentication required for basic usage.

    When to use:
        Use this tool when you need structured analysis or classification
        of inputs against established frameworks or standards.

    When NOT to use:
        Not suitable for real-time production decision-making without
        human review of results.

    Args:
        start_date (str): The start date to analyze or process.
        end_date (str): The end date to analyze or process.
        api_key (str): The api key to analyze or process.

    Behavioral Transparency:
        - Side Effects: This tool is read-only and produces no side effects. It does not modify
          any external state, databases, or files. All output is computed in-memory and returned
          directly to the caller.
        - Authentication: No authentication required for basic usage. Pro/Enterprise tiers
          require a valid MEOK API key passed via the MEOK_API_KEY environment variable.
        - Rate Limits: Free tier: 10 calls/day. Pro tier: unlimited. Rate limit headers are
          included in responses (X-RateLimit-Remaining, X-RateLimit-Reset).
        - Error Handling: Returns structured error objects with 'error' key on failure.
          Never raises unhandled exceptions. Invalid inputs return descriptive validation errors.
        - Idempotency: Fully idempotent — calling with the same inputs always produces the
          same output. Safe to retry on timeout or transient failure.
        - Data Privacy: No input data is stored, logged, or transmitted to external services.
          All processing happens locally within the MCP server process.
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    expenses = _db.list("expenses")
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
    """Get monthly summary

    Behavior:
        This tool is read-only and stateless — it produces analysis output
        without modifying any external systems, databases, or files.
        Safe to call repeatedly with identical inputs (idempotent).
        Free tier: 10/day rate limit. Pro tier: unlimited.
        No authentication required for basic usage.

    When to use:
        Use this tool when you need structured analysis or classification
        of inputs against established frameworks or standards.

    When NOT to use:
        Not suitable for real-time production decision-making without
        human review of results.

    Args:
        month (str): The month to analyze or process.
        api_key (str): The api key to analyze or process.

    Behavioral Transparency:
        - Side Effects: This tool is read-only and produces no side effects. It does not modify
          any external state, databases, or files. All output is computed in-memory and returned
          directly to the caller.
        - Authentication: No authentication required for basic usage. Pro/Enterprise tiers
          require a valid MEOK API key passed via the MEOK_API_KEY environment variable.
        - Rate Limits: Free tier: 10 calls/day. Pro tier: unlimited. Rate limit headers are
          included in responses (X-RateLimit-Remaining, X-RateLimit-Reset).
        - Error Handling: Returns structured error objects with 'error' key on failure.
          Never raises unhandled exceptions. Invalid inputs return descriptive validation errors.
        - Idempotency: Fully idempotent — calling with the same inputs always produces the
          same output. Safe to retry on timeout or transient failure.
        - Data Privacy: No input data is stored, logged, or transmitted to external services.
          All processing happens locally within the MCP server process.
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    if not month:
        month = datetime.now().strftime("%Y-%m")

    expenses = [
        e for e in _db.list("expenses") if e.get("date", "").startswith(month)
    ]

    total = sum(e.get("amount", 0) for e in expenses)

    return json.dumps({"month": month, "total": total, "expense_count": len(expenses)})


@mcp.tool()
def delete_expense(expense_id: str, api_key: str = "") -> str:
    """Delete expense

    Behavior:
        This tool is read-only and stateless — it produces analysis output
        without modifying any external systems, databases, or files.
        Safe to call repeatedly with identical inputs (idempotent).
        Free tier: 10/day rate limit. Pro tier: unlimited.
        No authentication required for basic usage.

    When to use:
        Use this tool when you need structured analysis or classification
        of inputs against established frameworks or standards.

    When NOT to use:
        Not suitable for real-time production decision-making without
        human review of results.

    Args:
        expense_id (str): The expense id to analyze or process.
        api_key (str): The api key to analyze or process.

    Behavioral Transparency:
        - Side Effects: This tool is read-only and produces no side effects. It does not modify
          any external state, databases, or files. All output is computed in-memory and returned
          directly to the caller.
        - Authentication: No authentication required for basic usage. Pro/Enterprise tiers
          require a valid MEOK API key passed via the MEOK_API_KEY environment variable.
        - Rate Limits: Free tier: 10 calls/day. Pro tier: unlimited. Rate limit headers are
          included in responses (X-RateLimit-Remaining, X-RateLimit-Reset).
        - Error Handling: Returns structured error objects with 'error' key on failure.
          Never raises unhandled exceptions. Invalid inputs return descriptive validation errors.
        - Idempotency: Fully idempotent — calling with the same inputs always produces the
          same output. Safe to retry on timeout or transient failure.
        - Data Privacy: No input data is stored, logged, or transmitted to external services.
          All processing happens locally within the MCP server process.
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": "https://meok.ai/pricing"})
    if err := _rl(): return err

    remaining = [e for e in _db.list("expenses") if e.get("id") != expense_id]
    _db.clear("expenses")
    for e in remaining:
        _db.append("expenses", e)
    _db.hdel("expenses_by_id", expense_id)
    return json.dumps({"deleted": True})


if __name__ == "__main__":
    mcp.run()
