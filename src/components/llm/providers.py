"""LLM provider definitions — models, tags, and connection details.

This is the single source of truth for all supported providers.
Frontend reads this to build the BYO settings UI.
"""

from pydantic import BaseModel


class ModelInfo(BaseModel, frozen=True):
    """A single model offered by a provider."""

    id: str
    tag: str = ""  # "recommended", "best_value", or ""


class ProviderInfo(BaseModel, frozen=True):
    """A supported LLM provider."""

    name: str
    slug: str  # unique key used in DB and API
    api_format: str  # "openai", "anthropic", "gemini"
    base_url: str  # default base URL (overridable for Azure)
    models: tuple[ModelInfo, ...]  # empty = free text input (Azure, OpenRouter)
    required_fields: tuple[str, ...]  # what the user must provide


# --- Provider Definitions ---

GROQ = ProviderInfo(
    name="Groq",
    slug="groq",
    api_format="openai",
    base_url="https://api.groq.com/openai/v1",
    models=(
        ModelInfo(id="llama-4-scout-17b-16e-instruct", tag="recommended"),
        ModelInfo(id="llama-3.3-70b-versatile"),
        ModelInfo(id="qwen-qwq-32b"),
        ModelInfo(id="gemma2-9b-it"),
        ModelInfo(id="mistral-saba-24b"),
    ),
    required_fields=("api_key",),
)

OPENAI = ProviderInfo(
    name="OpenAI",
    slug="openai",
    api_format="openai",
    base_url="https://api.openai.com/v1",
    models=(
        ModelInfo(id="gpt-5.4"),
        ModelInfo(id="gpt-5.4-mini", tag="recommended"),
        ModelInfo(id="gpt-5.4-nano"),
        ModelInfo(id="gpt-5.2"),
        ModelInfo(id="gpt-4.1"),
        ModelInfo(id="gpt-4.1-mini", tag="best_value"),
        ModelInfo(id="gpt-4.1-nano"),
        ModelInfo(id="gpt-4o"),
        ModelInfo(id="gpt-4o-mini"),
        ModelInfo(id="o3"),
        ModelInfo(id="o4-mini", tag="recommended"),
    ),
    required_fields=("api_key",),
)

ANTHROPIC = ProviderInfo(
    name="Anthropic",
    slug="anthropic",
    api_format="anthropic",
    base_url="https://api.anthropic.com/v1",
    models=(
        ModelInfo(id="claude-opus-4-7-20260416"),
        ModelInfo(id="claude-opus-4-6-20250514"),
        ModelInfo(id="claude-sonnet-4-6-20260217", tag="recommended"),
        ModelInfo(id="claude-haiku-4-5-20251001", tag="best_value"),
    ),
    required_fields=("api_key",),
)

GEMINI = ProviderInfo(
    name="Google Gemini",
    slug="gemini",
    api_format="gemini",
    base_url="https://generativelanguage.googleapis.com/v1beta",
    models=(
        ModelInfo(id="gemini-3.1-pro"),
        ModelInfo(id="gemini-3-flash", tag="recommended"),
        ModelInfo(id="gemini-3.1-flash-lite", tag="best_value"),
        ModelInfo(id="gemini-2.5-pro"),
        ModelInfo(id="gemini-2.5-flash"),
    ),
    required_fields=("api_key",),
)

AZURE_OPENAI = ProviderInfo(
    name="Azure OpenAI",
    slug="azure_openai",
    api_format="openai",
    base_url="",  # user provides endpoint
    models=(),  # free text — user enters deployment name
    required_fields=("api_key", "endpoint", "deployment_name", "api_version"),
)

OPENROUTER = ProviderInfo(
    name="OpenRouter",
    slug="openrouter",
    api_format="openai",
    base_url="https://openrouter.ai/api/v1",
    models=(),  # free text — user enters provider/model
    required_fields=("api_key", "model"),
)


# Registry — lookup by slug
PROVIDERS: dict[str, ProviderInfo] = {
    p.slug: p for p in (GROQ, OPENAI, ANTHROPIC, GEMINI, AZURE_OPENAI, OPENROUTER)
}

# Default provider for free/subscribed tiers
DEFAULT_PROVIDER = GROQ
DEFAULT_MODEL = "llama-4-scout-17b-16e-instruct"
