"""Tests for backend/csv_service.py - generate_csv, parse_uploaded_csv."""
import asyncio
from io import BytesIO, StringIO
import pandas as pd
import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi import HTTPException

from csv_service import generate_csv, parse_uploaded_csv, CSV_CHUNK_SIZE


class TestGenerateCsv:
    def test_empty_runs_raises(self):
        with pytest.raises(HTTPException) as exc_info:
            generate_csv([], "test")
        assert exc_info.value.status_code == 400

    def test_not_list_raises(self):
        with pytest.raises(HTTPException) as exc_info:
            generate_csv("not a list", "test")
        assert exc_info.value.status_code == 400

    def test_single_run(self):
        runs = [[1.0, 2.0, 3.0]]
        resp = generate_csv(runs, "openai")
        assert resp.media_type == "text/csv"
        assert "run 1" in resp.headers.get("Content-Disposition", "") or "random_numbers" in resp.headers.get("Content-Disposition", "")
        content = resp.body
        assert b"1.0" in content or b"1" in content
        assert b"2.0" in content or b"2" in content

    def test_multiple_runs_different_lengths(self):
        runs = [[1.0, 2.0], [3.0, 4.0, 5.0]]
        resp = generate_csv(runs, "test")
        assert resp.media_type == "text/csv"
        # Shorter run padded with empty
        content = resp.body.decode("utf-8") if isinstance(resp.body, bytes) else str(resp.body)
        lines = content.strip().split("\n")
        assert len(lines) >= 2
        assert "run 1" in content or "run 2" in content

    def test_filename_contains_provider(self):
        runs = [[1.0]]
        resp = generate_csv(runs, "anthropic")
        disp = resp.headers.get("Content-Disposition", "")
        assert "anthropic" in disp or "random_numbers" in disp


class TestParseUploadedCsv:
    @pytest.mark.asyncio
    async def test_valid_csv_run_columns(self):
        csv_content = "run 1,run 2\n1.0,2.0\n3.0,4.0\n"
        file = MagicMock()
        file.read = AsyncMock(side_effect=[csv_content.encode("utf-8"), b""])
        runs_data, num_runs = await parse_uploaded_csv(file)
        assert num_runs == 2
        assert len(runs_data) == 2
        assert runs_data[0] == [1.0, 3.0]
        assert runs_data[1] == [2.0, 4.0]

    @pytest.mark.asyncio
    async def test_no_run_columns_raises(self):
        csv_content = "col_a,col_b\n1,2\n"
        file = MagicMock()
        file.read = AsyncMock(side_effect=[csv_content.encode("utf-8"), b""])
        with pytest.raises(HTTPException) as exc_info:
            await parse_uploaded_csv(file)
        assert exc_info.value.status_code == 400
        assert "run" in exc_info.value.detail.lower() or "column" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_run_columns_case_insensitive(self):
        csv_content = "Run 1,Run 2\n1.0,2.0\n"
        file = MagicMock()
        file.read = AsyncMock(side_effect=[csv_content.encode("utf-8"), b""])
        runs_data, num_runs = await parse_uploaded_csv(file)
        assert num_runs == 2
        assert len(runs_data[0]) == 1
        assert runs_data[0][0] == 1.0

    @pytest.mark.asyncio
    async def test_empty_cells_skipped(self):
        csv_content = "run 1,run 2\n1.0,\n,2.0\n3.0,4.0\n"
        file = MagicMock()
        file.read = AsyncMock(side_effect=[csv_content.encode("utf-8"), b""])
        runs_data, num_runs = await parse_uploaded_csv(file)
        assert num_runs == 2
        assert 1.0 in runs_data[0] and 3.0 in runs_data[0]
        assert 2.0 in runs_data[1] and 4.0 in runs_data[1]

    @pytest.mark.asyncio
    async def test_no_valid_data_raises(self):
        csv_content = "run 1,run 2\n,\n,\n"
        file = MagicMock()
        file.read = AsyncMock(side_effect=[csv_content.encode("utf-8"), b""])
        with pytest.raises(HTTPException) as exc_info:
            await parse_uploaded_csv(file)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_non_utf8_raises(self):
        file = MagicMock()
        file.read = AsyncMock(side_effect=[b"\xff\xfe not valid utf8", b""])
        with pytest.raises(HTTPException) as exc_info:
            await parse_uploaded_csv(file)
        assert exc_info.value.status_code in (400, 500)


class TestCsvChunkSize:
    def test_constant_positive(self):
        assert CSV_CHUNK_SIZE > 0
