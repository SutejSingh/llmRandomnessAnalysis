"""Tests for backend/analysis_service.py - analyze_numbers_service."""
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi import HTTPException

from stats import StatsAnalyzer
from analysis_service import analyze_numbers_service


def _make_request(body: dict):
    request = MagicMock()
    request.json = AsyncMock(return_value=body)
    return request


@pytest.mark.asyncio
async def test_single_run_analysis():
    request = _make_request({
        "numbers": [1,2,2,3,4,5],
        "provider": "openai",
    })
    analyzer = StatsAnalyzer()
    result = await analyze_numbers_service(request, analyzer)
    assert result["provider"] == "openai"
    assert result["count"] == 6
    assert "basic_stats" in result

    assert result["basic_stats"].get("mean") is not None
    assert result["basic_stats"]["mean"] == pytest.approx(2.83, rel=1e-5)

    assert result["basic_stats"].get("median") is not None
    assert result["basic_stats"]["median"] == pytest.approx(2.5, rel=1e-5)

    assert result["basic_stats"]["mode"] == 2.0
    assert result["basic_stats"]["std"] == pytest.approx(1.41421356, rel=1e-5)
    assert result["basic_stats"]["variance"] == pytest.approx(2.0, rel=1e-5)
    assert result["basic_stats"]["min"] == 1.0
    assert result["basic_stats"]["max"] == 5.0
    assert result["basic_stats"]["q25"] == pytest.approx(2.0, rel=1e-5)
    assert result["basic_stats"]["q75"] == pytest.approx(4.0, rel=1e-5)

@pytest.mark.asyncio
async def test_multi_run_analysis():
    request = _make_request({
        "runs": [
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6],
        ],
        "provider": "test",
        "num_runs": 2,
    })
    analyzer = StatsAnalyzer()
    result = await analyze_numbers_service(request, analyzer)
    assert result["provider"] == "test"
    assert result["num_runs"] == 2
    assert "aggregate_stats" in result
    assert len(result["individual_analyses"]) == 2


@pytest.mark.asyncio
async def test_empty_numbers_raises():
    request = _make_request({"numbers": [], "provider": "test"})
    analyzer = StatsAnalyzer()
    with pytest.raises(HTTPException) as exc_info:
        await analyze_numbers_service(request, analyzer)
    assert exc_info.value.status_code == 400
    assert "empty" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_empty_runs_raises():
    request = _make_request({"runs": [], "provider": "test", "num_runs": 0})
    analyzer = StatsAnalyzer()
    with pytest.raises(HTTPException) as exc_info:
        await analyze_numbers_service(request, analyzer)
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_numbers_not_list_raises():
    request = _make_request({"numbers": "not a list", "provider": "test"})
    analyzer = StatsAnalyzer()
    with pytest.raises(HTTPException) as exc_info:
        await analyze_numbers_service(request, analyzer)
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_runs_not_list_raises():
    request = _make_request({"runs": "not a list", "provider": "test", "num_runs": 1})
    analyzer = StatsAnalyzer()
    with pytest.raises(HTTPException) as exc_info:
        await analyze_numbers_service(request, analyzer)
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_missing_numbers_and_runs_raises():
    request = _make_request({"provider": "test"})
    analyzer = StatsAnalyzer()
    with pytest.raises(HTTPException) as exc_info:
        await analyze_numbers_service(request, analyzer)
    assert exc_info.value.status_code == 400
    assert "runs" in exc_info.value.detail.lower() or "numbers" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_invalid_json_raises():
    request = MagicMock()
    request.json = AsyncMock(side_effect=json.JSONDecodeError("err", "doc", 0))
    analyzer = StatsAnalyzer()
    with pytest.raises(HTTPException) as exc_info:
        await analyze_numbers_service(request, analyzer)
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_multi_run_validation_error_raises():
    request = _make_request({
        "runs": [[1.0, 2.0]],
        "provider": "test",
        "num_runs": 99,
    })
    analyzer = StatsAnalyzer()
    result = await analyze_numbers_service(request, analyzer)
    assert result["num_runs"] == 99
    assert len(result["individual_analyses"]) == 1
