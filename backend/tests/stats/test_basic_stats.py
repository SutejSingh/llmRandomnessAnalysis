"""Tests for backend/stats/basic_stats.py - basic_stats (correctness and edge cases)."""
import numpy as np
import pytest

from stats import basic_stats as basic_stats_mod


class TestBasicStats:
    """Tests for basic_stats."""

    def test_single_element(self):
        arr = np.array([5.0])
        out = basic_stats_mod.basic_stats(arr)
        assert out["mean"] == 5.0
        assert out["median"] == 5.0
        assert out["min"] == 5.0
        assert out["max"] == 5.0
        assert out["std"] == 0.0
        assert out["variance"] == 0.0
        assert "skewness" in out
        assert "kurtosis" in out
        assert "q25" in out
        assert "q75" in out
        assert "q95" in out
        assert "mode" in out

    def test_two_elements(self):
        arr = np.array([1.0, 3.0])
        out = basic_stats_mod.basic_stats(arr)
        assert out["mean"] == 2.0
        assert out["std"] == pytest.approx(1.41421356, rel=1e-5)
        assert out["variance"] == pytest.approx(2.0, rel=1e-5)

    def test_mode_most_frequent(self):
        arr = np.array([1, 2, 2, 3, 3, 3])
        out = basic_stats_mod.basic_stats(arr)
        assert out["mode"] == 3.0  # 3 appears most (3 times)
        assert out["mean"] == pytest.approx(14 / 6, rel=1e-5)  # (1+2+2+3+3+3)/6

    def test_continuous_has_median_mode_quartiles(self):
        arr = np.linspace(0, 100, 101)
        out = basic_stats_mod.basic_stats(arr)
        assert out["mean"] == pytest.approx(50.0, rel=1e-5)
        assert out["median"] == pytest.approx(50.0, rel=1e-5)
        assert out["min"] == 0.0
        assert out["max"] == 100.0
        assert out["q25"] == pytest.approx(25.0, rel=1e-4)
        assert out["q75"] == pytest.approx(75.0, rel=1e-4)

    def test_skewness_and_kurtosis_present(self):
        arr = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        out = basic_stats_mod.basic_stats(arr)
        assert isinstance(out["skewness"], (int, float))
        assert isinstance(out["kurtosis"], (int, float))

    def test_empty_array_raises(self):
        arr = np.array([])
        with pytest.raises(Exception):  # np.mean([]) or percentile can raise
            basic_stats_mod.basic_stats(arr)


class TestBasicStatsCorrectness:
    """Deterministic correctness: known data -> exact expected stats."""

    def test_discrete_run_1_2_2_3_4_5(self):
        """Single-run basic_stats for [1,2,2,3,4,5]: mean, median, mode, q25, q75, std, variance."""
        arr = np.array([1, 2, 2, 3, 4, 5])
        out = basic_stats_mod.basic_stats(arr)
        assert out["mean"] == pytest.approx(17 / 6, rel=1e-5)
        assert out["median"] == pytest.approx(2.5, rel=1e-5)
        assert out["mode"] == 2.0
        assert out["min"] == 1.0
        assert out["max"] == 5.0
        assert out["q25"] == pytest.approx(2.0, rel=1e-5)
        assert out["q75"] == pytest.approx(4.0, rel=1e-5)
        # Sample std/variance (ddof=1)
        assert out["std"] == pytest.approx(1.4719601443879744, rel=1e-5)
        assert out["variance"] == pytest.approx(2.1666666666666665, rel=1e-5)
        assert out["q50"] == pytest.approx(2.5, rel=1e-5)

    def test_integer_input_types_supported(self):
        """Integer array input should be accepted; outputs should be numeric JSON-friendly types."""
        arr = np.array([1, 2, 2, 3, 4, 5], dtype=int)
        out = basic_stats_mod.basic_stats(arr)
        # Values
        assert out["mean"] == pytest.approx(17 / 6, rel=1e-5)
        assert out["median"] == pytest.approx(2.5, rel=1e-5)
        assert out["mode"] == 2.0
        assert out["q25"] == pytest.approx(2.0, rel=1e-5)
        assert out["q75"] == pytest.approx(4.0, rel=1e-5)
        # Types (should serialize cleanly to JSON)
        for k in ("mean", "median", "mode", "std", "variance", "min", "max", "q25", "q50", "q75", "q95"):
            assert isinstance(out[k], (int, float))

    def test_uniform_0_0_5_1(self):
        """Single-run [0, 0.5, 1.0]: mean 0.5, min 0, max 1."""
        arr = np.array([0.0, 0.5, 1.0])
        out = basic_stats_mod.basic_stats(arr)
        assert out["mean"] == pytest.approx(0.5, rel=1e-5)
        assert out["median"] == pytest.approx(0.5, rel=1e-5)
        assert out["min"] == 0.0
        assert out["max"] == 1.0
        assert out["q25"] == pytest.approx(0.5, rel=1e-5)
        assert out["q75"] == pytest.approx(1.0, rel=1e-5)
