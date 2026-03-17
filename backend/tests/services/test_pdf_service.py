"""Tests for backend/pdf_service.py - download_pdf_service (mocked LaTeX)."""
from unittest.mock import MagicMock, patch
import pytest
from fastapi import HTTPException

from pdf_service import download_pdf_service


@pytest.mark.asyncio
async def test_download_pdf_returns_response_when_success():
    mock_generator = MagicMock()
    mock_generator._generate_latex_pdf = MagicMock(return_value=b"%PDF-1.4 fake pdf bytes")
    mock_generator.cleanup = MagicMock()
    analysis = {"provider": "test"}
    with patch("pdf_service.LatexGenerator", return_value=mock_generator):
        with patch("pdf_service.tempfile.mkdtemp", return_value="/tmp/xyz"):
            with patch("pdf_service.os.path.exists", return_value=True):
                with patch("pdf_service.shutil.rmtree"):
                    resp = await download_pdf_service(analysis, mock_generator)
    assert resp.media_type == "application/pdf"
    assert "test" in resp.headers.get("Content-Disposition", "")
    assert resp.body == b"%PDF-1.4 fake pdf bytes" or resp.body[:20] == b"%PDF-1.4 fake pdf "


@pytest.mark.asyncio
async def test_download_pdf_raises_on_latex_error():
    mock_generator = MagicMock()
    mock_generator._generate_latex_pdf = MagicMock(side_effect=RuntimeError("pdflatex not found"))
    mock_generator.cleanup = MagicMock()
    analysis = {"provider": "test"}
    with patch("pdf_service.tempfile.mkdtemp", return_value="/tmp/xyz"):
        with patch("pdf_service.os.path.exists", return_value=True):
            with patch("pdf_service.shutil.rmtree"):
                with pytest.raises(HTTPException) as exc_info:
                    await download_pdf_service(analysis, mock_generator)
    assert exc_info.value.status_code == 500
    assert "PDF" in exc_info.value.detail or "Error" in exc_info.value.detail
