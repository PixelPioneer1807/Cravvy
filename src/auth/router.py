"""Auth routes — signup, login, refresh, logout, verify, forgot/reset password."""

import logging

from fastapi import APIRouter, Cookie, Response

from src.auth.exceptions import InvalidTokenError
from src.auth.schemas import (
    AuthResponseSchema,
    ForgotPasswordRequestSchema,
    LoginRequestSchema,
    MessageResponseSchema,
    ResetPasswordRequestSchema,
    SignupRequestSchema,
    TokenResponseSchema,
)
from src.auth.service import (
    forgot_password,
    login,
    logout,
    refresh_tokens,
    reset_password,
    signup,
    verify_email,
)
from src.shared import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

# Cookie settings for refresh token
_REFRESH_COOKIE_KEY = "refresh_token"
_REFRESH_COOKIE_MAX_AGE = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60  # days → seconds


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    """Set the refresh token as an HttpOnly secure cookie."""
    response.set_cookie(
        key=_REFRESH_COOKIE_KEY,
        value=refresh_token,
        max_age=_REFRESH_COOKIE_MAX_AGE,
        httponly=True,  # JS can't read it — blocks XSS
        secure=settings.ENV != "development",  # HTTPS only in production
        samesite="strict",  # blocks CSRF
        path="/api/v1/auth",  # only sent to auth endpoints
    )


def _clear_refresh_cookie(response: Response) -> None:
    """Delete the refresh token cookie."""
    response.delete_cookie(
        key=_REFRESH_COOKIE_KEY,
        path="/api/v1/auth",
    )


@router.post("/signup", response_model=MessageResponseSchema, status_code=201)
async def signup_route(body: SignupRequestSchema) -> MessageResponseSchema:
    """Create a new account and send verification email."""
    result = await signup(body.name, body.username, body.email, body.phone, body.password)

    # TODO: send verification email via Resend
    # For now, log the token (remove in production)
    logger.info(
        "Verification token for %s: %s",
        result["email"],
        result["verification_token"],
    )

    return MessageResponseSchema(message="Account created. Please check your email to verify.")


@router.get("/verify", response_model=MessageResponseSchema)
async def verify_route(token: str) -> MessageResponseSchema:
    """Verify email address using the token from the verification link."""
    await verify_email(token)
    return MessageResponseSchema(message="Email verified. You can now log in.")


@router.post("/login", response_model=AuthResponseSchema)
async def login_route(body: LoginRequestSchema, response: Response) -> AuthResponseSchema:
    """Authenticate and return access token + set refresh cookie."""
    result = await login(body.email, body.password)

    _set_refresh_cookie(response, result["refresh_token"])

    return AuthResponseSchema(
        access_token=result["access_token"],
        user=result["user"],
    )


@router.post("/refresh", response_model=TokenResponseSchema)
async def refresh_route(
    response: Response,
    refresh_token: str | None = Cookie(None, alias="refresh_token"),
) -> TokenResponseSchema:
    """Rotate refresh token and issue new access token. Reads from HttpOnly cookie."""
    if not refresh_token:
        raise InvalidTokenError("Missing refresh token")

    result = await refresh_tokens(refresh_token)

    _set_refresh_cookie(response, result["refresh_token"])

    return TokenResponseSchema(access_token=result["access_token"])


@router.post("/logout", response_model=MessageResponseSchema)
async def logout_route(
    response: Response,
    refresh_token: str | None = Cookie(None, alias="refresh_token"),
) -> MessageResponseSchema:
    """Logout — delete refresh token from Redis and clear cookie."""
    if refresh_token:
        await logout(refresh_token)

    _clear_refresh_cookie(response)

    return MessageResponseSchema(message="Logged out")


@router.post("/forgot-password", response_model=MessageResponseSchema)
async def forgot_password_route(body: ForgotPasswordRequestSchema) -> MessageResponseSchema:
    """Request a password reset email. Always returns success — prevents email enumeration."""
    reset_token = await forgot_password(body.email)

    if reset_token:
        # TODO: send reset email via Resend
        logger.info("Reset token for %s: %s", body.email, reset_token)

    # Always return the same message, even if email doesn't exist
    return MessageResponseSchema(message="If an account exists, a reset link has been sent.")


@router.post("/reset-password", response_model=MessageResponseSchema)
async def reset_password_route(body: ResetPasswordRequestSchema) -> MessageResponseSchema:
    """Reset password using the token from the reset email."""
    await reset_password(body.token, body.new_password)
    return MessageResponseSchema(message="Password reset successful. You can now log in.")
