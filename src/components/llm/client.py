"""LLM client — sends requests to the correct provider.

3 code paths:
1. OpenAI-compatible (OpenAI, Groq, Azure, OpenRouter) — same request format
2. Anthropic — custom headers, /messages endpoint, system as top-level field
3. Google Gemini — key in query param, model in URL, contents[].parts[] format
"""

import logging
from typing import Any

import httpx

from src.components.llm.schemas import ChatRequest, ChatResponse, TokenUsage
from src.shared import ExternalServiceError

logger = logging.getLogger(__name__)


def _api_error(provider: str, response: httpx.Response) -> ExternalServiceError:
    """Build a standardized API error from a failed response."""
    detail = response.text[:200]
    return ExternalServiceError(provider, f"HTTP {response.status_code}: {detail}")


# Reusable async HTTP client — connection pooling across requests
_http_client: httpx.AsyncClient | None = None


def _get_http_client() -> httpx.AsyncClient:
    """Lazy-init a shared httpx client for connection pooling."""
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(timeout=60.0)
    return _http_client


# --- OpenAI-Compatible Path (OpenAI, Groq, Azure, OpenRouter) ---


async def chat_openai(
    request: ChatRequest,
    api_key: str,
    base_url: str,
    extra_headers: dict[str, str] | None = None,
) -> ChatResponse:
    """Send chat completion to an OpenAI-compatible API."""
    client = _get_http_client()

    headers: dict[str, str] = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)

    body: dict[str, Any] = {
        "model": request.model,
        "messages": [{"role": m.role, "content": m.content} for m in request.messages],
        "max_tokens": request.max_tokens,
        "temperature": request.temperature,
    }
    if request.tools:
        body["tools"] = request.tools

    url = f"{base_url.rstrip('/')}/chat/completions"

    response = await client.post(url, headers=headers, json=body)

    if response.status_code != 200:
        logger.error("OpenAI-compat error [%s]: %s", response.status_code, response.text)
        raise _api_error("LLM", response)

    data = response.json()
    choice = data["choices"][0]
    message = choice["message"]
    usage = data.get("usage", {})

    return ChatResponse(
        content=message.get("content", ""),
        model=data.get("model", request.model),
        tool_calls=message.get("tool_calls"),
        usage=TokenUsage(
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
        ),
    )


async def chat_azure(
    request: ChatRequest,
    api_key: str,
    endpoint: str,
    deployment_name: str,
    api_version: str,
) -> ChatResponse:
    """Send chat completion to Azure OpenAI. Different URL structure + auth header."""
    client = _get_http_client()

    url = (
        f"{endpoint.rstrip('/')}/openai/deployments/{deployment_name}"
        f"/chat/completions?api-version={api_version}"
    )

    headers: dict[str, str] = {
        "api-key": api_key,
        "Content-Type": "application/json",
    }

    # Azure ignores the model field — deployment name determines the model
    body: dict[str, Any] = {
        "messages": [{"role": m.role, "content": m.content} for m in request.messages],
        "max_tokens": request.max_tokens,
        "temperature": request.temperature,
    }
    if request.tools:
        body["tools"] = request.tools

    response = await client.post(url, headers=headers, json=body)

    if response.status_code != 200:
        logger.error("Azure error [%s]: %s", response.status_code, response.text)
        raise _api_error("Azure OpenAI", response)

    data = response.json()
    choice = data["choices"][0]
    message = choice["message"]
    usage = data.get("usage", {})

    return ChatResponse(
        content=message.get("content", ""),
        model=deployment_name,
        tool_calls=message.get("tool_calls"),
        usage=TokenUsage(
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
        ),
    )


# --- Anthropic Path ---


async def chat_anthropic(
    request: ChatRequest,
    api_key: str,
    base_url: str,
) -> ChatResponse:
    """Send messages to Anthropic's API. Custom format."""
    client = _get_http_client()

    headers: dict[str, str] = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }

    # Anthropic: system is a top-level field, not a message
    system_prompt = ""
    messages: list[dict[str, str]] = []
    for m in request.messages:
        if m.role == "system":
            system_prompt = m.content
        else:
            messages.append({"role": m.role, "content": m.content})

    body: dict[str, Any] = {
        "model": request.model,
        "max_tokens": request.max_tokens,
        "messages": messages,
    }
    if system_prompt:
        body["system"] = system_prompt
    if request.tools:
        body["tools"] = request.tools

    url = f"{base_url.rstrip('/')}/messages"

    response = await client.post(url, headers=headers, json=body)

    if response.status_code != 200:
        logger.error("Anthropic error [%s]: %s", response.status_code, response.text)
        raise _api_error("Anthropic", response)

    data = response.json()
    usage = data.get("usage", {})

    # Anthropic returns content as a list of blocks
    content_blocks = data.get("content", [])
    text_content = ""
    tool_calls = []
    for block in content_blocks:
        if block.get("type") == "text":
            text_content += block.get("text", "")
        elif block.get("type") == "tool_use":
            tool_calls.append(block)

    return ChatResponse(
        content=text_content,
        model=data.get("model", request.model),
        tool_calls=tool_calls if tool_calls else None,
        usage=TokenUsage(
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            total_tokens=usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
        ),
    )


# --- Google Gemini Path ---


async def chat_gemini(
    request: ChatRequest,
    api_key: str,
    base_url: str,
) -> ChatResponse:
    """Send generateContent to Google Gemini. Completely different format."""
    client = _get_http_client()

    # Gemini: model in URL, key as query param
    url = f"{base_url.rstrip('/')}/models/{request.model}:generateContent?key={api_key}"

    # Gemini: system is systemInstruction, messages are contents[].parts[]
    system_instruction = None
    contents: list[dict[str, Any]] = []
    for m in request.messages:
        if m.role == "system":
            system_instruction = {"parts": [{"text": m.content}]}
        else:
            role = "user" if m.role == "user" else "model"
            contents.append({"role": role, "parts": [{"text": m.content}]})

    body: dict[str, Any] = {
        "contents": contents,
        "generationConfig": {
            "temperature": request.temperature,
            "maxOutputTokens": request.max_tokens,
        },
    }
    if system_instruction:
        body["systemInstruction"] = system_instruction
    if request.tools:
        body["tools"] = request.tools

    response = await client.post(url, json=body, headers={"Content-Type": "application/json"})

    if response.status_code != 200:
        logger.error("Gemini error [%s]: %s", response.status_code, response.text)
        raise _api_error("Google Gemini", response)

    data = response.json()
    candidates = data.get("candidates", [])

    text_content = ""
    tool_calls = []
    if candidates:
        parts = candidates[0].get("content", {}).get("parts", [])
        for part in parts:
            if "text" in part:
                text_content += part["text"]
            elif "functionCall" in part:
                tool_calls.append(part["functionCall"])

    usage_meta = data.get("usageMetadata", {})

    return ChatResponse(
        content=text_content,
        model=request.model,
        tool_calls=tool_calls if tool_calls else None,
        usage=TokenUsage(
            input_tokens=usage_meta.get("promptTokenCount", 0),
            output_tokens=usage_meta.get("candidatesTokenCount", 0),
            total_tokens=usage_meta.get("totalTokenCount", 0),
        ),
    )
