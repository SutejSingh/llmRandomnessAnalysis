"""Tests for backend/stats/analyzer.py - StatsAnalyzer.analyze, analyze_multi_run, _convert_numpy_types."""
import numpy as np
import pytest

from stats.analyzer import StatsAnalyzer


class TestStatsAnalyzerAnalyze:
    """Tests for StatsAnalyzer.analyze."""

    def test_returns_all_sections(self):
        analyzer = StatsAnalyzer()
        numbers = list(np.random.uniform(0, 1, 100))
        out = analyzer.analyze(numbers, provider="test")
        assert out["provider"] == "test"
        assert out["count"] == 100
        assert "basic_stats" in out
        assert "distribution" in out
        assert "range_behavior" in out
        assert "independence" in out
        assert "stationarity" in out
        assert "spectral" in out
        assert "nist_tests" in out
        assert "raw_data" not in out

    def test_basic_stats_native_types(self):
        analyzer = StatsAnalyzer()
        numbers = [0.1, 0.2, 0.3, 0.4, 0.5]
        out = analyzer.analyze(numbers, provider="p")
        mean = out["basic_stats"]["mean"]
        assert isinstance(mean, (int, float)) or hasattr(mean, "__float__")
        assert mean == pytest.approx(0.3, rel=1e-5)

    def test_two_numbers(self):
        analyzer = StatsAnalyzer()
        out = analyzer.analyze([0.25, 0.75], provider="p")
        assert out["count"] == 2
        assert out["basic_stats"]["mean"] == pytest.approx(0.5, rel=1e-5)
        assert out["basic_stats"]["min"] == pytest.approx(0.25, rel=1e-5)
        assert out["basic_stats"]["max"] == pytest.approx(0.75, rel=1e-5)

    def test_empty_list_raises_or_errors(self):
        analyzer = StatsAnalyzer()
        with pytest.raises(Exception):
            analyzer.analyze([], provider="p")


class TestStatsAnalyzerAnalyzeMultiRun:
    """Tests for StatsAnalyzer.analyze_multi_run."""

    def test_no_runs_raises(self):
        analyzer = StatsAnalyzer()
        with pytest.raises(ValueError, match="No runs provided"):
            analyzer.analyze_multi_run([], "p", 0)

    def test_empty_run_raises(self):
        analyzer = StatsAnalyzer()
        with pytest.raises(ValueError, match="Run 1 is empty"):
            analyzer.analyze_multi_run([[]], "p", 1)
        with pytest.raises(ValueError, match="Run 2 is empty"):
            analyzer.analyze_multi_run([[1.0, 2.0], []], "p", 2)

    def test_non_numeric_in_run_raises(self):
        analyzer = StatsAnalyzer()
        with pytest.raises(ValueError, match="non-numeric"):
            analyzer.analyze_multi_run([[1.0, "x", 2.0]], "p", 1)

    def test_valid_multi_run_structure(self):
        analyzer = StatsAnalyzer()
        runs = [
            list(np.random.uniform(0, 1, 50)),
            list(np.random.uniform(0, 1, 50)),
        ]
        out = analyzer.analyze_multi_run(runs, "test", 2)
        assert out["provider"] == "test"
        assert out["num_runs"] == 2
        assert out["count_per_run"] == 50
        assert "aggregate_stats" in out
        assert "combined_stream_stats" in out
        assert "distribution_deviation" in out
        assert "test_results" in out
        assert "autocorrelation_table" in out
        assert "ecdf_all_runs" in out
        assert "frequency_histogram" in out
        assert "combined_kde" in out
        assert "individual_analyses" in out
        assert len(out["individual_analyses"]) == 2

    def test_test_results_counts(self):
        analyzer = StatsAnalyzer()
        runs = [list(np.random.uniform(0, 1, 200)) for _ in range(3)]
        out = analyzer.analyze_multi_run(runs, "p", 3)
        tr = out["test_results"]
        assert "ks_uniformity_passed" in tr
        assert "runs_test_passed" in tr
        assert "3/3" in tr["ks_uniformity_passed"] or "0/3" in tr["ks_uniformity_passed"] or "1/3" in tr["ks_uniformity_passed"] or "2/3" in tr["ks_uniformity_passed"]

    def test_individual_analyses_native_types(self):
        analyzer = StatsAnalyzer()
        runs = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
        out = analyzer.analyze_multi_run(runs, "p", 2)
        for ind in out["individual_analyses"]:
            assert "basic_stats" in ind
            assert isinstance(ind["basic_stats"]["mean"], (int, float))

    def test_single_run_multi_run(self):
        analyzer = StatsAnalyzer()
        runs = [list(np.random.uniform(0, 1, 30))]
        out = analyzer.analyze_multi_run(runs, "p", 1)
        assert out["num_runs"] == 1
        assert len(out["individual_analyses"]) == 1
        assert out["count_per_run"] == 30


class TestConvertNumpyTypes:
    """Tests for _convert_numpy_types (delegates to utils)."""

    def test_delegates_to_utils(self):
        analyzer = StatsAnalyzer()
        assert analyzer._convert_numpy_types(np.int32(42)) == 42
        assert analyzer._convert_numpy_types(np.float64(3.14)) == 3.14
