"""Users routes — profile management endpoints."""

from typing import Any

from fastapi import APIRouter, Depends

from src.auth.dependencies import get_current_user, require_verified
from src.auth.schemas import MessageResponseSchema
from src.users.schemas import ProfileResponseSchema, UpdateProfileRequestSchema
from src.users.service import delete_account, get_profile, update_profile

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/me", response_model=ProfileResponseSchema)
async def get_me(user: dict[str, Any] = Depends(get_current_user)) -> ProfileResponseSchema:
    """Get the current user's full profile."""
    profile = await get_profile(user["id"])
    return ProfileResponseSchema(**profile)


@router.patch("/me", response_model=ProfileResponseSchema)
async def update_me(
    body: UpdateProfileRequestSchema,
    user: dict[str, Any] = Depends(require_verified),
) -> ProfileResponseSchema:
    """Update the current user's profile. Only send fields you want to change."""
    # exclude_none=True → only include fields the user actually sent
    updates = body.model_dump(exclude_none=True)
    profile = await update_profile(user["id"], updates)
    return ProfileResponseSchema(**profile)


@router.delete("/me", response_model=MessageResponseSchema)
async def delete_me(
    user: dict[str, Any] = Depends(require_verified),
) -> MessageResponseSchema:
    """Permanently delete the current user's account."""
    await delete_account(user["id"])
    return MessageResponseSchema(message="Account deleted")
