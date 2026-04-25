"""
Smoke Test: Model Adapters
Run from EvalForge/ root: python3 tests/smoke/smoke_adapters.py

Tests whichever adapters you have credentials/services for.
Skips gracefully if keys are missing.
"""
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")

print("=" * 50)
print("Model Adapters — Smoke Test")
print("=" * 50)

PROMPT = "Say hello in exactly 5 words."

# --- Anthropic ---
anthropic_key = os.getenv("ANTHROPIC_API_KEY")
if anthropic_key:
    from adapters.anthropic_adapter import AnthropicAdapter
    print("\n[AnthropicAdapter]")
    adapter = AnthropicAdapter(api_key=anthropic_key)
    print(f"  Metadata: {adapter.get_metadata()}")
    response = adapter.generate(PROMPT)
    print(f"  Response: {response}")
    assert isinstance(response, str) and len(response) > 0
    print("  ✅ Passed")
else:
    print("\n[AnthropicAdapter] ⏭️  Skipped — ANTHROPIC_API_KEY not set")

# --- OpenAI ---
openai_key = os.getenv("OPENAI_API_KEY")
if openai_key:
    from adapters.openai_adapter import OpenAIAdapter
    print("\n[OpenAIAdapter]")
    adapter = OpenAIAdapter(api_key=openai_key)
    print(f"  Metadata: {adapter.get_metadata()}")
    response = adapter.generate(PROMPT)
    print(f"  Response: {response}")
    assert isinstance(response, str) and len(response) > 0
    print("  ✅ Passed")
else:
    print("\n[OpenAIAdapter] ⏭️  Skipped — OPENAI_API_KEY not set")

# --- Ollama (local) ---
import requests
try:
    requests.get("http://localhost:11434", timeout=2)
    ollama_available = True
except Exception:
    ollama_available = False

if ollama_available:
    from adapters.ollama_adapter import OllamaAdapter
    print("\n[OllamaAdapter]")
    adapter = OllamaAdapter()
    print(f"  Metadata: {adapter.get_metadata()}")
    response = adapter.generate(PROMPT)
    print(f"  Response: {response}")
    assert isinstance(response, str) and len(response) > 0
    print("  ✅ Passed")
else:
    print("\n[OllamaAdapter] ⏭️  Skipped — Ollama not running on localhost:11434")

print("\n✅ Adapter smoke tests complete.\n")
