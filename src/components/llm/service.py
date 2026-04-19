"""LLM service — routes requests to the correct provider based on user config."""

import logging

from src.components.llm.client import (
    chat_anthropic,
    chat_azure,
    chat_gemini,
    chat_openai,
)
from src.components.llm.providers import DEFAULT_MODEL, DEFAULT_PROVIDER, PROVIDERS
from src.components.llm.schemas import ChatMessage, ChatRequest, ChatResponse
from src.shared import ExternalServiceError, decrypt, settings

logger = logging.getLogger(__name__)


async def chat(
    messages: list[dict[str, str]],
    user_config: dict[str, str] | None = None,
    tools: list[dict] | None = None,  # type: ignore[type-arg]
    max_tokens: int = 1024,
    temperature: float = 0.7,
) -> ChatResponse:
    """Send a chat request to the appropriate LLM provider.

    Args:
        messages: List of {role, content} dicts.
        user_config: BYO config from user's MongoDB doc. None = use default Groq.
        tools: MCP tool definitions for function calling.
        max_tokens: Max response tokens.
        temperature: Sampling temperature.

    Returns:
        ChatResponse with content, tool_calls, and usage.
    """
    # Determine provider and credentials
    if user_config and user_config.get("provider"):
        provider_slug = user_config["provider"]
        api_key = decrypt(user_config["api_key"])
        model = user_config.get("model", "")
    else:
        # Default: Groq with our server key
        provider_slug = DEFAULT_PROVIDER.slug
        api_key = settings.GROQ_API_KEY
        model = DEFAULT_MODEL

    provider = PROVIDERS.get(provider_slug)
    if not provider:
        raise ExternalServiceError("LLM", f"Unknown provider: {provider_slug}")

    request = ChatRequest(
        messages=[ChatMessage(role=m["role"], content=m["content"]) for m in messages],
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        tools=tools,
    )

    # Route to the correct code path
    if provider_slug == "azure_openai":
        return await chat_azure(
            request=request,
            api_key=api_key,
            endpoint=user_config["endpoint"] if user_config else "",
            deployment_name=user_config["deployment_name"] if user_config else "",
            api_version=user_config.get("api_version", "2024-12-01-preview") if user_config else "",
        )

    if provider.api_format == "anthropic":
        return await chat_anthropic(
            request=request,
            api_key=api_key,
            base_url=provider.base_url,
        )

    if provider.api_format == "gemini":
        return await chat_gemini(
            request=request,
            api_key=api_key,
            base_url=provider.base_url,
        )

    # OpenAI-compatible (OpenAI, Groq, OpenRouter)
    extra_headers: dict[str, str] = {}
    if provider_slug == "openrouter":
        extra_headers["HTTP-Referer"] = "https://cravvy.app"
        extra_headers["X-Title"] = "Cravvy"

    return await chat_openai(
        request=request,
        api_key=api_key,
        base_url=provider.base_url,
        extra_headers=extra_headers if extra_headers else None,
    )
