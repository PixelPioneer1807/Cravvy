"""LLM provider definitions — models, tags, and connection details.

This is the single source of truth for all supported providers.
Frontend reads this to build the BYO settings UI.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelInfo:
    """A single model offered by a provider."""

    id: str
    tag: str = ""  # "recommended", "best_value", or ""


@dataclass(frozen=True)
class ProviderInfo:
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
        ModelInfo("llama-4-scout-17b-16e-instruct", "recommended"),
        ModelInfo("llama-3.3-70b-versatile"),
        ModelInfo("qwen-qwq-32b"),
        ModelInfo("gemma2-9b-it"),
        ModelInfo("mistral-saba-24b"),
    ),
    required_fields=("api_key",),
)

OPENAI = ProviderInfo(
    name="OpenAI",
    slug="openai",
    api_format="openai",
    base_url="https://api.openai.com/v1",
    models=(
        ModelInfo("gpt-5.4"),
        ModelInfo("gpt-5.4-mini", "recommended"),
        ModelInfo("gpt-5.4-nano"),
        ModelInfo("gpt-5.2"),
        ModelInfo("gpt-4.1"),
        ModelInfo("gpt-4.1-mini", "best_value"),
        ModelInfo("gpt-4.1-nano"),
        ModelInfo("gpt-4o"),
        ModelInfo("gpt-4o-mini"),
        ModelInfo("o3"),
        ModelInfo("o4-mini", "recommended"),
    ),
    required_fields=("api_key",),
)

ANTHROPIC = ProviderInfo(
    name="Anthropic",
    slug="anthropic",
    api_format="anthropic",
    base_url="https://api.anthropic.com/v1",
    models=(
        ModelInfo("claude-opus-4-7-20260416"),
        ModelInfo("claude-opus-4-6-20250514"),
        ModelInfo("claude-sonnet-4-6-20260217", "recommended"),
        ModelInfo("claude-haiku-4-5-20251001", "best_value"),
    ),
    required_fields=("api_key",),
)

GEMINI = ProviderInfo(
    name="Google Gemini",
    slug="gemini",
    api_format="gemini",
    base_url="https://generativelanguage.googleapis.com/v1beta",
    models=(
        ModelInfo("gemini-3.1-pro"),
        ModelInfo("gemini-3-flash", "recommended"),
        ModelInfo("gemini-3.1-flash-lite", "best_value"),
        ModelInfo("gemini-2.5-pro"),
        ModelInfo("gemini-2.5-flash"),
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
