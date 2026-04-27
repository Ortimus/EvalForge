"""
Adapter Factory — resolves a provider string + model_id into a ready-to-use adapter.
This is the single place in the codebase that knows about concrete adapter classes.
"""
import os
from .base import BaseModelAdapter


def get_adapter(provider: str, model_id: str, api_key: str | None = None) -> BaseModelAdapter:
    """
    Returns an instantiated adapter for the given provider.

    Args:
        provider:  "anthropic" | "openai" | "huggingface" | "ollama"
        model_id:  provider-specific model identifier
        api_key:   optional override; falls back to environment variables

    Raises:
        ValueError: if provider is not recognised
    """
    provider = provider.lower().strip()

    if provider == "anthropic":
        from .anthropic_adapter import AnthropicAdapter
        return AnthropicAdapter(
            model_id=model_id,
            api_key=api_key or os.getenv("ANTHROPIC_API_KEY"),
        )

    if provider == "openai":
        from .openai_adapter import OpenAIAdapter
        return OpenAIAdapter(
            model_id=model_id,
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
        )

    if provider == "huggingface":
        from .huggingface_adapter import HuggingFaceAdapter
        return HuggingFaceAdapter(model_id=model_id)

    if provider == "ollama":
        from .ollama_adapter import OllamaAdapter
        return OllamaAdapter(
            model_id=model_id,
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        )

    raise ValueError(
        f"Unknown provider '{provider}'. "
        f"Valid options: anthropic, openai, huggingface, ollama"
    )
