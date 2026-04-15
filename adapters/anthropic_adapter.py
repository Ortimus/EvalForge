"""
AnthropicAdapter — wraps the Anthropic Messages API.
"""
import anthropic
from .base import BaseModelAdapter, ModelMetadata


class AnthropicAdapter(BaseModelAdapter):

    def __init__(self, model_id: str = "claude-sonnet-4-20250514", api_key: str | None = None):
        self.model_id = model_id
        self.client = anthropic.Anthropic(api_key=api_key)

    def generate(self, prompt: str, max_tokens: int = 1024, **kwargs) -> str:
        message = self.client.messages.create(
            model=self.model_id,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text

    def get_metadata(self) -> ModelMetadata:
        return ModelMetadata(
            provider="anthropic",
            model_id=self.model_id,
            context_window=200000,
        )
