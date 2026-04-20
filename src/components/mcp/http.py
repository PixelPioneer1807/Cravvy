"""Shared async HTTP client for all MCP tool calls.

Single httpx.AsyncClient with connection pooling — reused across
all platform API calls (Zomato, Swiggy, Zepto, Edamam, Google Maps).
"""

import logging

import httpx

logger = logging.getLogger(__name__)

_client: httpx.AsyncClient | None = None


def get_mcp_client() -> httpx.AsyncClient:
    """Get or create the shared MCP HTTP client."""
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=30.0)
    return _client


async def close_mcp_client() -> None:
    """Close the shared HTTP client. Called on shutdown."""
    global _client
    if _client:
        await _client.aclose()
        _client = None
        logger.info("MCP HTTP client closed")
