"""Startup hooks — validate and connect all services."""

import asyncio
import logging

from src.shared import connect_mongo, connect_redis, disconnect_mongo, disconnect_redis

logger = logging.getLogger(__name__)


async def startup() -> None:
    """Connect to all services in parallel. Exit if any fail."""
    try:
        await asyncio.gather(connect_mongo(), connect_redis())
    except Exception as e:
        logger.critical("Service connection failed: %s", e)
        await asyncio.gather(disconnect_mongo(), disconnect_redis())
        raise SystemExit(1) from e

    logger.info("All services connected — ready to serve")
