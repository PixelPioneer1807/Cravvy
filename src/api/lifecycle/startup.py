"""Startup hooks — validate and connect all services."""

import asyncio
import logging

from src.components.mcp.gateway import register_all_tools
from src.components.mcp.http import get_mcp_client
from src.shared import connect_mongo, connect_redis, disconnect_mongo, disconnect_redis, get_db

logger = logging.getLogger(__name__)


async def startup() -> None:
    """Connect to all services in parallel. Exit if any fail."""
    try:
        await asyncio.gather(connect_mongo(), connect_redis())
    except Exception as e:
        logger.critical("Service connection failed: %s", e)
        await asyncio.gather(disconnect_mongo(), disconnect_redis())
        raise SystemExit(1) from e

    # Create MongoDB indexes (idempotent — safe to run every startup)
    db = get_db()
    await asyncio.gather(
        db.users.create_index("email", unique=True),
        db.users.create_index("username", unique=True),
        db.indian_nutrition.create_index([("name", "text")]),
    )
    logger.info("MongoDB indexes ensured")

    # Initialize MCP HTTP client + register all tools
    get_mcp_client()
    register_all_tools()
    logger.info("MCP gateway initialized")

    logger.info("All services connected — ready to serve")
