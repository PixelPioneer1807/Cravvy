"""Auth-specific exceptions — extend the base AppError hierarchy."""

from src.shared import AppError


class EmailAlreadyExistsError(AppError):
    """Thrown when signup email is already registered."""

    def __init__(self) -> None:
        super().__init__(
            message="An account with this email already exists",
            status=409,
            code="EMAIL_ALREADY_EXISTS",
        )


class InvalidCredentialsError(AppError):
    """Thrown on login failure. Same message for wrong email OR wrong password — prevents
    enumeration."""

    def __init__(self) -> None:
        super().__init__(
            message="Invalid email or password",
            status=401,
            code="INVALID_CREDENTIALS",
        )


class EmailNotVerifiedError(AppError):
    """Thrown when an unverified user tries to access protected routes."""

    def __init__(self) -> None:
        super().__init__(
            message="Please verify your email before continuing",
            status=403,
            code="EMAIL_NOT_VERIFIED",
        )


class InvalidTokenError(AppError):
    """Thrown when a verification/reset/refresh token is invalid or expired."""

    def __init__(self, message: str = "Invalid or expired token") -> None:
        super().__init__(
            message=message,
            status=401,
            code="INVALID_TOKEN",
        )


class AccountSuspendedError(AppError):
    """Thrown when a suspended user tries to log in."""

    def __init__(self) -> None:
        super().__init__(
            message="Your account has been suspended",
            status=403,
            code="ACCOUNT_SUSPENDED",
        )
