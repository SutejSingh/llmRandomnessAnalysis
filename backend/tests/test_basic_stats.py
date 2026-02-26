"""Tests for backend/stats/basic_stats.py - is_integer_like, mode_discrete, mode_continuous, basic_stats."""
import numpy as np
import pytest

from stats import basic_stats as basic_stats_mod


class TestIsIntegerLike:
    """Tests for is_integer_like."""

    def test_empty_array_returns_false(self):
        assert basic_stats_mod.is_integer_like(np.array([])) is False

    def test_integers_return_true(self):
        assert basic_stats_mod.is_integer_like(np.array([1, 2, 3])) == True
        assert basic_stats_mod.is_integer_like(np.array([0])) == True

    def test_whole_number_floats_return_true(self):
        assert basic_stats_mod.is_integer_like(np.array([1.0, 2.0, 3.0])) == True
        assert basic_stats_mod.is_integer_like(np.array([0.0])) == True

    def test_non_integer_floats_return_false(self):
        assert basic_stats_mod.is_integer_like(np.array([1.5, 2.0])) == False
        assert basic_stats_mod.is_integer_like(np.array([0.1])) == False

    def test_nan_returns_false(self):
        assert basic_stats_mod.is_integer_like(np.array([1.0, np.nan])) is False
        assert basic_stats_mod.is_integer_like(np.array([np.nan])) is False

    def test_inf_returns_false(self):
        assert basic_stats_mod.is_integer_like(np.array([1.0, np.inf])) is False
        assert basic_stats_mod.is_integer_like(np.array([-np.inf, 1])) is False

    def test_mixed_list_with_float_casted(self):
        arr = np.array([1, 2, 3.0])
        assert basic_stats_mod.is_integer_like(arr) == True


class TestModeDiscrete:
    """Tests for mode_discrete."""

    def test_empty_returns_nan(self):
        result = basic_stats_mod.mode_discrete(np.array([]))
        assert np.isnan(result)

    def test_single_value(self):
        assert basic_stats_mod.mode_discrete(np.array([5])) == 5.0

    def test_most_frequent_wins(self):
        arr = np.array([1, 2, 2, 3])
        assert basic_stats_mod.mode_discrete(arr) == 2.0

    def test_tie_break_smallest(self):
        arr = np.array([3, 1, 2, 1, 2, 3])  # 1,2,3 each twice
        assert basic_stats_mod.mode_discrete(arr) == 1.0

    def test_all_same(self):
        arr = np.array([7, 7, 7])
        assert basic_stats_mod.mode_discrete(arr) == 7.0

    def test_float_integers(self):
        arr = np.array([1.0, 2.0, 2.0])
        assert basic_stats_mod.mode_discrete(arr) == 2.0


class TestModeContinuous:
    """Tests for mode_continuous."""

    def test_empty_returns_nan(self):
        result = basic_stats_mod.mode_continuous(np.array([]))
        assert np.isnan(result)

    def test_single_value(self):
        arr = np.array([3.14])
        result = basic_stats_mod.mode_continuous(arr)
        assert result == 3.14

    def test_returns_bin_midpoint(self):
        # Data clustered in one bin
        arr = np.array([0.5] * 10 + [0.1] * 2 + [0.9] * 2)
        result = basic_stats_mod.mode_continuous(arr, bins=5)
        assert 0 <= result <= 1
        assert not np.isnan(result)

    def test_uniform_data_returns_bin_midpoint(self):
        arr = np.array([1.0, 2.0, 3.0])
        result = basic_stats_mod.mode_continuous(arr, bins=3)
        assert 1.0 <= result <= 3.0
        assert not np.isnan(result)

    def test_bins_respected(self):
        arr = np.linspace(0, 1, 100)
        result = basic_stats_mod.mode_continuous(arr, bins=10)
        assert 0 <= result <= 1
        assert not np.isnan(result)

    def test_bins_capped_by_len(self):
        arr = np.array([1.0, 2.0])
        result = basic_stats_mod.mode_continuous(arr, bins=100)
        # bins=min(50, max(1, 2)) = 2
        assert not np.isnan(result)


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

    def test_discrete_uses_discrete_mode_and_percentiles(self):
        arr = np.array([1, 2, 2, 3, 3, 3])
        out = basic_stats_mod.basic_stats(arr)
        assert out["mode"] == 3.0  # 3 appears most (3 times)
        assert out["mean"] == pytest.approx(14/6, rel=1e-5)  # (1+2+2+3+3+3)/6

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
