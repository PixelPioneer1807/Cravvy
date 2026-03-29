"""Application lifecycle — startup and shutdown hooks."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.lifecycle.shutdown import shutdown
from src.api.lifecycle.startup import startup
from src.shared import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Run startup before serving, shutdown after."""
    logger.info("Starting Cravvy [env=%s]", settings.ENV)
    await startup()
    yield
    logger.info("Shutting down Cravvy")
    await shutdown()


__all__ = [
    "lifespan",
]
