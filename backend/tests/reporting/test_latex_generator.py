"""Tests for backend/reporting/latex_generator.py - escape_latex, get_status, is_ready, get_error, _normalize_analysis_to_multi_run."""
from unittest.mock import MagicMock, patch
import pytest

from reporting.latex_generator import LatexGenerator


class TestLatexGeneratorStatus:
    def test_initial_status_pending(self):
        gen = LatexGenerator()
        assert gen.get_status() == "pending"
        assert gen.is_ready() is False
        assert gen.get_error() is None
        assert gen.get_pdf_bytes() is None

    def test_escape_latex_static(self):
        out = LatexGenerator.escape_latex("a & b")
        assert "&" not in out or "\\" in out
        assert out != "a & b"


class TestNormalizeAnalysisToMultiRun:
    def test_empty_analysis_returns_unchanged(self):
        gen = LatexGenerator()
        assert gen._normalize_analysis_to_multi_run({}, None) == {}
        assert gen._normalize_analysis_to_multi_run(None, None) is None

    def test_already_multi_run_returns_unchanged(self):
        gen = LatexGenerator()
        analysis = {
            "individual_analyses": [{"basic_stats": {}}],
            "aggregate_stats": {"mean": {}},
        }
        out = gen._normalize_analysis_to_multi_run(analysis, None)
        assert out is analysis
        assert out["individual_analyses"] == [{"basic_stats": {}}]

    def test_single_run_normalized_to_multi_run_structure(self):
        gen = LatexGenerator()
        analysis = {
            "basic_stats": {"mean": 0.5, "mode": 0.5, "std": 0.29, "min": 0.0, "max": 1.0, "median": 0.5, "variance": 0.08, "q25": 0.25, "q75": 0.75, "q95": 0.95, "skewness": 0, "kurtosis": 0},
            "distribution": {"is_uniform": {"ks_p": 0.1, "ks_stat": 0.1}},
            "nist_tests": {"runs_test": {"passed": True}, "binary_matrix_rank_test": {"passed": False}, "longest_run_of_ones_test": {"passed": True}, "approximate_entropy_test": {"passed": True}},
            "range_behavior": {"ecdf": {"x": [0, 0.5, 1], "y": [0, 0.5, 1]}},
            "independence": {"autocorrelation": {"lags": [1], "values": [0.1]}},
        }
        out = gen._normalize_analysis_to_multi_run(analysis, None)
        assert out["num_runs"] == 1
        assert "test_results" in out
        assert "aggregate_stats" in out
        assert "individual_analyses" in out
        assert len(out["individual_analyses"]) == 1
        assert "autocorrelation_table" in out
        assert "ecdf_all_runs" in out
        assert "frequency_histogram" in out

    def test_nan_mode_handled(self):
        gen = LatexGenerator()
        analysis = {
            "basic_stats": {"mean": 0.5, "mode": float("nan"), "std": 0.29, "min": 0.0, "max": 1.0, "median": 0.5, "variance": 0.08, "q25": 0.25, "q75": 0.75, "q95": 0.95, "skewness": 0, "kurtosis": 0},
            "distribution": {"is_uniform": {"ks_p": 0.05}},
            "nist_tests": {},
            "range_behavior": {"ecdf": {}},
            "independence": {"autocorrelation": {"lags": [], "values": []}},
        }
        out = gen._normalize_analysis_to_multi_run(analysis, None)
        assert out["aggregate_stats"]["mode"]["mean"] == 0


class TestCleanup:
    def test_cleanup_does_not_raise(self):
        gen = LatexGenerator()
        gen.cleanup()
        gen.cleanup()
