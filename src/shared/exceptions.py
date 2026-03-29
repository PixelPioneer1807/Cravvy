"""Base exception hierarchy for consistent error handling."""


class AppError(Exception):
    """Base error — all custom exceptions extend this."""

    def __init__(self, message: str, status: int, code: str) -> None:
        self.message = message
        self.status = status
        self.code = code
        super().__init__(message)


class NotFoundError(AppError):
    """Resource not found."""

    def __init__(self, resource: str, id: str) -> None:
        super().__init__(
            message=f"{resource} not found",
            status=404,
            code="RESOURCE_NOT_FOUND",
        )


class AuthError(AppError):
    """Authentication or authorization failure."""

    def __init__(self, message: str = "Invalid credentials") -> None:
        super().__init__(message=message, status=401, code="AUTH_FAILED")


class ForbiddenError(AppError):
    """Insufficient permissions."""

    def __init__(self, message: str = "Forbidden") -> None:
        super().__init__(message=message, status=403, code="FORBIDDEN")


class ValidationError(AppError):
    """Request validation failure."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, status=422, code="VALIDATION_ERROR")


class RateLimitError(AppError):
    """Rate limit exceeded."""

    def __init__(self, message: str = "Too many requests") -> None:
        super().__init__(message=message, status=429, code="RATE_LIMIT_EXCEEDED")


class ExternalServiceError(AppError):
    """External service (MCP, Groq, etc.) failure."""

    def __init__(self, service: str, message: str = "Service unavailable") -> None:
        super().__init__(
            message=f"{service}: {message}",
            status=502,
            code="EXTERNAL_SERVICE_ERROR",
        )
