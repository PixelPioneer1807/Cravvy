"""Global error handler — catches all AppErrors and returns consistent JSON."""

import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from src.shared import AppError

logger = logging.getLogger(__name__)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Convert AppError into a clean JSON response."""
    request_id = getattr(request.state, "request_id", "unknown")

    logger.warning(
        "AppError [%s] %s — %s (request_id=%s)",
        exc.status,
        exc.code,
        exc.message,
        request_id,
    )

    return JSONResponse(
        status_code=exc.status,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "request_id": request_id,
            }
        },
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unexpected errors. Log the stack trace, return nothing useful to client."""
    request_id = getattr(request.state, "request_id", "unknown")

    logger.exception("Unhandled error (request_id=%s)", request_id)

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Something went wrong",
                "request_id": request_id,
            }
        },
    )
