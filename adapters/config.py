"""
Config loader — reads configs/models.yaml and configs/scoring.yaml.
Kept dependency-free (just yaml + pathlib) so any layer can import it.
"""
from __future__ import annotations
from functools import lru_cache
from pathlib import Path
import yaml

CONFIGS_DIR = Path(__file__).parent.parent / "configs"


@lru_cache(maxsize=None)
def _load(name: str) -> dict:
    return yaml.safe_load((CONFIGS_DIR / name).read_text()) or {}


def provider_config(provider: str) -> dict:
    """Return the config block for a provider ({} if the provider is unknown)."""
    return _load("models.yaml").get("providers", {}).get(provider, {})


def default_model(provider: str) -> str | None:
    return provider_config(provider).get("default")


def list_models() -> dict[str, list[str]]:
    """provider -> known model IDs. Intended for UI dropdowns."""
    return {
        p: cfg.get("models", [])
        for p, cfg in _load("models.yaml").get("providers", {}).items()
    }


def judge_config() -> dict:
    return _load("scoring.yaml").get("judge", {})
