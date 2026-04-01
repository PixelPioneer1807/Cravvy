"""Auth service — all authentication business logic."""

import logging
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from src.auth.exceptions import (
    AccountSuspendedError,
    EmailAlreadyExistsError,
    EmailNotVerifiedError,
    InvalidCredentialsError,
    InvalidTokenError,
)
from src.auth.models import UserModel, UserStatus
from src.shared import get_db, get_redis, settings

logger = logging.getLogger(__name__)

# bcrypt context — cost factor 12 means ~250ms per hash
# That's intentional — makes brute force infeasible
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token expiry constants
VERIFICATION_TOKEN_HOURS = 24
RESET_TOKEN_HOURS = 1


def _hash_password(password: str) -> str:
    """Hash a plain password with bcrypt."""
    return pwd_context.hash(password)


def _verify_password(plain: str, hashed: str) -> bool:
    """Check a plain password against its bcrypt hash."""
    return pwd_context.verify(plain, hashed)


def _create_access_token(user_id: str, email: str) -> str:
    """Create a short-lived JWT access token (15min default).

    Contains: sub (user id), email, exp (expiry), iat (issued at).
    Signed with HS256 using JWT_PRIVATE_KEY.
    """
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "email": email,
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_PRIVATE_KEY, algorithm="HS256")


def _generate_opaque_token() -> str:
    """Generate a cryptographically random token for refresh/verification/reset."""
    return secrets.token_urlsafe(32)


async def _get_users_collection() -> Any:
    """Get the MongoDB users collection."""
    db = get_db()
    return db.users


# --- Public API ---


async def signup(name: str, email: str, password: str) -> dict[str, Any]:
    """Create a new user account.

    1. Check email doesn't exist
    2. Hash password
    3. Generate verification token
    4. Insert user doc
    5. Return user data (caller sends the verification email)
    """
    users = await _get_users_collection()

    existing = await users.find_one({"email": email})
    if existing:
        raise EmailAlreadyExistsError()

    verification_token = _generate_opaque_token()
    now = datetime.now(UTC)

    user = UserModel(
        name=name,
        email=email,
        hashed_password=_hash_password(password),
        status=UserStatus.UNVERIFIED,
        created_at=now,
        updated_at=now,
        verification_token=verification_token,
        verification_expires_at=now + timedelta(hours=VERIFICATION_TOKEN_HOURS),
    )

    result = await users.insert_one(user.model_dump())
    user_id = str(result.inserted_id)

    logger.info("User created: %s (%s)", email, user_id)

    return {
        "user_id": user_id,
        "email": email,
        "name": name,
        "verification_token": verification_token,
    }


async def verify_email(token: str) -> None:
    """Verify a user's email with the token from the verification link.

    1. Find user by token
    2. Check not expired
    3. Set status to active
    4. Clear the verification token
    """
    users = await _get_users_collection()

    user = await users.find_one({"verification_token": token})
    if not user:
        raise InvalidTokenError("Invalid verification token")

    if user.get("verification_expires_at") and user["verification_expires_at"] < datetime.now(UTC):
        raise InvalidTokenError("Verification token has expired")

    await users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "status": UserStatus.ACTIVE,
                "updated_at": datetime.now(UTC),
            },
            "$unset": {
                "verification_token": "",
                "verification_expires_at": "",
            },
        },
    )

    logger.info("Email verified: %s", user["email"])


async def login(email: str, password: str) -> dict[str, Any]:
    """Authenticate a user and return tokens.

    1. Find user by email
    2. Verify password (same error for both failures — prevents enumeration)
    3. Check account status
    4. Create access token (JWT)
    5. Create refresh token (opaque, stored in Redis)
    6. Return both
    """
    users = await _get_users_collection()

    user = await users.find_one({"email": email})
    if not user:
        raise InvalidCredentialsError()

    if not _verify_password(password, user["hashed_password"]):
        raise InvalidCredentialsError()

    if user["status"] == UserStatus.SUSPENDED:
        raise AccountSuspendedError()

    if user["status"] == UserStatus.UNVERIFIED:
        raise EmailNotVerifiedError()

    user_id = str(user["_id"])
    access_token = _create_access_token(user_id, email)
    refresh_token = _generate_opaque_token()

    # Store refresh token in Redis with TTL
    # Key format: refresh:{token} → user_id
    redis = get_redis()
    await redis.set(
        f"refresh:{refresh_token}",
        user_id,
        ex=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )

    logger.info("User logged in: %s", email)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "id": user_id,
            "name": user["name"],
            "email": user["email"],
            "status": user["status"],
        },
    }


