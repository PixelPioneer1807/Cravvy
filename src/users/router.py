"""Users routes — profile management and BYO key configuration."""

from typing import Any

from fastapi import APIRouter, Depends

from src.auth.dependencies import get_current_user, require_verified
from src.auth.schemas import MessageResponseSchema
from src.components.llm.providers import PROVIDERS
from src.components.llm.schemas import BYOConfigSchema, ProviderListSchema, ProviderModelSchema
from src.users.schemas import ProfileResponseSchema, UpdateProfileRequestSchema
from src.users.service import delete_account, get_profile, save_byo_config, update_profile

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


@router.get("/providers", response_model=list[ProviderListSchema])
async def list_providers() -> list[ProviderListSchema]:
    """List all supported BYO providers and their models. Used by frontend settings page."""
    result: list[ProviderListSchema] = []
    for provider in PROVIDERS.values():
        # Skip groq — that's our default, not a BYO option
        if provider.slug == "groq":
            continue
        result.append(
            ProviderListSchema(
                name=provider.name,
                slug=provider.slug,
                models=[ProviderModelSchema(id=m.id, tag=m.tag) for m in provider.models],
                required_fields=list(provider.required_fields),
            )
        )
    return result


@router.post("/me/byo", response_model=MessageResponseSchema)
async def set_byo_config(
    body: BYOConfigSchema,
    user: dict[str, Any] = Depends(require_verified),
) -> MessageResponseSchema:
    """Save BYO (Bring Your Own) API key configuration."""
    await save_byo_config(user["id"], body.model_dump())
    return MessageResponseSchema(message="API key saved")


@router.delete("/me/byo", response_model=MessageResponseSchema)
async def remove_byo_config(
    user: dict[str, Any] = Depends(require_verified),
) -> MessageResponseSchema:
    """Remove BYO config and revert to free Groq tier."""
    await save_byo_config(user["id"], None)
    return MessageResponseSchema(message="Reverted to free tier")
