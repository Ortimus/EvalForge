from types import SimpleNamespace as NS

from adapters.anthropic_adapter import AnthropicAdapter
from adapters.config import provider_config


def test_max_tokens_comes_from_models_yaml_and_can_be_overridden():
    seen = {}

    class FakeMessages:
        def create(self, **kw):
            seen.update(kw)
            return NS(content=[NS(type="text", text="ok")], stop_reason="end_turn")

    adapter = AnthropicAdapter(model_id="claude-haiku-5-5", api_key="x")
    adapter.client = NS(messages=FakeMessages())

    adapter.generate("hi")
    assert seen["max_tokens"] == provider_config("anthropic")["max_tokens"] >= 4096
    adapter.generate("hi", max_tokens=123)
    assert seen["max_tokens"] == 123
