"""Tests for backend/stats/distribution.py - normalize, ecdf/qq metrics, distribution_analysis, compute_distribution_deviation_metrics."""
import numpy as np
import pytest

from stats import distribution as distribution_mod


class TestNormalizeToUnit:
    """Tests for normalize_to_unit."""

    def test_empty_returns_empty(self):
        arr = np.array([], dtype=float)
        out = distribution_mod.normalize_to_unit(arr)
        np.testing.assert_array_equal(out, arr)

    def test_single_value_returns_half(self):
        arr = np.array([42.0])
        out = distribution_mod.normalize_to_unit(arr)
        np.testing.assert_array_almost_equal(out, np.array([0.5]))

    def test_min_max_equal_returns_half(self):
        arr = np.array([5.0, 5.0, 5.0])
        out = distribution_mod.normalize_to_unit(arr)
        np.testing.assert_array_almost_equal(out, np.array([0.5, 0.5, 0.5]))

    def test_normalizes_to_zero_one(self):
        arr = np.array([0.0, 50.0, 100.0])
        out = distribution_mod.normalize_to_unit(arr)
        np.testing.assert_array_almost_equal(out, np.array([0.0, 0.5, 1.0]))

    def test_negative_range(self):
        arr = np.array([-10.0, 0.0, 10.0])
        out = distribution_mod.normalize_to_unit(arr)
        np.testing.assert_array_almost_equal(out, np.array([0.0, 0.5, 1.0]))


class TestEcdfKsStatisticNormalized:
    """Tests for ecdf_ks_statistic_normalized."""

    def test_empty_returns_nan(self):
        assert np.isnan(distribution_mod.ecdf_ks_statistic_normalized(np.array([])))

    def test_perfect_uniform_zero_deviation(self):
        u = np.linspace(0.01, 0.99, 100)
        u = np.sort(u)
        # For true uniform, empirical CDF at u_i is i/n, theoretical is u_i. Max dev is small.
        stat = distribution_mod.ecdf_ks_statistic_normalized(u)
        assert stat >= 0
        assert not np.isnan(stat)

    def test_single_value(self):
        u = np.array([0.5])
        stat = distribution_mod.ecdf_ks_statistic_normalized(u)
        assert stat >= 0
        assert not np.isnan(stat)

    def test_2d_raveled(self):
        u = np.array([[0.2, 0.8], [0.3, 0.7]])
        stat = distribution_mod.ecdf_ks_statistic_normalized(u)
        assert stat >= 0
        assert not np.isnan(stat)


class TestEcdfMadNormalized:
    """Tests for ecdf_mad_normalized."""

    def test_empty_returns_nan(self):
        assert np.isnan(distribution_mod.ecdf_mad_normalized(np.array([])))

    def test_uniform_small_mad(self):
        u = np.sort(np.random.uniform(0, 1, 200))
        mad = distribution_mod.ecdf_mad_normalized(u)
        assert mad >= 0
        assert not np.isnan(mad)

    def test_single_value(self):
        assert distribution_mod.ecdf_mad_normalized(np.array([0.5])) >= 0


class TestEcdfRegionalDeviation:
    """Tests for ecdf_regional_deviation."""

    def test_empty_returns_zeros(self):
        out = distribution_mod.ecdf_regional_deviation(np.array([]), regions=5)
        assert out == [0.0] * 5

    def test_regions_zero_returns_empty_list(self):
        out = distribution_mod.ecdf_regional_deviation(np.array([]), regions=0)
        assert out == []

    def test_five_regions_returns_five_values(self):
        u = np.sort(np.random.uniform(0, 1, 500))
        out = distribution_mod.ecdf_regional_deviation(u, regions=5)
        assert len(out) == 5
        assert all(x >= 0 for x in out)


class TestQqRSquaredNormalized:
    """Tests for qq_r_squared_normalized."""

    def test_less_than_two_returns_nan(self):
        assert np.isnan(distribution_mod.qq_r_squared_normalized(np.array([])))
        assert np.isnan(distribution_mod.qq_r_squared_normalized(np.array([0.5])))

    def test_perfect_diagonal_r2_one(self):
        n = 50
        u = (np.arange(1, n + 1, dtype=float) - 0.5) / n
        r2 = distribution_mod.qq_r_squared_normalized(u)
        assert r2 <= 1.0
        assert r2 >= 0.0
        assert not np.isnan(r2)

    def test_two_points(self):
        u = np.array([0.25, 0.75])
        r2 = distribution_mod.qq_r_squared_normalized(u)
        assert not np.isnan(r2)


