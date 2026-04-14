"""User document model — what lives in MongoDB."""

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, EmailStr, Field


class UserStatus(StrEnum):
    """User account status."""

    UNVERIFIED = "unverified"
    ACTIVE = "active"
    SUSPENDED = "suspended"


class UserModel(BaseModel):
    """MongoDB user document structure.

    This is the full internal representation.
    Never return this directly — use UserResponseSchema for API responses.
    """

    name: str
    username: str
    email: EmailStr
    phone: str
    hashed_password: str
    status: UserStatus = UserStatus.UNVERIFIED
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Email verification
    verification_token: str | None = None
    verification_expires_at: datetime | None = None

    # Password reset
    reset_token: str | None = None
    reset_expires_at: datetime | None = None

    # Preferences (populated later by users module)
    dietary: dict[str, str] | None = None  # type, allergies, goals
    budget: dict[str, float] | None = None  # monthly limit, spent

    # Platform connections (populated by integrations module)
    connected_platforms: dict[str, dict[str, str]] | None = None

    # Recommendation engine state (Thompson Sampling)
    taste_profile: dict[str, dict[str, float]] | None = None

    # Message tracking (for pricing tiers)
    messages_used: int = 0
    subscription_tier: str = "free"  # free, subscribed, byo_key
    byo_provider: str | None = None  # groq, openai, anthropic, etc.
    byo_api_key: str | None = None  # encrypted, never returned in responses
