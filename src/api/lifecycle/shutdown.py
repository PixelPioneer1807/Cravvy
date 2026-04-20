"""Shutdown hooks — close all connections gracefully."""

import asyncio
import logging

from src.components.mcp.http import close_mcp_client
from src.shared import disconnect_mongo, disconnect_redis

logger = logging.getLogger(__name__)


async def shutdown() -> None:
    """Disconnect all services in parallel."""
    await asyncio.gather(disconnect_mongo(), disconnect_redis(), close_mcp_client())
    logger.info("All connections closed — goodbye")
