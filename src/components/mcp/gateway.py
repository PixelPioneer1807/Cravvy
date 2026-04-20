"""MCP Gateway — central FastMCP server that registers all tools.

All food platform tools, recipe tools, nutrition tools, and maps tools
are registered on this single server. The chat module calls these tools
based on LLM decisions.
"""

import importlib
import logging

from fastmcp import FastMCP

logger = logging.getLogger(__name__)

# The central MCP server — all tools registered here
gateway = FastMCP("Cravvy MCP Gateway")

# All tool modules to import at startup — each registers tools via @gateway.tool
_TOOL_MODULES = [
    "src.components.mcp.tools.zomato",
    "src.components.mcp.tools.swiggy_food",
    "src.components.mcp.tools.swiggy_instamart",
    "src.components.mcp.tools.swiggy_dineout",
    "src.components.mcp.tools.zepto",
    "src.components.mcp.tools.edamam",
    "src.components.mcp.tools.indb",
    "src.components.mcp.tools.google_maps",
]


def register_all_tools() -> None:
    """Import all tool modules to trigger @gateway.tool registrations.

    Called once at startup. Each tool module imports `gateway` and
    decorates its functions with @gateway.tool.
    """
    for module_path in _TOOL_MODULES:
        importlib.import_module(module_path)

    tool_count = len(gateway._tool_manager._tools)  # type: ignore[attr-defined]
    logger.info("MCP Gateway: %d tools registered", tool_count)
