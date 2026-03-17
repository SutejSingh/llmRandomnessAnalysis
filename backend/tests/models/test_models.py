"""Tests for backend/models.py - Pydantic models validation."""
import pytest
from pydantic import ValidationError

from models import (
    PromptRequest,
    NumberData,
    MultiRunData,
    PDFDownloadRequest,
    CSVDownloadRequest,
)


class TestPromptRequest:
    def test_required_provider(self):
        r = PromptRequest(provider="openai")
        assert r.provider == "openai"
        assert r.count is None or r.count == 100
        assert r.system_prompt is None
        assert r.batch_mode is None or r.batch_mode is False

    def test_optional_fields(self):
        r = PromptRequest(
            provider="anthropic",
            system_prompt="You are helpful.",
            user_prompt="Hi",
            count=50,
            api_key="sk-xxx",
            batch_mode=True,
        )
        assert r.provider == "anthropic"
        assert r.system_prompt == "You are helpful."
        assert r.user_prompt == "Hi"
        assert r.count == 50
        assert r.api_key == "sk-xxx"
        assert r.batch_mode is True

    def test_missing_provider_raises(self):
        with pytest.raises(ValidationError):
            PromptRequest()


class TestNumberData:
    def test_valid(self):
        d = NumberData(numbers=[0.1, 0.2, 0.3], provider="openai")
        assert d.numbers == [0.1, 0.2, 0.3]
        assert d.provider == "openai"

    def test_empty_numbers_allowed(self):
        d = NumberData(numbers=[], provider="test")
        assert d.numbers == []

    def test_missing_provider_raises(self):
        with pytest.raises(ValidationError):
            NumberData(numbers=[1.0])

    def test_missing_numbers_raises(self):
        with pytest.raises(ValidationError):
            NumberData(provider="test")


class TestMultiRunData:
    def test_valid(self):
        d = MultiRunData(
            runs=[[0.1, 0.2], [0.3, 0.4]],
            provider="openai",
            num_runs=2,
        )
        assert len(d.runs) == 2
        assert d.provider == "openai"
        assert d.num_runs == 2

    def test_missing_field_raises(self):
        with pytest.raises(ValidationError):
            MultiRunData(runs=[[1.0]], provider="p")
        with pytest.raises(ValidationError):
            MultiRunData(runs=[[1.0]], num_runs=1)

    def test_runs_must_be_list_of_lists(self):
        with pytest.raises(ValidationError):
            MultiRunData(runs=[1, 2, 3], provider="p", num_runs=1)


class TestPDFDownloadRequest:
    def test_valid(self):
        d = PDFDownloadRequest(analysis={"provider": "test", "count": 100})
        assert d.analysis["provider"] == "test"

    def test_empty_analysis_allowed(self):
        d = PDFDownloadRequest(analysis={})
        assert d.analysis == {}


class TestCSVDownloadRequest:
    def test_valid(self):
        d = CSVDownloadRequest(runs=[[1.0, 2.0]], provider="manual")
        assert len(d.runs) == 1
        assert d.provider == "manual"

    def test_default_provider(self):
        d = CSVDownloadRequest(runs=[])
        assert d.provider == "manual"