async def refresh_tokens(refresh_token: str) -> dict[str, Any]:
    """Rotate refresh token and issue new access token.

    1. Look up refresh token in Redis
    2. If not found → token was already used or revoked (possible breach)
    3. Delete old refresh token (rotation)
    4. Create new access + refresh tokens
    5. Store new refresh token in Redis

    If an old refresh token is reused, it means someone stole it.
    In that case we'd revoke all tokens for the user (not implemented yet — TODO).
    """
    redis = get_redis()

    user_id = await redis.get(f"refresh:{refresh_token}")
    if not user_id:
        raise InvalidTokenError("Invalid or expired refresh token")

    # Delete old token (rotation — can never be used again)
    await redis.delete(f"refresh:{refresh_token}")

    # Get user data for the new access token
    users = await _get_users_collection()
    user = await users.find_one({"_id": _to_object_id(user_id)})
    if not user:
        raise InvalidTokenError("User not found")

    # Create new token pair
    new_access_token = _create_access_token(user_id, user["email"])
    new_refresh_token = _generate_opaque_token()

    await redis.set(
        f"refresh:{new_refresh_token}",
        user_id,
        ex=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )

    logger.info("Tokens refreshed for user: %s", user_id)

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
    }


async def logout(refresh_token: str) -> None:
    """Delete the refresh token from Redis. Access token dies on its own (short TTL)."""
    redis = get_redis()
    await redis.delete(f"refresh:{refresh_token}")
    logger.info("User logged out")


async def forgot_password(email: str) -> str | None:
    """Generate a password reset token.

    Returns the token if user exists, None if not.
    Caller should ALWAYS return "check your email" regardless — prevents enumeration.
    """
    users = await _get_users_collection()

    user = await users.find_one({"email": email})
    if not user:
        return None

    reset_token = _generate_opaque_token()
    now = datetime.now(UTC)

    await users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "reset_token": reset_token,
                "reset_expires_at": now + timedelta(hours=RESET_TOKEN_HOURS),
                "updated_at": now,
            },
        },
    )

    logger.info("Password reset requested: %s", email)
    return reset_token


async def reset_password(token: str, new_password: str) -> None:
    """Reset password using the token from the reset email.

    1. Find user by reset token
    2. Check not expired
    3. Hash new password
    4. Clear reset token
    """
    users = await _get_users_collection()

    user = await users.find_one({"reset_token": token})
    if not user:
        raise InvalidTokenError("Invalid reset token")

    if user.get("reset_expires_at") and user["reset_expires_at"] < datetime.now(UTC):
        raise InvalidTokenError("Reset token has expired")

    await users.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "hashed_password": _hash_password(new_password),
                "updated_at": datetime.now(UTC),
            },
            "$unset": {
                "reset_token": "",
                "reset_expires_at": "",
            },
        },
    )

    logger.info("Password reset completed: %s", user["email"])


async def get_user_by_id(user_id: str) -> dict[str, Any] | None:
    """Fetch a user by their MongoDB _id. Used by auth dependencies."""
    users = await _get_users_collection()
    user = await users.find_one({"_id": _to_object_id(user_id)})
    if not user:
        return None
    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"],
        "status": user["status"],
    }


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and verify a JWT access token. Raises InvalidTokenError if invalid/expired."""
    try:
        payload: dict[str, Any] = jwt.decode(token, settings.JWT_PRIVATE_KEY, algorithms=["HS256"])
        return payload
    except JWTError as e:
        raise InvalidTokenError("Invalid access token") from e


def _to_object_id(id_str: str) -> Any:
    """Convert a string ID to MongoDB ObjectId."""
    from bson import ObjectId

    return ObjectId(id_str)
