"""
OpenAIAdapter — wraps the OpenAI Chat Completions API.
"""
from openai import OpenAI
from .base import BaseModelAdapter, ModelMetadata


class OpenAIAdapter(BaseModelAdapter):

    def __init__(self, model_id: str = "gpt-4o", api_key: str | None = None):
        self.model_id = model_id
        self.client = OpenAI(api_key=api_key)

    def generate(self, prompt: str, max_tokens: int = 1024, **kwargs) -> str:
        response = self.client.chat.completions.create(
            model=self.model_id,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content

    def get_metadata(self) -> ModelMetadata:
        return ModelMetadata(provider="openai", model_id=self.model_id)
