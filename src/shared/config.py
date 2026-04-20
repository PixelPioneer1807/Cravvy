"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration — crashes on startup if required vars are missing."""

    # App
    DEBUG: bool = False
    ENV: str = "development"
    PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"

    # MongoDB
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB_NAME: str = "cravvy"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_SESSION_TTL_SECONDS: int = 604800  # 7 days

    # Auth
    JWT_PRIVATE_KEY: str = ""
    JWT_PUBLIC_KEY: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"

    # Encryption — AES-256-GCM for PII at rest
    # Generate with: python -c "import secrets; print(secrets.token_hex(32))"
    ENCRYPTION_KEY: str = ""

    # AI (Groq — free tier: 25 msgs, then ₹49/60 msgs or BYO key)
    GROQ_API_KEY: str = ""

    # Integrations — OAuth client credentials for platform connections
    ZOMATO_CLIENT_ID: str = ""
    ZOMATO_CLIENT_SECRET: str = ""
    SWIGGY_CLIENT_ID: str = ""
    SWIGGY_CLIENT_SECRET: str = ""
    ZEPTO_CLIENT_ID: str = ""
    ZEPTO_CLIENT_SECRET: str = ""

    # Edamam — Recipe Search API
    EDAMAM_APP_ID: str = ""
    EDAMAM_APP_KEY: str = ""

    # Google Maps
    GOOGLE_MAPS_API_KEY: str = ""

    # Email
    RESEND_API_KEY: str = ""
    FROM_EMAIL: str = "noreply@cravvy.app"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
