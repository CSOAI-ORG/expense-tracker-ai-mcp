<div align="center">

# Expense Tracker Ai MCP

**MCP server for expense tracker ai mcp operations**

[![PyPI](https://img.shields.io/pypi/v/meok-expense-tracker-ai-mcp)](https://pypi.org/project/meok-expense-tracker-ai-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MEOK AI Labs](https://img.shields.io/badge/MEOK_AI_Labs-MCP_Server-purple)](https://meok.ai)

</div>

## Overview

Expense Tracker Ai MCP provides AI-powered tools via the Model Context Protocol (MCP).

## Tools

| Tool | Description |
|------|-------------|
| `add_expense` | Add new expense |
| `get_expenses` | Get expenses with filters |
| `set_budget` | Set monthly budget |
| `get_budget_status` | Get budget status |
| `get_category_summary` | Get spending by category |
| `get_monthly_summary` | Get monthly summary |
| `delete_expense` | Delete expense |

## Installation

```bash
pip install meok-expense-tracker-ai-mcp
```

## Usage with Claude Desktop

Add to your Claude Desktop MCP config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "expense-tracker-ai": {
      "command": "python",
      "args": ["-m", "meok_expense_tracker_ai_mcp.server"]
    }
  }
}
```

## Usage with FastMCP

```python
from mcp.server.fastmcp import FastMCP

# This server exposes 7 tool(s) via MCP
# See server.py for full implementation
```

## License

MIT © [MEOK AI Labs](https://meok.ai)
