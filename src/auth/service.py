"""Auth service — all authentication business logic.

Note: Uses standalone functions instead of an AuthService class.
FastAPI's Depends() pattern works cleaner with functions — no need to
instantiate a class per request. The module itself acts as the service.
"""

import asyncio
import logging
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import JWTError, jwt

from src.auth.exceptions import (
    AccountSuspendedError,
    EmailAlreadyExistsError,
    EmailNotVerifiedError,
    InvalidCredentialsError,
    InvalidTokenError,
    UsernameAlreadyExistsError,
)
from src.auth.models import UserModel, UserStatus
from src.shared import decrypt, encrypt, get_db, get_redis, settings

logger = logging.getLogger(__name__)

# Argon2id — memory-hard password hashing (OWASP #1 recommendation)
# Defaults: time_cost=3, memory_cost=65536 (64MB), parallelism=4
# 490x harder to crack on GPU than bcrypt
_hasher = PasswordHasher()

# Token expiry constants
VERIFICATION_TOKEN_HOURS = 24
RESET_TOKEN_HOURS = 1

# Type alias — MongoDB documents are untyped dicts, Any is unavoidable here
# because user dicts contain mixed types (str, int, dict, datetime)
type UserDict = dict[str, Any]
type TokenDict = dict[str, str]


def _hash_password(password: str) -> str:
    """Hash a password with Argon2id. Returns PHC string format."""
    return _hasher.hash(password)


def _verify_password(plain: str, hashed: str) -> bool:
    """Check a plain password against its Argon2id hash."""
    try:
        return _hasher.verify(hashed, plain)
    except VerifyMismatchError:
        return False


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


def _get_users_collection():  # type: ignore[no-untyped-def] — motor collection is untyped
    """Get the MongoDB users collection."""
    db = get_db()
    return db.users


def _to_object_id(id_str: str):  # type: ignore[no-untyped-def] — bson.ObjectId lacks stubs
    """Convert a string ID to MongoDB ObjectId."""
    from bson import ObjectId

    return ObjectId(id_str)


def _build_user_response(user_id: str, user: dict) -> UserDict:  # type: ignore[type-arg]
    """Build a safe user dict for API responses. Decrypts PII fields."""
    return {
        "id": user_id,
        "name": decrypt(user["name"]),
        "username": user["username"],  # plaintext
        "email": user["email"],  # plaintext
        "phone": decrypt(user["phone"]),
        "status": user["status"],
    }


# --- Public API ---


async def signup(name: str, username: str, email: str, phone: str, password: str) -> UserDict:
    """Create a new user account.

    1. Check email and username don't exist (parallel)
    2. Hash password
    3. Generate verification token
    4. Insert user doc
    5. Return user data (caller sends the verification email)
    """
    users = _get_users_collection()

    # Check email and username uniqueness in parallel
    existing_email, existing_username = await asyncio.gather(
        users.find_one({"email": email}),
        users.find_one({"username": username}),
    )
    if existing_email:
        raise EmailAlreadyExistsError()
    if existing_username:
        raise UsernameAlreadyExistsError()

    verification_token = _generate_opaque_token()
    now = datetime.now(UTC)

    user = UserModel(
        name=encrypt(name),
        username=username,  # plaintext — needed for unique index search
        email=email,  # plaintext — needed for login search
        phone=encrypt(phone),
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
    users = _get_users_collection()

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


async def login(email: str, password: str) -> UserDict:
    """Authenticate a user and return tokens.

    1. Find user by email
    2. Verify password (same error for both failures — prevents enumeration)
    3. Check account status
    4. Create access token (JWT)
    5. Create refresh token (opaque, stored in Redis)
    6. Return both
    """
    users = _get_users_collection()

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
        "user": _build_user_response(user_id, user),
    }


async def refresh_tokens(refresh_token: str) -> TokenDict:
    """Rotate refresh token and issue new access token.

    1. Look up refresh token in Redis
    2. If not found → token was already used or revoked (possible breach)
    3. Delete old refresh token (rotation)
    4. Create new access + refresh tokens
    5. Store new refresh token in Redis
    """
    redis = get_redis()

    user_id = await redis.get(f"refresh:{refresh_token}")
    if not user_id:
        raise InvalidTokenError("Invalid or expired refresh token")

    # Delete old token (rotation — can never be used again)
    await redis.delete(f"refresh:{refresh_token}")

    # Get user data for the new access token
    users = _get_users_collection()
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
    users = _get_users_collection()

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
    users = _get_users_collection()

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


async def get_user_by_id(user_id: str) -> UserDict | None:
    """Fetch a user by their MongoDB _id. Used by auth dependencies."""
    users = _get_users_collection()
    user = await users.find_one({"_id": _to_object_id(user_id)})
    if not user:
        return None
    return _build_user_response(str(user["_id"]), user)


def decode_access_token(token: str) -> dict[str, str]:
    """Decode and verify a JWT access token. Raises InvalidTokenError if invalid/expired."""
    try:
        payload: dict[str, str] = jwt.decode(token, settings.JWT_PRIVATE_KEY, algorithms=["HS256"])
        return payload
    except JWTError as e:
        raise InvalidTokenError("Invalid access token") from e
