"""
AnthropicAdapter — wraps the Anthropic Messages API.
"""
import anthropic
from .config import provider_config
from .base import BaseModelAdapter, ModelMetadata


def extract_text(message) -> str:
    """
    Join the text blocks of a Messages API response.

    Newer models may return other block types (e.g. 'thinking') before the
    answer, so content[0].text is not safe. Only 'text' blocks are the answer.
    """
    text = "".join(b.text for b in message.content if getattr(b, "type", None) == "text")
    if not text:
        raise ValueError(
            f"Response contained no text block (stop_reason={getattr(message, 'stop_reason', None)}, "
            f"block types={[getattr(b, 'type', '?') for b in message.content]})"
        )
    return text


class AnthropicAdapter(BaseModelAdapter):

    def __init__(self, model_id: str, api_key: str | None = None):
        # model_id is required: defaults live in configs/models.yaml and are
        # resolved by adapters.factory.get_adapter().
        self.model_id = model_id
        self.max_tokens = provider_config("anthropic").get("max_tokens", 1024)
        self.client = anthropic.Anthropic(api_key=api_key)

    def generate(self, prompt: str, max_tokens: int | None = None, **kwargs) -> str:
        message = self.client.messages.create(
            model=self.model_id,
            max_tokens=max_tokens or self.max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return extract_text(message)

    def get_metadata(self) -> ModelMetadata:
        return ModelMetadata(
            provider="anthropic",
            model_id=self.model_id,
            context_window=200000,
        )
