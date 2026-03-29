"""FastAPI application factory."""

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes.health import router as health_router
from src.shared import settings
from src.shared.database import (
    connect_mongo,
    connect_redis,
    disconnect_mongo,
    disconnect_redis,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup and shutdown lifecycle.

    Startup: validate all services before accepting requests.
    Shutdown: close all connections gracefully.
    """
    # --- Startup ---
    logger.info("Starting Cravvy [env=%s]", settings.ENV)

    try:
        await asyncio.gather(connect_mongo(), connect_redis())
    except Exception as e:
        logger.critical("Service connection failed: %s", e)
        await asyncio.gather(disconnect_mongo(), disconnect_redis())
        raise SystemExit(1) from e

    logger.info("All services connected — ready to serve")

    yield

    # --- Shutdown ---
    logger.info("Shutting down Cravvy")
    await asyncio.gather(disconnect_mongo(), disconnect_redis())
    logger.info("All connections closed — goodbye")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Cravvy",
        description="Your food wingman",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )

    # Middleware (order matters — first added = outermost)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.FRONTEND_URL],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes
    app.include_router(health_router)

    return app
