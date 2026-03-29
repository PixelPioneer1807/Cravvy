"""Health check endpoint for load balancers and monitoring."""

import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from src.shared import get_db, get_redis

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> JSONResponse:
    """Check MongoDB and Redis connectivity. Returns 200 or 503."""
    services: dict[str, str] = {}

    try:
        db = get_db()
        await db.client.admin.command("ping")
        services["mongodb"] = "ok"
    except Exception:
        services["mongodb"] = "down"

    try:
        redis = get_redis()
        await redis.ping()
        services["redis"] = "ok"
    except Exception:
        services["redis"] = "down"

    all_healthy = all(v == "ok" for v in services.values())

    return JSONResponse(
        status_code=200 if all_healthy else 503,
        content={"status": "ok" if all_healthy else "degraded", "services": services},
    )
