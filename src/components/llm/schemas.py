"""LLM schemas — request/response models for the inference layer."""

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single message in a conversation."""

    role: str = Field(description="system, user, or assistant")
    content: str


class TokenUsage(BaseModel):
    """Token usage for tracking message limits."""

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


class ChatRequest(BaseModel):
    """What gets sent to the LLM client internally."""

    messages: list[ChatMessage]
    model: str
    max_tokens: int = 1024
    temperature: float = 0.7
    # Tool definitions vary per provider (OpenAI vs Anthropic vs Gemini format)
    tools: list[dict] | None = None  # type: ignore[type-arg]


class ChatResponse(BaseModel):
    """What the LLM client returns."""

    content: str
    model: str
    # Tool call shape differs per provider — normalized downstream
    tool_calls: list[dict] | None = None  # type: ignore[type-arg]
    usage: TokenUsage | None = None


class BYOConfigSchema(BaseModel):
    """What the frontend sends when user configures BYO key."""

    provider: str = Field(
        description="Provider slug: openai, anthropic, gemini, azure_openai, openrouter",
    )
    api_key: str = Field(min_length=1)
    model: str = Field(
        default="",
        description="Model ID. Required for all except Azure.",
    )

    # Azure-specific fields
    endpoint: str = Field(default="", description="Azure endpoint URL")
    deployment_name: str = Field(default="", description="Azure deployment name")
    api_version: str = Field(default="", description="Azure API version")


class ProviderModelSchema(BaseModel):
    """A model in the provider list — for frontend dropdown."""

    id: str
    tag: str


class ProviderListSchema(BaseModel):
    """A provider and its models — for frontend settings page."""

    name: str
    slug: str
    models: list[ProviderModelSchema]
    required_fields: list[str]
