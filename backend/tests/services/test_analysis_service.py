"""Tests for backend/analysis_service.py - analyze_numbers_service."""
import json
from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi import HTTPException
from var_names import *

from stats import StatsAnalyzer
from analysis_service import analyze_numbers_service


def _make_request(body: dict):
    request = MagicMock()
    request.json = AsyncMock(return_value=body)
    return request


@pytest.mark.asyncio
async def test_single_run_analysis():
    request = _make_request({
        NUMBERS: [1,2,2,3,4,5],
        PROVIDER: "openai",
    })
    analyzer = StatsAnalyzer()
    result = await analyze_numbers_service(request, analyzer)
    assert result[PROVIDER] == "openai"
    assert result[COUNT] == 6
    assert BASIC_STATS in result

    assert result[BASIC_STATS].get(MEAN) is not None
    assert result[BASIC_STATS][MEAN] == pytest.approx(17 / 6, rel=1e-5)  # (1+2+2+3+4+5)/6

    assert result[BASIC_STATS].get(MEDIAN) is not None
    assert result[BASIC_STATS][MEDIAN] == pytest.approx(2.5, rel=1e-5)

    assert result[BASIC_STATS][MODE] == 2.0
    # Sample std/variance (ddof=1)
    assert result[BASIC_STATS][STANDARD_DEV] == pytest.approx(1.4719601443879744, rel=1e-5)
    assert result[BASIC_STATS][VARIANCE] == pytest.approx(2.1666666666666665, rel=1e-5)
    assert result[BASIC_STATS][MIN] == 1.0
    assert result[BASIC_STATS][MAX] == 5.0
    assert result[BASIC_STATS][Q25] == pytest.approx(2.0, rel=1e-5)
    assert result[BASIC_STATS][Q75] == pytest.approx(4.0, rel=1e-5)

@pytest.mark.asyncio
async def test_multi_run_analysis():
    request = _make_request({
        RUNS: [
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6],
        ],
        PROVIDER: "test",
        NUM_RUNS: 2,
    })
    analyzer = StatsAnalyzer()
    result = await analyze_numbers_service(request, analyzer)
    assert result[PROVIDER] == "test"
    assert result[NUM_RUNS] == 2
    assert "aggregate_stats" in result
    assert len(result["individual_analyses"]) == 2


@pytest.mark.asyncio
async def test_empty_numbers_raises():
    request = _make_request({NUMBERS: [], PROVIDER: "test"})
    analyzer = StatsAnalyzer()
    with pytest.raises(HTTPException) as exc_info:
        await analyze_numbers_service(request, analyzer)
    assert exc_info.value.status_code == 400
    assert "empty" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_empty_runs_raises():
    request = _make_request({RUNS: [], PROVIDER: "test", NUM_RUNS: 0})
    analyzer = StatsAnalyzer()
    with pytest.raises(HTTPException) as exc_info:
        await analyze_numbers_service(request, analyzer)
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_numbers_not_list_raises():
    request = _make_request({NUMBERS: "not a list", PROVIDER: "test"})
    analyzer = StatsAnalyzer()
    with pytest.raises(HTTPException) as exc_info:
        await analyze_numbers_service(request, analyzer)
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_runs_not_list_raises():
    request = _make_request({RUNS: "not a list", PROVIDER: "test", NUM_RUNS: 1})
    analyzer = StatsAnalyzer()
    with pytest.raises(HTTPException) as exc_info:
        await analyze_numbers_service(request, analyzer)
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_missing_numbers_and_runs_raises():
    request = _make_request({PROVIDER: "test"})
    analyzer = StatsAnalyzer()
    with pytest.raises(HTTPException) as exc_info:
        await analyze_numbers_service(request, analyzer)
    assert exc_info.value.status_code == 400
    assert RUNS in exc_info.value.detail.lower() or NUMBERS in exc_info.value.detail.lower()


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
        RUNS: [[1.0, 2.0]],
        PROVIDER: "test",
        NUM_RUNS: 99,
    })
    analyzer = StatsAnalyzer()
    result = await analyze_numbers_service(request, analyzer)
    assert result[NUM_RUNS] == 99
    assert len(result["individual_analyses"]) == 1
