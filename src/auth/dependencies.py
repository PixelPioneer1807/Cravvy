"""Auth dependencies — inject authenticated user into route handlers."""

from typing import Any

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.auth.exceptions import EmailNotVerifiedError, InvalidTokenError
from src.auth.service import decode_access_token, get_user_by_id

# HTTPBearer extracts the token from "Authorization: Bearer <token>" header
# auto_error=False means it returns None instead of 403 if header is missing
_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> dict[str, Any]:
    """Extract and verify JWT from Authorization header. Returns user dict.

    Usage in routes:
        @router.get("/me")
        async def me(user: dict = Depends(get_current_user)):
            return user
    """
    if not credentials:
        raise InvalidTokenError("Missing authorization header")

    payload = decode_access_token(credentials.credentials)

    user_id = payload.get("sub")
    if not user_id:
        raise InvalidTokenError("Invalid token payload")

    user = await get_user_by_id(user_id)
    if not user:
        raise InvalidTokenError("User not found")

    return user


async def require_verified(
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Same as get_current_user but also checks email is verified.

    Usage in routes:
        @router.post("/meals/plan")
        async def generate_plan(user: dict = Depends(require_verified)):
            ...
    """
    if user.get("status") != "active":
        raise EmailNotVerifiedError()

    return user
