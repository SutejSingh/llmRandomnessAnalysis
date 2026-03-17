"""Tests for backend/reporting/latex_charts.py - chart generation returns filenames and handles edge cases."""
import os
import tempfile
import pytest

from reporting import latex_charts


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d


class TestGenerateOverlaidEcdfChart:
    def test_empty_ecdf_returns_none(self, temp_dir):
        analysis = {"ecdf_all_runs": []}
        assert latex_charts.generate_overlaid_ecdf_chart(analysis, temp_dir) is None

    def test_with_data_returns_filename(self, temp_dir):
        analysis = {
            "ecdf_all_runs": [
                {"run": 1, "x": [0.0, 0.5, 1.0], "y": [0.0, 0.5, 1.0]},
            ]
        }
        out = latex_charts.generate_overlaid_ecdf_chart(analysis, temp_dir)
        assert out == "ecdf_overlaid.png"
        assert os.path.exists(os.path.join(temp_dir, out))


class TestGenerateOverlaidQqChart:
    def test_no_individual_analyses_returns_none(self, temp_dir):
        analysis = {}
        assert latex_charts.generate_overlaid_qq_chart(analysis, temp_dir) is None

    def test_with_qq_data_returns_filename(self, temp_dir):
        analysis = {
            "individual_analyses": [
                {"distribution": {"qq_plot": {"theoretical": [0.25, 0.5, 0.75], "sample": [0.2, 0.5, 0.8]}}},
            ]
        }
        out = latex_charts.generate_overlaid_qq_chart(analysis, temp_dir)
        assert out == "qq_overlaid.png"
        assert os.path.exists(os.path.join(temp_dir, out))


class TestGenerateFrequencyHistogramChart:
    def test_empty_bins_returns_none(self, temp_dir):
        analysis = {"frequency_histogram": {"bins": [], "frequencies": [], "bin_edges": []}}
        assert latex_charts.generate_frequency_histogram_chart(analysis, temp_dir) is None

    def test_with_data_returns_filename(self, temp_dir):
        analysis = {
            "frequency_histogram": {
                "bins": [0.1, 0.3, 0.5, 0.7, 0.9],
                "frequencies": [10, 20, 30, 20, 10],
                "bin_edges": [0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
            }
        }
        out = latex_charts.generate_frequency_histogram_chart(analysis, temp_dir)
        assert out == "frequency_histogram.png"
        assert os.path.exists(os.path.join(temp_dir, out))


class TestGenerateKdeChart:
    def test_empty_kde_returns_none(self, temp_dir):
        assert latex_charts.generate_kde_chart({"x": [], "y": []}, 1, temp_dir) is None

    def test_with_data_returns_filename(self, temp_dir):
        kde = {"x": [0.0, 0.5, 1.0], "y": [0.5, 1.0, 0.5]}
        out = latex_charts.generate_kde_chart(kde, 1, temp_dir)
        assert out == "kde_run1.png"
        assert os.path.exists(os.path.join(temp_dir, out))


class TestGenerateEcdfChart:
    def test_empty_returns_none(self, temp_dir):
        assert latex_charts.generate_ecdf_chart({"x": [], "y": []}, 1, temp_dir) is None

    def test_with_data_returns_filename(self, temp_dir):
        ecdf = {"x": [0.0, 0.5, 1.0], "y": [0.0, 0.5, 1.0]}
        out = latex_charts.generate_ecdf_chart(ecdf, 1, temp_dir)
        assert out == "ecdf_run1.png"
        assert os.path.exists(os.path.join(temp_dir, out))


class TestGenerateQqChart:
    def test_empty_returns_none(self, temp_dir):
        assert latex_charts.generate_qq_chart({"theoretical": [], "sample": []}, 1, temp_dir) is None

    def test_with_data_returns_filename(self, temp_dir):
        qq = {"theoretical": [0.25, 0.5, 0.75], "sample": [0.2, 0.5, 0.8]}
        out = latex_charts.generate_qq_chart(qq, 1, temp_dir)
        assert out == "qq_run1.png"
        assert os.path.exists(os.path.join(temp_dir, out))


class TestGenerateAcfChart:
    def test_empty_returns_none(self, temp_dir):
        assert latex_charts.generate_acf_chart({"lags": [], "values": []}, 1, temp_dir) is None

    def test_with_data_returns_filename(self, temp_dir):
        acf = {"lags": [1, 2, 3], "values": [0.5, 0.2, 0.1]}
        out = latex_charts.generate_acf_chart(acf, 1, temp_dir)
        assert out == "acf_run1.png"
        assert os.path.exists(os.path.join(temp_dir, out))


class TestGenerateLag1ScatterChart:
    def test_empty_returns_none(self, temp_dir):
        assert latex_charts.generate_lag1_scatter_chart({"x": [], "y": []}, 1, temp_dir) is None

    def test_with_data_returns_filename(self, temp_dir):
        lag1 = {"x": [1.0, 2.0, 3.0], "y": [2.0, 3.0, 4.0]}
        out = latex_charts.generate_lag1_scatter_chart(lag1, 1, temp_dir)
        assert out == "lag1_run1.png"
        assert os.path.exists(os.path.join(temp_dir, out))


class TestGenerateTimeSeriesChart:
    def test_empty_returns_none(self, temp_dir):
        assert latex_charts.generate_time_series_chart({"index": [], "values": []}, 1, temp_dir) is None

    def test_with_data_returns_filename(self, temp_dir):
        ts = {"index": [0.0, 1.0, 2.0], "values": [0.5, 0.6, 0.4]}
        out = latex_charts.generate_time_series_chart(ts, 1, temp_dir)
        assert out == "timeseries_run1.png"
        assert os.path.exists(os.path.join(temp_dir, out))


class TestGenerateRollingStatsChart:
    def test_missing_rolling_mean_returns_none(self, temp_dir):
        stat = {"rolling_mean": {"index": [], "values": []}, "rolling_std": {"values": []}}
        assert latex_charts.generate_rolling_stats_chart(stat, 1, temp_dir) is None

    def test_with_data_returns_filename(self, temp_dir):
        stat = {
            "rolling_mean": {"index": [0, 1, 2], "values": [0.5, 0.5, 0.5]},
            "rolling_std": {"values": [0.1, 0.1, 0.1]},
        }
        out = latex_charts.generate_rolling_stats_chart(stat, 1, temp_dir)
        assert out == "rolling_run1.png"
        assert os.path.exists(os.path.join(temp_dir, out))


class TestGenerateFftChart:
    def test_empty_returns_none(self, temp_dir):
        assert latex_charts.generate_fft_chart({"frequencies": [], "magnitude": []}, 1, temp_dir) is None

    def test_with_data_returns_filename(self, temp_dir):
        spec = {"frequencies": [0.1, 0.2, 0.3], "magnitude": [1.0, 0.5, 0.2]}
        out = latex_charts.generate_fft_chart(spec, 1, temp_dir)
        assert out == "fft_run1.png"
        assert os.path.exists(os.path.join(temp_dir, out))


class TestGeneratePowerSpectrumChart:
    def test_empty_returns_none(self, temp_dir):
        assert latex_charts.generate_power_spectrum_chart({"frequencies": [], "power": []}, 1, temp_dir) is None

    def test_with_data_returns_filename(self, temp_dir):
        spec = {"frequencies": [0.1, 0.2], "power": [1.0, 0.25]}
        out = latex_charts.generate_power_spectrum_chart(spec, 1, temp_dir)
        assert out == "power_run1.png"
        assert os.path.exists(os.path.join(temp_dir, out))
