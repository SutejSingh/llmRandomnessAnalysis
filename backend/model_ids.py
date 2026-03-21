"""
Allowed LLM model ids per provider (must match frontend constants).
Unknown or missing model uses the provider default.
"""
from typing import Dict, FrozenSet, Optional

# Defaults when `model` is omitted or invalid (invalid raises ValueError from resolver)
DEFAULT_MODELS: Dict[str, str] = {
    "openai": "gpt-5.4",
    "anthropic": "claude-sonnet-4-6",
    "deepseek": "deepseek-chat",
}

ALLOWED_MODELS: Dict[str, FrozenSet[str]] = {
    "openai": frozenset(
        {
            "gpt-5.4",
            "gpt-5.4-nano",
            "gpt-5.4-mini",
            "gpt-5.4-pro",
            "gpt-5-mini",
            "gpt-5-nano",
            "gpt-5",
            "gpt-4.1",
        }
    ),
    "anthropic": frozenset(
        {
            "claude-opus-4-6",
            "claude-sonnet-4-6",
            "claude-haiku-4-5",
            "claude-haiku-4-5-20251001",
            "claude-sonnet-4-5",
            "claude-opus-4-5",
            "claude-opus-4-1",
            "claude-sonnet-4-20250514",
            "claude-opus-4-20250514",
            "claude-3-5-sonnet-20241022",
        }
    ),
    "deepseek": frozenset(
        {
            "deepseek-chat",
            "deepseek-reasoner",
        }
    ),
}


def resolve_model_id(provider: str, model: Optional[str]) -> str:
    """
    Return validated model id for the provider.
    If model is None or blank, return default for provider.
    Raises ValueError if provider is unknown or model is not allowed.
    """
    if provider not in DEFAULT_MODELS:
        raise ValueError(f"Unknown provider: {provider}")
    default = DEFAULT_MODELS[provider]
    if not model or not str(model).strip():
        return default
    mid = str(model).strip()
    allowed = ALLOWED_MODELS.get(provider, frozenset())
    if mid not in allowed:
        raise ValueError(
            f"Invalid model '{mid}' for provider '{provider}'. "
            f"Allowed: {sorted(allowed)}"
        )
    return mid
