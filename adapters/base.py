"""
BaseModelAdapter — the contract every model provider must implement.
All evaluation logic depends ONLY on this interface, never on concrete adapters.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ModelMetadata:
    provider: str          # e.g. "anthropic", "openai", "huggingface", "ollama"
    model_id: str          # e.g. "claude-sonnet-4-20250514"
    version: str = "unknown"
    context_window: int = 0


class BaseModelAdapter(ABC):

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Send a prompt, return the model's text response."""
        ...

    @abstractmethod
    def get_metadata(self) -> ModelMetadata:
        """Return identifying metadata for MLflow logging."""
        ...