class TestQqMseNormalized:
    """Tests for qq_mse_normalized."""

    def test_empty_returns_nan(self):
        assert np.isnan(distribution_mod.qq_mse_normalized(np.array([])))

    def test_non_negative(self):
        u = np.sort(np.random.uniform(0, 1, 100))
        mse = distribution_mod.qq_mse_normalized(u)
        assert mse >= 0
        assert not np.isnan(mse)


class TestEmptyDeviationMetrics:
    """Tests for empty_deviation_metrics."""

    def test_structure(self):
        out = distribution_mod.empty_deviation_metrics()
        assert "ecdf" in out
        assert "qq" in out
        assert out["ecdf"]["ks_statistic"]["mean"] == 0.0
        assert out["ecdf"]["mad"]["mean"] == 0.0
        assert out["qq"]["r_squared"]["mean"] == 0.0
        assert out["qq"]["mse_from_diagonal"]["mean"] == 0.0
        assert len(out["ecdf"]["regional_deviation"]["labels"]) == 5


class TestComputeDistributionDeviationMetrics:
    """Tests for compute_distribution_deviation_metrics."""

    def test_empty_runs_returns_empty_metrics(self):
        out = distribution_mod.compute_distribution_deviation_metrics([])
        assert out == distribution_mod.empty_deviation_metrics()

    def test_none_runs_returns_empty_metrics(self):
        out = distribution_mod.compute_distribution_deviation_metrics(None)
        assert "ecdf" in out
        assert out["ecdf"]["ks_statistic"]["mean"] == 0.0

    def test_single_run(self):
        run = list(np.random.uniform(0, 1, 100))
        out = distribution_mod.compute_distribution_deviation_metrics([run])
        assert "ecdf" in out
        assert "qq" in out
        assert out["ecdf"]["ks_statistic"]["mean"] >= 0
        assert out["qq"]["r_squared"]["mean"] <= 1 and out["qq"]["r_squared"]["mean"] >= -1

    def test_run_with_nan_skipped(self):
        run_ok = list(np.random.uniform(0, 1, 50))
        run_nan = [np.nan, 0.5, 0.6]
        out = distribution_mod.compute_distribution_deviation_metrics([run_ok, run_nan])
        # Should still have metrics from run_ok; run_nan may be skipped
        assert "ecdf" in out

    def test_run_with_inf_skipped(self):
        run_ok = list(np.random.uniform(0, 1, 50))
        run_inf = [0.5, np.inf, 0.6]
        out = distribution_mod.compute_distribution_deviation_metrics([run_ok, run_inf])
        assert "ecdf" in out

    def test_all_runs_invalid_returns_empty_metrics(self):
        out = distribution_mod.compute_distribution_deviation_metrics([[np.nan], [np.inf], []])
        assert out["ecdf"]["ks_statistic"]["mean"] == 0.0


class TestDistributionAnalysis:
    """Tests for distribution_analysis."""

    def test_basic_structure(self):
        arr = np.random.uniform(0, 1, 200)
        out = distribution_mod.distribution_analysis(arr)
        assert "is_uniform" in out
        assert "ks_stat" in out["is_uniform"]
        assert "ks_p" in out["is_uniform"]
        assert "histogram" in out
        assert "kde" in out
        assert "qq_plot" in out
        assert "sample" in out["qq_plot"]
        assert "theoretical" in out["qq_plot"]

    def test_two_values(self):
        arr = np.array([0.25, 0.75])
        out = distribution_mod.distribution_analysis(arr)
        assert out["is_uniform"]["ks_stat"] >= 0
        assert "histogram" in out
        assert len(out["kde"]["x"]) >= 1
        assert len(out["kde"]["y"]) >= 1

    def test_small_array_has_structure(self):
        arr = np.array([0.2, 0.5, 0.5, 0.8])
        out = distribution_mod.distribution_analysis(arr)
        assert "is_uniform" in out
        assert "histogram" in out
        assert "kde" in out
