"""LLM component — multi-provider inference layer (Groq default + BYO key support)."""

from src.components.llm.service import chat as chat

__all__ = [
    "chat",
]
