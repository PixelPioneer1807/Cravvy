"""Auth request/response schemas — the contract between frontend and backend."""

from pydantic import BaseModel, EmailStr, Field

# --- Requests ---


class SignupRequestSchema(BaseModel):
    """What the frontend sends to POST /auth/signup."""

    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequestSchema(BaseModel):
    """What the frontend sends to POST /auth/login."""

    email: EmailStr
    password: str


class ForgotPasswordRequestSchema(BaseModel):
    """What the frontend sends to POST /auth/forgot-password."""

    email: EmailStr


class ResetPasswordRequestSchema(BaseModel):
    """What the frontend sends to POST /auth/reset-password."""

    token: str
    new_password: str = Field(min_length=8, max_length=128)


# --- Responses ---


class TokenResponseSchema(BaseModel):
    """What the backend returns after login/refresh. Access token only — refresh token goes in
    HttpOnly cookie."""

    access_token: str
    token_type: str = "bearer"


class UserResponseSchema(BaseModel):
    """Public user data returned to the frontend. Never includes password or internal fields."""

    id: str
    name: str
    email: str
    status: str


class AuthResponseSchema(BaseModel):
    """Login/signup success response — tokens + user info."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponseSchema


class MessageResponseSchema(BaseModel):
    """Generic success message for actions like signup, logout, verify, etc."""

    message: str
