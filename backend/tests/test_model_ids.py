"""Tests for backend/model_ids.py - resolve_model_id."""
import pytest

from model_ids import DEFAULT_MODELS, resolve_model_id


def test_default_when_empty():
    assert resolve_model_id("openai", None) == DEFAULT_MODELS["openai"]
    assert resolve_model_id("openai", "") == DEFAULT_MODELS["openai"]
    assert resolve_model_id("openai", "   ") == DEFAULT_MODELS["openai"]


def test_valid_explicit():
    assert resolve_model_id("openai", "gpt-4.1") == "gpt-4.1"
    assert resolve_model_id("anthropic", "claude-opus-4-6") == "claude-opus-4-6"
    assert resolve_model_id("deepseek", "deepseek-reasoner") == "deepseek-reasoner"


def test_invalid_model():
    with pytest.raises(ValueError, match="Invalid model"):
        resolve_model_id("openai", "not-a-real-model")


def test_unknown_provider():
    with pytest.raises(ValueError, match="Unknown provider"):
        resolve_model_id("unknown", "gpt-5.4")
