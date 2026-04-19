"""Users request/response schemas — profile management."""

from pydantic import BaseModel, Field


class DietarySchema(BaseModel):
    """Dietary preferences — set during onboarding or settings."""

    diet_type: str = Field(
        default="non_veg",
        description="veg, non_veg, vegan, eggetarian, jain",
    )
    allergies: list[str] = Field(
        default_factory=list,
        description="List of allergens: nuts, dairy, gluten, shellfish, soy, etc.",
    )
    health_goal: str = Field(
        default="maintain",
        description="lose_weight, gain_muscle, maintain",
    )


class BudgetSchema(BaseModel):
    """Monthly food budget settings."""

    monthly_limit: float = Field(default=0, description="Monthly food budget in ₹. 0 = no limit.")
    spent: float = Field(default=0, description="Amount spent so far this month in ₹.")


class LocationSchema(BaseModel):
    """User location — for nearby restaurant discovery."""

    city: str = ""
    area: str = ""
    lat: float | None = None
    lng: float | None = None


class ProfileResponseSchema(BaseModel):
    """Full user profile returned to the frontend."""

    id: str
    name: str
    username: str
    email: str
    phone: str
    status: str
    dietary: DietarySchema
    budget: BudgetSchema
    location: LocationSchema
    subscription_tier: str
    messages_used: int


class UpdateProfileRequestSchema(BaseModel):
    """What the frontend sends to PATCH /users/me. All fields optional — only update what's sent."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    phone: str | None = Field(default=None, min_length=10, max_length=15)
    dietary: DietarySchema | None = None
    budget: BudgetSchema | None = None
    location: LocationSchema | None = None
