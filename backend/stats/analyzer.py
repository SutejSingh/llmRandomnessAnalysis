"""StatsAnalyzer: orchestrates single-run and multi-run statistical analysis."""
import numpy as np
from scipy.stats import kstest
from scipy import stats
from typing import Dict, Any, List

from . import utils
from . import basic_stats as basic_stats_mod
from . import distribution as distribution_mod
from . import range_behavior as range_behavior_mod
from . import independence as independence_mod
from . import stationarity as stationarity_mod
from . import spectral as spectral_mod
from . import nist_tests as nist_tests_mod
from .utils import MAX_CHART_POINTS


class StatsAnalyzer:
    """Perform comprehensive statistical analysis on number sequences (single or multi-run)."""

    def __init__(self):
        pass

    def _convert_numpy_types(self, obj):
        """Recursively convert numpy types to Python native types."""
        return utils.convert_numpy_types(obj)

    def analyze(self, numbers: List[float], provider: str) -> Dict[str, Any]:
        """Perform comprehensive statistical analysis. Does not include raw_data in response."""
        arr = np.array(numbers)
        analysis = {
            "provider": provider,
            "count": len(numbers),
            "basic_stats": basic_stats_mod.basic_stats(arr),
            "distribution": distribution_mod.distribution_analysis(arr),
            "range_behavior": range_behavior_mod.range_behavior(arr),
            "independence": independence_mod.independence_analysis(arr),
            "stationarity": stationarity_mod.stationarity_analysis(arr),
            "spectral": spectral_mod.spectral_analysis(arr),
            "nist_tests": nist_tests_mod.nist_tests(arr),
        }
        return analysis

    def analyze_multi_run(self, runs: List[List[float]], provider: str, num_runs: int) -> Dict[str, Any]:
        """Perform comprehensive statistical analysis across multiple runs."""
        if not runs or len(runs) == 0:
            raise ValueError("No runs provided")
        for idx, run in enumerate(runs):
            if not run or len(run) == 0:
                raise ValueError(f"Run {idx + 1} is empty")
            if not all(isinstance(x, (int, float)) for x in run):
                raise ValueError(f"Run {idx + 1} contains non-numeric values")

        individual_analyses = []
        means = []
        std_devs = []
        skewnesses = []
        kurtoses = []
        ks_passed = []
        runs_test_passed = []
        matrix_rank_test_passed = []
        longest_run_test_passed = []
        approximate_entropy_test_passed = []
        autocorr_info = []
        all_ecdf_data = []

        for run_idx, run_numbers in enumerate(runs):
            if not run_numbers or len(run_numbers) == 0:
                continue
            arr = np.array(run_numbers)
            if len(arr) == 0 or np.any(np.isnan(arr)) or np.any(np.isinf(arr)):
                continue

            run_mean = float(np.mean(arr))
            run_std = float(np.std(arr))
            run_skewness = float(stats.skew(arr))
            run_kurtosis = float(stats.kurtosis(arr))
            means.append(run_mean)
            std_devs.append(run_std)
            skewnesses.append(run_skewness)
            kurtoses.append(run_kurtosis)

            min_val = float(arr.min())
            max_val = float(arr.max())
            ks_stat, ks_p = kstest(arr, 'uniform', args=(min_val, max_val - min_val))
            ks_passed.append(ks_p > 0.05)

            nist_results = nist_tests_mod.nist_tests(arr)
            runs_test_passed.append(nist_results.get("runs_test", {}).get("passed", False))
            matrix_rank_test_passed.append(nist_results.get("binary_matrix_rank_test", {}).get("passed", False))
            longest_run_test_passed.append(nist_results.get("longest_run_of_ones_test", {}).get("passed", False))
            approximate_entropy_test_passed.append(nist_results.get("approximate_entropy_test", {}).get("passed", False))

            max_lag = min(50, len(arr) // 4)
            autocorrs = []
            significant_lags = []
            max_corr = 0.0
            for lag in range(1, max_lag + 1):
                if lag < len(arr):
                    corr = np.corrcoef(arr[:-lag], arr[lag:])[0, 1]
                    if not np.isnan(corr):
                        abs_corr = abs(corr)
                        autocorrs.append(float(corr))
                        if abs_corr > max_corr:
                            max_corr = abs_corr
                        if abs_corr > 0.2:
                            significant_lags.append(lag)
                    else:
                        autocorrs.append(0.0)
                else:
                    autocorrs.append(0.0)
            autocorr_info.append({
                "run": int(run_idx + 1),
                "significant_lags": [int(lag) for lag in significant_lags] if significant_lags else ["None"],
                "max_correlation": float(max_corr)
            })

            sorted_arr = np.sort(arr)
            ecdf_y = np.arange(1, len(sorted_arr) + 1) / len(sorted_arr)
            ecdf_x_list, ecdf_y_list = utils.downsample(sorted_arr, ecdf_y, MAX_CHART_POINTS)
            all_ecdf_data.append({
                "run": int(run_idx + 1),
                "x": [float(x) for x in ecdf_x_list],
                "y": [float(y) for y in ecdf_y_list]
            })
            individual_analyses.append(self.analyze(run_numbers, provider))

        if len(means) == 0:
            raise ValueError("No valid runs to analyze")

        means_arr = np.array(means)
        std_devs_arr = np.array(std_devs)
        skewnesses_arr = np.array(skewnesses)
        kurtoses_arr = np.array(kurtoses)
        modes = [a.get("basic_stats", {}).get("mode", np.nan) for a in individual_analyses]
        modes_arr = np.array([m for m in modes if not (isinstance(m, float) and np.isnan(m))], dtype=float)
        if len(modes_arr) == 0:
            modes_arr = np.array(means_arr)

        def calc_metric_stats(metric_arr):
            if len(metric_arr) == 0:
                return {"mean": 0.0, "std_dev": 0.0, "range": 0.0}
            mean_val = float(np.mean(metric_arr))
            std_dev_val = float(np.std(metric_arr)) if len(metric_arr) > 1 else 0.0
            range_val = float(np.max(metric_arr) - np.min(metric_arr))
            return {"mean": mean_val, "std_dev": std_dev_val, "range": range_val}

        aggregate_stats = {
            "mean": calc_metric_stats(means_arr),
            "std_dev": calc_metric_stats(std_devs_arr),
            "skewness": calc_metric_stats(skewnesses_arr),
            "kurtosis": calc_metric_stats(kurtoses_arr),
            "mode": calc_metric_stats(modes_arr),
        }

        ks_passed_count = int(sum(ks_passed))
        runs_test_passed_count = int(sum(runs_test_passed))
        matrix_rank_test_passed_count = int(sum(matrix_rank_test_passed))
        longest_run_test_passed_count = int(sum(longest_run_test_passed))
        approximate_entropy_test_passed_count = int(sum(approximate_entropy_test_passed))

        all_numbers = []
        for run_numbers in runs:
            all_numbers.extend(run_numbers)
        all_numbers_arr = np.array(all_numbers)
        combined_stream_stats = self._convert_numpy_types(basic_stats_mod.basic_stats(all_numbers_arr)) if len(all_numbers_arr) > 0 else {}

        min_val = float(np.min(all_numbers_arr))
        max_val = float(np.max(all_numbers_arr))
        num_bins = min(50, len(np.unique(all_numbers_arr)))
        if num_bins > 0:
            counts, bin_edges = np.histogram(all_numbers_arr, bins=num_bins)
            bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
            frequency_histogram = {
                "bins": [float(x) for x in bin_centers.tolist()],
                "frequencies": [int(x) for x in counts.tolist()],
                "bin_edges": [float(x) for x in bin_edges.tolist()]
            }
        else:
            frequency_histogram = {"bins": [], "frequencies": [], "bin_edges": []}

        n_kde = min(MAX_CHART_POINTS, len(all_numbers_arr) + 1)
        combined_kde_x = np.linspace(min_val, max_val, n_kde)
        combined_kde_y = stats.gaussian_kde(all_numbers_arr)(combined_kde_x)
        combined_kde = {
            "x": [float(x) for x in combined_kde_x.tolist()],
            "y": [float(y) for y in combined_kde_y.tolist()]
        }

        converted_aggregate_stats = self._convert_numpy_types(aggregate_stats)
        distribution_deviation = distribution_mod.compute_distribution_deviation_metrics(runs)
        distribution_deviation = self._convert_numpy_types(distribution_deviation)

        result = {
            "provider": str(provider),
            "num_runs": int(num_runs),
            "count_per_run": int(len(runs[0])) if runs else 0,
            "aggregate_stats": converted_aggregate_stats,
            "combined_stream_stats": combined_stream_stats,
            "distribution_deviation": distribution_deviation,
            "test_results": {
                "ks_uniformity_passed": f"{ks_passed_count}/{num_runs}",
                "runs_test_passed": f"{runs_test_passed_count}/{num_runs}",
                "binary_matrix_rank_test_passed": f"{matrix_rank_test_passed_count}/{num_runs}",
                "longest_run_of_ones_test_passed": f"{longest_run_test_passed_count}/{num_runs}",
                "approximate_entropy_test_passed": f"{approximate_entropy_test_passed_count}/{num_runs}",
                "ks_passed_count": ks_passed_count,
                "runs_test_passed_count": runs_test_passed_count,
                "binary_matrix_rank_test_passed_count": matrix_rank_test_passed_count,
                "longest_run_of_ones_test_passed_count": longest_run_test_passed_count,
                "approximate_entropy_test_passed_count": approximate_entropy_test_passed_count
            },
            "autocorrelation_table": autocorr_info,
            "ecdf_all_runs": all_ecdf_data,
            "frequency_histogram": frequency_histogram,
            "combined_kde": combined_kde
        }

        converted_individual_analyses = []
        for analysis in individual_analyses:
            converted_analysis = self._convert_numpy_types(analysis)
            converted_individual_analyses.append(converted_analysis)
        result["individual_analyses"] = converted_individual_analyses
        return result
