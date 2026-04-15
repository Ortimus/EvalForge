"""
HuggingFaceAdapter — wraps a local HuggingFace pipeline.
"""
from .base import BaseModelAdapter, ModelMetadata


class HuggingFaceAdapter(BaseModelAdapter):

    def __init__(self, model_id: str, device: str = "cpu"):
        from transformers import pipeline
        self.model_id = model_id
        self.pipe = pipeline("text-generation", model=model_id, device=device)

    def generate(self, prompt: str, max_new_tokens: int = 512, **kwargs) -> str:
        output = self.pipe(prompt, max_new_tokens=max_new_tokens, return_full_text=False)
        return output[0]["generated_text"]

    def get_metadata(self) -> ModelMetadata:
        return ModelMetadata(provider="huggingface", model_id=self.model_id)
