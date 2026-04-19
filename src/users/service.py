"""Users service — profile management business logic."""

import logging
from datetime import UTC, datetime
from typing import Any

from bson import ObjectId

from src.shared import NotFoundError, decrypt, encrypt, get_db

logger = logging.getLogger(__name__)

# Type alias — user profile dicts have mixed types (str, int, dict)
type ProfileDict = dict[str, Any]


def _get_users_collection():  # type: ignore[no-untyped-def] — motor is untyped
    """Get the MongoDB users collection."""
    db = get_db()
    return db.users


def _to_object_id(id_str: str):  # type: ignore[no-untyped-def] — bson lacks stubs
    """Convert a string ID to MongoDB ObjectId."""
    return ObjectId(id_str)


def _build_profile(user: dict) -> ProfileDict:  # type: ignore[type-arg]
    """Build a full profile dict from a MongoDB document. Decrypts PII fields."""
    return {
        "id": str(user["_id"]),
        "name": decrypt(user["name"]),
        "username": user["username"],
        "email": user["email"],
        "phone": decrypt(user["phone"]),
        "status": user["status"],
        "dietary": user.get("dietary")
        or {
            "diet_type": "non_veg",
            "allergies": [],
            "health_goal": "maintain",
        },
        "budget": user.get("budget") or {"monthly_limit": 0, "spent": 0},
        "location": user.get("location") or {"city": "", "area": "", "lat": None, "lng": None},
        "subscription_tier": user.get("subscription_tier", "free"),
        "messages_used": user.get("messages_used", 0),
    }


async def get_profile(user_id: str) -> ProfileDict:
    """Fetch the full user profile by ID."""
    users = _get_users_collection()
    user = await users.find_one({"_id": _to_object_id(user_id)})
    if not user:
        raise NotFoundError("user", user_id)
    return _build_profile(user)


async def update_profile(user_id: str, updates: dict) -> ProfileDict:  # type: ignore[type-arg]
    """Update user profile fields. Only updates what's provided.

    PII fields (name, phone) are encrypted before storing.
    """
    users = _get_users_collection()

    # Build the $set dict — only include non-None fields
    set_fields: dict[str, Any] = {"updated_at": datetime.now(UTC)}

    if updates.get("name") is not None:
        set_fields["name"] = encrypt(updates["name"])

    if updates.get("phone") is not None:
        set_fields["phone"] = encrypt(updates["phone"])

    if updates.get("dietary") is not None:
        set_fields["dietary"] = updates["dietary"]

    if updates.get("budget") is not None:
        set_fields["budget"] = updates["budget"]

    if updates.get("location") is not None:
        set_fields["location"] = updates["location"]

    result = await users.update_one(
        {"_id": _to_object_id(user_id)},
        {"$set": set_fields},
    )

    if result.matched_count == 0:
        raise NotFoundError("user", user_id)

    logger.info("Profile updated: %s", user_id)
    return await get_profile(user_id)


async def delete_account(user_id: str) -> None:
    """Permanently delete a user account and all associated data."""
    users = _get_users_collection()
    result = await users.delete_one({"_id": _to_object_id(user_id)})
    if result.deleted_count == 0:
        raise NotFoundError("user", user_id)

    logger.info("Account deleted: %s", user_id)


async def save_byo_config(user_id: str, config: dict[str, str] | None) -> None:
    """Save or remove BYO API key configuration.

    API key is encrypted before storing. Passing None removes BYO config.
    """
    users = _get_users_collection()

    if config is None:
        # Revert to free tier
        await users.update_one(
            {"_id": _to_object_id(user_id)},
            {
                "$set": {
                    "subscription_tier": "free",
                    "updated_at": datetime.now(UTC),
                },
                "$unset": {
                    "byo_provider": "",
                    "byo_api_key": "",
                    "byo_model": "",
                    "byo_endpoint": "",
                    "byo_deployment_name": "",
                    "byo_api_version": "",
                },
            },
        )
        logger.info("BYO config removed for user: %s", user_id)
        return

    # Encrypt the API key before storing
    set_fields: dict[str, Any] = {
        "subscription_tier": "byo_key",
        "byo_provider": config["provider"],
        "byo_api_key": encrypt(config["api_key"]),
        "updated_at": datetime.now(UTC),
    }

    # Optional fields depending on provider
    if config.get("model"):
        set_fields["byo_model"] = config["model"]
    if config.get("endpoint"):
        set_fields["byo_endpoint"] = config["endpoint"]
    if config.get("deployment_name"):
        set_fields["byo_deployment_name"] = config["deployment_name"]
    if config.get("api_version"):
        set_fields["byo_api_version"] = config["api_version"]

    result = await users.update_one(
        {"_id": _to_object_id(user_id)},
        {"$set": set_fields},
    )

    if result.matched_count == 0:
        raise NotFoundError("user", user_id)

    logger.info("BYO config saved for user: %s (provider: %s)", user_id, config["provider"])
