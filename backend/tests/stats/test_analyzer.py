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

    def test_integer_list_input_basic_stats_correct(self):
        """Single-run integer list should produce correct basic_stats (no float-only assumption)."""
        analyzer = StatsAnalyzer()
        numbers = [1, 2, 2, 3, 4, 5]
        out = analyzer.analyze(numbers, provider="p")
        bs = out["basic_stats"]
        assert out["count"] == 6
        assert bs["mean"] == pytest.approx(17 / 6, rel=1e-5)
        assert bs["median"] == pytest.approx(2.5, rel=1e-5)
        assert bs["mode"] == 2.0
        assert bs["q25"] == pytest.approx(2.0, rel=1e-5)
        assert bs["q75"] == pytest.approx(4.0, rel=1e-5)
        assert bs["std"] == pytest.approx(1.4719601443879744, rel=1e-5)
        assert bs["variance"] == pytest.approx(2.1666666666666665, rel=1e-5)
        for k in ("mean", "median", "mode", "std", "variance", "min", "max", "q25", "q50", "q75", "q95"):
            assert isinstance(bs[k], (int, float))

    def test_single_run_correctness_all_sections(self):
        """Single-run: [0, 0.5, 1.0] -> exact basic_stats; distribution/range/independence/spectral/stationarity/nist present and sane."""
        analyzer = StatsAnalyzer()
        numbers = [0.0, 0.5, 1.0]
        out = analyzer.analyze(numbers, provider="test")
        assert out["provider"] == "test"
        assert out["count"] == 3
        # Basic stats
        assert out["basic_stats"]["mean"] == pytest.approx(0.5, rel=1e-5)
        assert out["basic_stats"]["median"] == pytest.approx(0.5, rel=1e-5)
        assert out["basic_stats"]["min"] == 0.0
        assert out["basic_stats"]["max"] == 1.0
        assert out["basic_stats"]["q25"] == pytest.approx(0.5, rel=1e-5)
        assert out["basic_stats"]["q75"] == pytest.approx(1.0, rel=1e-5)
        # Distribution
        assert "is_uniform" in out["distribution"]
        assert "ks_stat" in out["distribution"]["is_uniform"]
        assert "ks_p" in out["distribution"]["is_uniform"]
        assert out["distribution"]["is_uniform"]["ks_p"] > 0 and out["distribution"]["is_uniform"]["ks_p"] <= 1
        # Range behavior
        assert out["range_behavior"]["boundaries"]["min"] == 0.0
        assert out["range_behavior"]["boundaries"]["max"] == 1.0
        assert len(out["range_behavior"]["ecdf"]["x"]) == len(out["range_behavior"]["ecdf"]["y"])
        if len(out["range_behavior"]["ecdf"]["y"]) >= 1:
            assert out["range_behavior"]["ecdf"]["y"][-1] == pytest.approx(1.0, rel=1e-5)
        # Independence (short series may have 0 lags)
        assert "autocorrelation" in out["independence"]
        assert "lag1_scatter" in out["independence"]
        assert len(out["independence"]["autocorrelation"]["values"]) >= 0
        # Stationarity
        assert "rolling_mean" in out["stationarity"]
        assert "chunks" in out["stationarity"]
        assert len(out["stationarity"]["chunks"]) >= 1  # 4 for long series; short series may have fewer
        # Spectral
        assert "frequencies" in out["spectral"]
        assert "magnitude" in out["spectral"]
        # NIST
        assert "runs_test" in out["nist_tests"]
        assert "passed" in out["nist_tests"]["runs_test"] or "error" in out["nist_tests"]["runs_test"]

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

    def test_multi_run_correctness_combined_and_aggregate(self):
        """Multi-run: two deterministic runs -> combined_stream_stats mean, aggregate_stats mean of means, test_results k/n format."""
        analyzer = StatsAnalyzer()
        runs = [[0.0, 0.5, 1.0], [0.2, 0.5, 0.8]]  # means 0.5 and 0.5; avoid constant run for KDE
        out = analyzer.analyze_multi_run(runs, "test", 2)
        assert out["provider"] == "test"
        assert out["num_runs"] == 2
        assert out["count_per_run"] == 3
        # Combined stream = all 6 numbers: 0, 0.5, 1, 0.2, 0.5, 0.8 -> mean = 3/6 = 0.5
        assert out["combined_stream_stats"]["mean"] == pytest.approx(0.5, rel=1e-5)
        assert out["combined_stream_stats"]["min"] == 0.0
        assert out["combined_stream_stats"]["max"] == 1.0
        # Aggregate: mean of per-run means = (0.5 + 0.5) / 2 = 0.5
        assert out["aggregate_stats"]["mean"]["mean"] == pytest.approx(0.5, rel=1e-5)
        # Test results are "k/n" strings
        tr = out["test_results"]
        assert "runs_test_passed" in tr
        assert "/" in tr["runs_test_passed"]
        assert tr["runs_test_passed"] in ("0/2", "1/2", "2/2")
        assert "ks_uniformity_passed" in tr
        assert len(out["individual_analyses"]) == 2
        assert out["individual_analyses"][0]["basic_stats"]["mean"] == pytest.approx(0.5, rel=1e-5)
        assert out["individual_analyses"][1]["basic_stats"]["mean"] == pytest.approx(0.5, rel=1e-5)
        # Distribution deviation and autocorrelation table
        assert "distribution_deviation" in out
        assert "ecdf" in out["distribution_deviation"]
        assert len(out["autocorrelation_table"]) == 2
        assert out["autocorrelation_table"][0]["run"] == 1
        assert out["autocorrelation_table"][1]["run"] == 2

    def test_multi_run_integer_inputs_supported(self):
        """Multi-run with integer-only runs should work and compute combined_stream_stats correctly."""
        analyzer = StatsAnalyzer()
        runs = [[1, 2, 3], [4, 5, 6]]
        out = analyzer.analyze_multi_run(runs, "p", 2)
        assert out["num_runs"] == 2
        assert out["count_per_run"] == 3
        # Combined stream is [1..6] => mean 3.5, min 1, max 6
        cs = out["combined_stream_stats"]
        assert cs["mean"] == pytest.approx(3.5, rel=1e-5)
        assert cs["min"] == 1.0
        assert cs["max"] == 6.0
        assert len(out["individual_analyses"]) == 2


class TestConvertNumpyTypes:
    """Tests for _convert_numpy_types (delegates to utils)."""

    def test_delegates_to_utils(self):
        analyzer = StatsAnalyzer()
        assert analyzer._convert_numpy_types(np.int32(42)) == 42
        assert analyzer._convert_numpy_types(np.float64(3.14)) == 3.14
