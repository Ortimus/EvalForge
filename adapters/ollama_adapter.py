"""
OllamaAdapter — wraps a locally running Ollama server.
Great for local dev without any API keys.
"""
import requests
from .base import BaseModelAdapter, ModelMetadata


class OllamaAdapter(BaseModelAdapter):

    def __init__(self, model_id: str = "llama3", base_url: str = "http://localhost:11434"):
        self.model_id = model_id
        self.base_url = base_url

    def generate(self, prompt: str, **kwargs) -> str:
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={"model": self.model_id, "prompt": prompt, "stream": False},
        )
        response.raise_for_status()
        return response.json()["response"]

    def get_metadata(self) -> ModelMetadata:
        return ModelMetadata(provider="ollama", model_id=self.model_id)
