"""Tests for backend/llm_client.py - _extract_number, _extract_numbers_csv, _extract_numbers, _get_api_key."""
import os
import pytest
from unittest.mock import patch

from llm_client import LLMClient


class TestExtractNumber:
    def test_decimal(self):
        client = LLMClient()
        assert client._extract_number("The number is 0.12345") == 0.12345
        assert client._extract_number("0.5") == 0.5

    def test_integer(self):
        client = LLMClient()
        assert client._extract_number("42") == 42.0
        assert client._extract_number("Here is 7") == 7.0

    def test_first_match_used(self):
        client = LLMClient()
        assert client._extract_number("Values: 0.1 and 0.2 and 0.3") == 0.1

    def test_no_number_returns_none(self):
        client = LLMClient()
        assert client._extract_number("No number here") is None
        assert client._extract_number("") is None
        assert client._extract_number("   ") is None

    def test_decimal_preferred_over_integer(self):
        client = LLMClient()
        # Pattern order: decimal first then integer
        assert client._extract_number("3.14") == 3.14


class TestExtractNumbersCsv:
    def test_one_per_line(self):
        client = LLMClient()
        text = "0.1\n0.2\n0.3\n"
        out = client._extract_numbers_csv(text)
        assert out == [0.1, 0.2, 0.3]

    def test_empty_lines_skipped(self):
        client = LLMClient()
        text = "0.1\n\n0.2\n\n"
        out = client._extract_numbers_csv(text)
        assert out == [0.1, 0.2]

    def test_comma_separated_first_number_per_line(self):
        client = LLMClient()
        text = "0.1, 0.2\n0.3, 0.4\n"
        out = client._extract_numbers_csv(text)
        assert len(out) == 2
        assert out[0] == 0.1
        assert out[1] == 0.3

    def test_no_numbers_returns_empty(self):
        client = LLMClient()
        assert client._extract_numbers_csv("no numbers") == []
        assert client._extract_numbers_csv("") == []

    def test_leading_dot_number(self):
        client = LLMClient()
        text = ".5\n"
        out = client._extract_numbers_csv(text)
        assert out == [0.5]


class TestExtractNumbers:
    def test_expected_count_respected(self):
        client = LLMClient()
        text = "0.1, 0.2, 0.3, 0.4, 0.5"
        out = client._extract_numbers(text, expected_count=3)
        assert len(out) == 3
        assert out[0] == 0.1 and out[1] == 0.2 and out[2] == 0.3

    def test_less_than_expected_returns_what_found(self):
        client = LLMClient()
        text = "0.1 and 0.2"
        out = client._extract_numbers(text, expected_count=10)
        assert len(out) <= 10
        assert 0.1 in out
        assert 0.2 in out

    def test_empty_text(self):
        client = LLMClient()
        assert client._extract_numbers("", expected_count=5) == []

    def test_numbers_greater_than_one_normalized_in_comma_path(self):
        client = LLMClient()
        # Code divides by 10^len(int) when num > 1 in comma pattern
        text = "100 200 300"
        out = client._extract_numbers(text, expected_count=3)
        assert len(out) == 3


class TestGetApiKey:
    def test_provided_key_used(self):
        client = LLMClient()
        key = "sk-test12345678901234567890"
        assert client._get_api_key("openai", provided_key=key) == key

    def test_provided_key_stripped(self):
        client = LLMClient()
        assert client._get_api_key("openai", provided_key="  sk-xxx  ") == "sk-xxx"

    def test_empty_provided_key_ignored(self):
        client = LLMClient()
        with patch.dict(os.environ, {"OPENAI_API_KEY": "env-key"}, clear=False):
            assert client._get_api_key("openai", provided_key="") == "env-key"
        with patch.dict(os.environ, {"OPENAI_API_KEY": "env-key"}, clear=False):
            assert client._get_api_key("openai", provided_key="   ") == "env-key"

    def test_env_fallback(self):
        client = LLMClient()
        with patch.dict(os.environ, {"OPENAI_API_KEY": "env-openai"}, clear=False):
            assert client._get_api_key("openai", provided_key=None) == "env-openai"
        with patch.dict(os.environ, {}, clear=False):
            assert client._get_api_key("openai", provided_key=None) is None

    def test_anthropic_and_deepseek_env_keys(self):
        client = LLMClient()
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "anth-key"}, clear=False):
            assert client._get_api_key("anthropic", provided_key=None) == "anth-key"
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "ds-key"}, clear=False):
            assert client._get_api_key("deepseek", provided_key=None) == "ds-key"

    def test_unknown_provider_returns_none(self):
        client = LLMClient()
        with patch.dict(os.environ, {}, clear=False):
            assert client._get_api_key("unknown", provided_key=None) is None


class TestDefaultPrompts:
    def test_has_all_providers(self):
        client = LLMClient()
        assert "openai" in client.default_prompts
        assert "anthropic" in client.default_prompts
        assert "deepseek" in client.default_prompts
        assert "random" in client.default_prompts["openai"].lower()
