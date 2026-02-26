"""Tests for backend/reporting/latex_tables.py - all generate_* table functions."""
import pytest

from reporting import latex_tables


class TestGenerateAggregateStatsTable:
    def test_produces_latex(self):
        analysis = {
            "aggregate_stats": {
                "mean": {"mean": 0.5, "std_dev": 0.1, "range": 0.3},
                "mode": {"mean": 0.5, "std_dev": 0.0, "range": 0.0},
                "std_dev": {"mean": 0.29, "std_dev": 0.02, "range": 0.05},
                "skewness": {"mean": 0.0, "std_dev": 0.1, "range": 0.2},
                "kurtosis": {"mean": -1.2, "std_dev": 0.1, "range": 0.3},
            }
        }
        out = latex_tables.generate_aggregate_stats_table(analysis)
        assert r"\begin{table}" in out
        assert r"\end{table}" in out
        assert "Mean" in out
        assert "0.500000" in out

    def test_empty_aggregate_stats_still_has_structure(self):
        analysis = {"aggregate_stats": {}}
        out = latex_tables.generate_aggregate_stats_table(analysis)
        assert r"\begin{tabular}" in out


class TestGeneratePerRunStatsTable:
    def test_produces_latex(self):
        analysis = {
            "individual_analyses": [
                {"basic_stats": {"mean": 0.5, "mode": 0.5, "std": 0.29, "min": 0.0, "max": 1.0}, "distribution": {"is_uniform": {"ks_p": 0.1}}},
                {"basic_stats": {"mean": 0.5, "mode": 0.5, "std": 0.3, "min": 0.0, "max": 1.0}, "distribution": {"is_uniform": {"ks_p": 0.6}}},
            ]
        }
        out = latex_tables.generate_per_run_stats_table(analysis)
        assert r"\begin{table}" in out
        assert "Run" in out
        assert "1" in out and "2" in out

    def test_empty_individual_analyses(self):
        analysis = {"individual_analyses": []}
        out = latex_tables.generate_per_run_stats_table(analysis)
        assert r"\begin{tabular}" in out

    def test_nan_mode_shows_na(self):
        analysis = {
            "individual_analyses": [
                {"basic_stats": {"mean": 0.5, "mode": float("nan"), "std": 0.29, "min": 0.0, "max": 1.0}, "distribution": {"is_uniform": {"ks_p": 0.05}}},
            ]
        }
        out = latex_tables.generate_per_run_stats_table(analysis)
        assert "N/A" in out


class TestGenerateAutocorrTable:
    def test_produces_latex(self):
        analysis = {
            "autocorrelation_table": [
                {"run": 1, "significant_lags": [1, 2], "max_correlation": 0.3},
                {"run": 2, "significant_lags": ["None"], "max_correlation": 0.1},
            ]
        }
        out = latex_tables.generate_autocorr_table(analysis)
        assert r"\begin{table}" in out
        assert "Significant" in out or "Correlation" in out
        assert "None" in out or "1, 2" in out

    def test_empty_table(self):
        analysis = {"autocorrelation_table": []}
        out = latex_tables.generate_autocorr_table(analysis)
        assert r"\begin{tabular}" in out


class TestGenerateDistributionDeviationTables:
    def test_empty_returns_empty_string(self):
        analysis = {}
        out = latex_tables.generate_distribution_deviation_tables(analysis)
        assert out == ""

    def test_with_ecdf_and_qq(self):
        analysis = {
            "distribution_deviation": {
                "ecdf": {
                    "ks_statistic": {"mean": 0.05, "std_dev": 0.01, "cv": 0.2},
                    "mad": {"mean": 0.03, "std_dev": 0.01, "cv": 0.3},
                    "regional_deviation": {"labels": ["0.0–0.2", "0.2–0.4", "0.4–0.6", "0.6–0.8", "0.8–1.0"], "mean": [0.02] * 5},
                },
                "qq": {
                    "r_squared": {"mean": 0.99, "std_dev": 0.01},
                    "mse_from_diagonal": {"mean": 0.001, "std_dev": 0.0005},
                },
            }
        }
        out = latex_tables.generate_distribution_deviation_tables(analysis)
        assert "K-S" in out or "deviation" in out
        assert "R$^2$" in out or "MSE" in out


class TestGenerateDescriptiveStatsTable:
    def test_produces_latex(self):
        basic_stats = {
            "mean": 0.5, "mode": 0.5, "median": 0.5, "std": 0.29, "variance": 0.084,
            "min": 0.0, "max": 1.0, "q25": 0.25, "q75": 0.75, "q95": 0.95,
            "skewness": 0.0, "kurtosis": -1.2,
        }
        out = latex_tables.generate_descriptive_stats_table(basic_stats, caption="Test")
        assert r"\begin{table}" in out
        assert "Mean" in out
        assert "Test" in out

    def test_nan_mode(self):
        basic_stats = {"mean": 0.5, "mode": "N/A", "median": 0.5, "std": 0.29, "variance": 0.08, "min": 0.0, "max": 1.0, "q25": 0.25, "q75": 0.75, "q95": 0.95, "skewness": 0, "kurtosis": 0}
        out = latex_tables.generate_descriptive_stats_table(basic_stats)
        assert "N/A" in out


class TestGenerateNistTestTableContent:
    def test_error_in_test_returns_error_text(self):
        nist_test = {"error": "Sequence too short"}
        out = latex_tables.generate_nist_test_table_content(nist_test, "Runs Test")
        assert "Error" in out
        assert "Sequence" in out or "short" in out

    def test_valid_test_returns_table(self):
        nist_test = {"p_value": 0.5, "statistic": 0.1, "passed": True}
        out = latex_tables.generate_nist_test_table_content(nist_test, "Runs Test")
        assert r"\begin{tabular}" in out
        assert "0.500000" in out or "0.5" in out
        assert "Passed" in out


class TestGenerateNistTablesGrid:
    def test_empty_returns_empty(self):
        assert latex_tables.generate_nist_tables_grid([]) == ""

    def test_single_table(self):
        grid = [("Runs Test", {"p_value": 0.5, "passed": True})]
        out = latex_tables.generate_nist_tables_grid(grid)
        assert r"\begin{table}" in out
        assert "Runs Test" in out

    def test_two_tables(self):
        grid = [
            ("Runs Test", {"p_value": 0.5, "passed": True}),
            ("Rank Test", {"p_value": 0.3, "passed": False}),
        ]
        out = latex_tables.generate_nist_tables_grid(grid)
        assert "Runs Test" in out
        assert "Rank Test" in out
