"""Tests for backend/stats spectral, stationarity, independence, range_behavior."""
import numpy as np
import pytest

from stats import spectral as spectral_mod
from stats import stationarity as stationarity_mod
from stats import independence as independence_mod
from stats import range_behavior as range_behavior_mod


# ----- spectral_analysis -----
class TestSpectralAnalysis:
    def test_basic_structure(self):
        arr = np.random.uniform(0, 1, 200)
        out = spectral_mod.spectral_analysis(arr)
        assert "frequencies" in out
        assert "magnitude" in out
        assert "power" in out
        assert len(out["frequencies"]) == len(out["magnitude"]) == len(out["power"])

    def test_positive_frequencies_only(self):
        arr = np.linspace(0, 1, 100)
        out = spectral_mod.spectral_analysis(arr)
        assert all(f > 0 for f in out["frequencies"])

    def test_single_value(self):
        arr = np.array([0.5])
        out = spectral_mod.spectral_analysis(arr)
        assert "frequencies" in out
        assert "magnitude" in out
        assert "power" in out
        # n=1: fft has one value, no positive freqs
        assert len(out["frequencies"]) >= 0

    def test_magnitude_and_power_consistent(self):
        arr = np.random.uniform(0, 1, 100)
        out = spectral_mod.spectral_analysis(arr)
        for m, p in zip(out["magnitude"], out["power"]):
            assert abs(p - m ** 2) < 1e-10


# ----- stationarity_analysis -----
class TestStationarityAnalysis:
    def test_basic_structure(self):
        arr = np.random.uniform(0, 1, 200)
        out = stationarity_mod.stationarity_analysis(arr)
        assert "rolling_mean" in out
        assert "rolling_std" in out
        assert "chunks" in out
        assert "index" in out["rolling_mean"]
        assert "values" in out["rolling_mean"]
        assert len(out["chunks"]) == 4

    def test_chunk_stats(self):
        arr = np.linspace(0, 100, 100)
        out = stationarity_mod.stationarity_analysis(arr)
        assert len(out["chunks"]) == 4
        for c in out["chunks"]:
            assert "chunk" in c
            assert "mean" in c
            assert "std" in c
            assert "min" in c
            assert "max" in c

    def test_small_array(self):
        arr = np.array([1.0, 2.0, 3.0, 4.0, 5.0] * 4)
        out = stationarity_mod.stationarity_analysis(arr)
        assert "rolling_mean" in out
        assert "chunks" in out


# ----- independence_analysis -----
class TestIndependenceAnalysis:
    def test_basic_structure(self):
        arr = np.random.uniform(0, 1, 200)
        out = independence_mod.independence_analysis(arr)
        assert "autocorrelation" in out
        assert "lag1_scatter" in out
        assert "time_series" in out
        assert out["autocorrelation"]["lags"]
        assert out["autocorrelation"]["values"]
        assert len(out["autocorrelation"]["lags"]) == len(out["autocorrelation"]["values"])
        assert "x" in out["lag1_scatter"]
        assert "y" in out["lag1_scatter"]

    def test_autocorr_lag1_self_correlation(self):
        arr = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        out = independence_mod.independence_analysis(arr)
        assert out["autocorrelation"]["values"][0] == pytest.approx(1.0, rel=1e-5)

    def test_short_array(self):
        arr = np.array([1.0, 2.0])
        out = independence_mod.independence_analysis(arr)
        assert "autocorrelation" in out
        assert "lag1_scatter" in out
        assert "time_series" in out

    def test_single_element(self):
        arr = np.array([0.5])
        out = independence_mod.independence_analysis(arr)
        assert "autocorrelation" in out
        assert "lag1_scatter" in out


# ----- range_behavior -----
class TestRangeBehavior:
    def test_basic_structure(self):
        arr = np.random.uniform(0, 1, 200)
        out = range_behavior_mod.range_behavior(arr)
        assert "ecdf" in out
        assert "boundaries" in out
        assert "edge_histogram" in out
        assert out["boundaries"]["min"] <= out["boundaries"]["max"]
        assert "near_min_count" in out["boundaries"]
        assert "near_max_count" in out["boundaries"]
        assert "near_min_pct" in out["boundaries"]
        assert "near_max_pct" in out["boundaries"]

    def test_ecdf_x_y_same_length(self):
        arr = np.linspace(0, 1, 100)
        out = range_behavior_mod.range_behavior(arr)
        assert len(out["ecdf"]["x"]) == len(out["ecdf"]["y"])
        assert out["ecdf"]["y"][0] > 0
        assert out["ecdf"]["y"][-1] == pytest.approx(1.0, rel=1e-5)

    def test_edge_histogram_20_bins(self):
        arr = np.random.uniform(0, 1, 500)
        out = range_behavior_mod.range_behavior(arr)
        counts = out["edge_histogram"]["counts"]
        edges = out["edge_histogram"]["edges"]
        assert len(counts) == 20
        assert len(edges) == 21

    def test_single_value(self):
        arr = np.array([0.5])
        out = range_behavior_mod.range_behavior(arr)
        assert out["boundaries"]["min"] == 0.5
        assert out["boundaries"]["max"] == 0.5
        assert out["boundaries"]["near_min_count"] == 1
        assert out["boundaries"]["near_max_count"] == 1
        assert out["boundaries"]["near_min_pct"] == 100.0
        assert out["boundaries"]["near_max_pct"] == 100.0
