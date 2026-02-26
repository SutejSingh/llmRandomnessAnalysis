"""Tests for backend/generation_service.py - generate_numbers_service, generate_numbers_stream_service (mocked LLM)."""
from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi import HTTPException

from models import PromptRequest
from generation_service import generate_numbers_service, generate_numbers_stream_service


@pytest.mark.asyncio
async def test_generate_numbers_service_success():
    mock_client = MagicMock()
    mock_client.generate_random_numbers = AsyncMock(return_value=[0.1, 0.2, 0.3])
    request = PromptRequest(provider="openai", count=3)
    result = await generate_numbers_service(request, mock_client)
    assert result["numbers"] == [0.1, 0.2, 0.3]
    assert result["provider"] == "openai"
    mock_client.generate_random_numbers.assert_called_once()
    call_kw = mock_client.generate_random_numbers.call_args[1]
    assert call_kw["provider"] == "openai"
    assert call_kw["count"] == 3


@pytest.mark.asyncio
async def test_generate_numbers_service_uses_count_default():
    mock_client = MagicMock()
    mock_client.generate_random_numbers = AsyncMock(return_value=[0.5] * 100)
    request = PromptRequest(provider="openai")
    await generate_numbers_service(request, mock_client)
    call_kw = mock_client.generate_random_numbers.call_args[1]
    assert call_kw["count"] == 100


@pytest.mark.asyncio
async def test_generate_numbers_service_raises_on_error():
    mock_client = MagicMock()
    mock_client.generate_random_numbers = AsyncMock(side_effect=ValueError("API key required"))
    request = PromptRequest(provider="openai")
    with pytest.raises(HTTPException) as exc_info:
        await generate_numbers_service(request, mock_client)
    assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_generate_numbers_stream_service_returns_streaming_response():
    async def mock_stream(*a, **k):
        yield 0.1
        yield 0.2
    mock_client = MagicMock()
    mock_client.generate_random_numbers_stream = mock_stream
    request = PromptRequest(provider="openai", count=2)
    resp = await generate_numbers_stream_service(request, mock_client)
    assert resp.media_type == "text/event-stream"
    assert "Cache-Control" in resp.headers
    # Consume a few events
    events = []
    async for chunk in resp.body_iterator:
        events.append(chunk)
        if len(events) >= 4:
            break
    assert len(events) >= 1
    body = "".join(e if isinstance(e, str) else e.decode("utf-8") for e in events)
    assert "data:" in body
