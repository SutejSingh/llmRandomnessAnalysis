"""Tests for backend/dummy_data_service.py - get_dummy_data_service, stream_dummy_data_service."""
import asyncio
import json
import os
import tempfile
from pathlib import Path
import pytest
from fastapi import HTTPException
from unittest.mock import patch

from dummy_data_service import get_dummy_data_service, stream_dummy_data_service


class TestGetDummyDataService:
    def test_file_not_found_raises_404(self):
        with pytest.raises(HTTPException) as exc_info:
            get_dummy_data_service("nonexistent_file_12345.json")
        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()

    def test_single_run_format(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump([0.1, 0.2, 0.3], f)
            path = f.name
        try:
            with patch("dummy_data_service.os.path.join", return_value=path):
                with patch("dummy_data_service.os.path.exists", return_value=True):
                    result = get_dummy_data_service(os.path.basename(path))
            assert result["is_multi_run"] is False
            assert result["num_runs"] == 1
            assert result["count_per_run"] == 3
            assert result["data"] == [[0.1, 0.2, 0.3]]
        finally:
            os.unlink(path)

    def test_multi_run_format(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump([[0.1, 0.2], [0.3, 0.4]], f)
            path = f.name
        try:
            with patch("dummy_data_service.os.path.join", return_value=path):
                with patch("dummy_data_service.os.path.exists", return_value=True):
                    result = get_dummy_data_service(os.path.basename(path))
            assert result["is_multi_run"] is True
            assert result["num_runs"] == 2
            assert result["count_per_run"] == 2
            assert result["data"] == [[0.1, 0.2], [0.3, 0.4]]
        finally:
            os.unlink(path)

    def test_invalid_format_raises(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump([], f)
            path = f.name
        try:
            with patch("dummy_data_service.os.path.join", return_value=path):
                with patch("dummy_data_service.os.path.exists", return_value=True):
                    with pytest.raises(HTTPException) as exc_info:
                        get_dummy_data_service(os.path.basename(path))
            assert exc_info.value.status_code == 400
        finally:
            os.unlink(path)

    def test_invalid_json_raises(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("not json {")
            path = f.name
        try:
            with patch("dummy_data_service.os.path.join", return_value=path):
                with patch("dummy_data_service.os.path.exists", return_value=True):
                    with pytest.raises(HTTPException) as exc_info:
                        get_dummy_data_service(os.path.basename(path))
            assert exc_info.value.status_code == 500
        finally:
            os.unlink(path)


class TestStreamDummyDataService:
    @pytest.mark.asyncio
    async def test_file_not_found_returns_error_stream(self):
        with patch("dummy_data_service.os.path.exists", return_value=False):
            with patch("dummy_data_service.os.path.join", return_value="/nonexistent"):
                resp = await stream_dummy_data_service("missing.json")
        assert resp.media_type == "text/event-stream"
        # Consume body to get error event (chunks may be str or bytes)
        parts = []
        async for chunk in resp.body_iterator:
            parts.append(chunk if isinstance(chunk, str) else chunk.decode("utf-8"))
        text = "".join(parts)
        assert "error" in text.lower() or "not found" in text.lower()
        assert "[DONE]" in text
