import numpy as np
from scipy import stats
from scipy.fft import fft
from scipy.stats import kstest, chi2
import pandas as pd
from typing import Dict, Any, List, Tuple
import struct

# Cap points for visualization to keep payloads and chart generation bounded
MAX_CHART_POINTS = 5000


class StatsAnalyzer:
    def __init__(self):
        pass
    
    def _convert_numpy_types(self, obj):
        """Recursively convert numpy types to Python native types"""
        import numpy as np
        
        if isinstance(obj, (np.integer, np.int_, np.intc, np.intp, np.int8,
                           np.int16, np.int32, np.int64, np.uint8, np.uint16,
                           np.uint32, np.uint64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float_, np.float16, np.float32, np.float64)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return [self._convert_numpy_types(item) for item in obj.tolist()]
        elif isinstance(obj, dict):
            return {key: self._convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._convert_numpy_types(item) for item in obj]
        else:
            return obj

    @staticmethod
    def _downsample(x: np.ndarray, y: np.ndarray, max_points: int) -> Tuple[List[float], List[float]]:
        """Downsample two equal-length arrays to at most max_points, preserving first and last."""
        n = len(x)
        if n <= max_points:
            return x.tolist(), y.tolist()
        indices = np.linspace(0, n - 1, max_points, dtype=int)
        indices = np.unique(indices)
        if indices[-1] != n - 1:
            indices = np.append(indices, n - 1)
        return x[indices].tolist(), y[indices].tolist()

    @staticmethod
    def _downsample_single(arr: np.ndarray, max_points: int) -> List[float]:
        """Downsample a single array to at most max_points, preserving first and last."""
        n = len(arr)
        if n <= max_points:
            return arr.tolist()
        indices = np.linspace(0, n - 1, max_points, dtype=int)
        indices = np.unique(indices)
        if indices[-1] != n - 1:
            indices = np.append(indices, n - 1)
        return arr[indices].tolist()

    # -------------------------------------------------------------------------
    # Distribution deviation metrics (ECDF and Q-Q) for multi-run analysis.
    # All assume data is normalized to [0, 1] per run (min/max of that run).
    # -------------------------------------------------------------------------

    @staticmethod
    def _normalize_to_unit(arr: np.ndarray) -> np.ndarray:
        """Normalize array to [0, 1] using min/max of the run. Returns same length; constant arrays become 0.5."""
        if len(arr) == 0:
            return arr
        lo, hi = arr.min(), arr.max()
        if hi <= lo:
            return np.full_like(arr, 0.5, dtype=float)
        return (arr - lo) / (hi - lo)

    @staticmethod
    def _ecdf_ks_statistic_normalized(u: np.ndarray) -> float:
        """
        Max vertical deviation (K-S statistic) for uniform [0,1].
        D_n = max(|F_empirical(x) - F_theoretical(x)|). Theoretical F(x)=x.
        u must be sorted or we sort it; assumed normalized to [0,1].
        """
        if len(u) == 0:
            return float('nan')
        u = np.asarray(u, dtype=float)
        if u.ndim > 1:
            u = u.ravel()
        u = np.sort(u)
        n = len(u)
        # Empirical CDF at each point (right-continuous: F(x_i) = i/n)
        empirical = np.arange(1, n + 1, dtype=float) / n
        theoretical = u
        dev = np.abs(empirical - theoretical)
        # K-S also checks at jump points: just before each jump, F_emp drops
        dev_left = np.abs(np.arange(0, n, dtype=float) / n - theoretical)
        return float(np.max(np.maximum(dev, dev_left)))

    @staticmethod
    def _ecdf_mad_normalized(u: np.ndarray) -> float:
        """
        Mean absolute deviation: mean(|F_empirical(x) - F_theoretical(x)|).
        u assumed normalized to [0,1], will be sorted.
        """
        if len(u) == 0:
            return float('nan')
        u = np.asarray(u, dtype=float).ravel()
        u = np.sort(u)
        n = len(u)
        empirical = np.arange(1, n + 1, dtype=float) / n
        theoretical = u
        return float(np.mean(np.abs(empirical - theoretical)))

    @staticmethod
    def _ecdf_regional_deviation(u: np.ndarray, regions: int = 5) -> List[float]:
        """
        Break [0,1] into equal regions and compute mean absolute deviation in each.
        Returns list of length `regions`. Vectorized.
        """
        if len(u) == 0 or regions <= 0:
            return [0.0] * regions
        u = np.asarray(u, dtype=float).ravel()
        u = np.sort(u)
        n = len(u)
        empirical = np.arange(1, n + 1, dtype=float) / n
        theoretical = u
        abs_dev = np.abs(empirical - theoretical)
        boundaries = np.linspace(0, 1, regions + 1)
        out = []
        for i in range(regions):
            low, high = boundaries[i], boundaries[i + 1]
            # points in [low, high]; last region includes right endpoint so u=1.0 is counted
            is_last = i == regions - 1
            mask = (u >= low) & (u <= high) if is_last else (u >= low) & (u < high)
            if np.any(mask):
                out.append(float(np.mean(abs_dev[mask])))
            else:
                out.append(0.0)
        return out

    @staticmethod
    def _qq_r_squared_normalized(u: np.ndarray) -> float:
        """
        R² for Q-Q plot vs uniform: R² = 1 - (SS_res / SS_tot).
        Sample quantiles = sorted u, theoretical = (i - 0.5) / n (Blom).
        Measures how well points follow the diagonal y=x.
        """
        if len(u) < 2:
            return float('nan')
        u = np.asarray(u, dtype=float).ravel()
        u = np.sort(u)
        n = len(u)
        theoretical = (np.arange(1, n + 1, dtype=float) - 0.5) / n
        sample = u
        ss_res = np.sum((sample - theoretical) ** 2)
        ss_tot = np.sum((sample - np.mean(sample)) ** 2)
        if ss_tot <= 0:
            return float('nan')
        return float(1.0 - (ss_res / ss_tot))

    @staticmethod
    def _qq_mse_normalized(u: np.ndarray) -> float:
        """
        Mean squared error from diagonal (y=x) in Q-Q plot.
        Theoretical quantiles (Blom): (i - 0.5) / n; sample = sorted u.
        """
        if len(u) == 0:
            return float('nan')
        u = np.asarray(u, dtype=float).ravel()
        u = np.sort(u)
        n = len(u)
        theoretical = (np.arange(1, n + 1, dtype=float) - 0.5) / n
        return float(np.mean((u - theoretical) ** 2))

    def _compute_distribution_deviation_metrics(self, runs: List[List[float]]) -> Dict[str, Any]:
        """
        Compute ECDF and Q-Q deviation metrics across runs.
        Each run is normalized to [0,1] using its own min/max before computing metrics.
        Returns aggregates: mean, std_dev, cv where applicable; regional pattern; per-run lists omitted for payload size.
        """
        if not runs:
            return self._empty_deviation_metrics()
        n_runs = len(runs)
        ks_list = []
        mad_list = []
        regional_list = []
        r2_list = []
        mse_list = []
        for run in runs:
            arr = np.array(run, dtype=float)
            if len(arr) == 0 or np.any(np.isnan(arr)) or np.any(np.isinf(arr)):
                continue
            u = self._normalize_to_unit(arr)
            if len(u) < 2:
                continue
            ks_list.append(self._ecdf_ks_statistic_normalized(u))
            mad_list.append(self._ecdf_mad_normalized(u))
            regional_list.append(self._ecdf_regional_deviation(u, regions=5))
            r2_list.append(self._qq_r_squared_normalized(u))
            mse_list.append(self._qq_mse_normalized(u))
        if not ks_list:
            return self._empty_deviation_metrics()
        ks_arr = np.array(ks_list)
        mad_arr = np.array(mad_list)
        r2_arr = np.array(r2_list)
        mse_arr = np.array(mse_list)
        regional_arr = np.array(regional_list)  # shape (n_runs, 5)
        mean_regional = np.mean(regional_arr, axis=0)
        def safe_cv(x: np.ndarray) -> float:
            m = float(np.mean(x))
            if m == 0 or np.isnan(m):
                return 0.0
            s = float(np.std(x))
            return s / m
        return {
            "ecdf": {
                "ks_statistic": {
                    "mean": float(np.mean(ks_arr)),
                    "std_dev": float(np.std(ks_arr)) if len(ks_arr) > 1 else 0.0,
                    "cv": safe_cv(ks_arr),
                },
                "mad": {
                    "mean": float(np.mean(mad_arr)),
                    "std_dev": float(np.std(mad_arr)) if len(mad_arr) > 1 else 0.0,
                    "cv": safe_cv(mad_arr),
                },
                "regional_deviation": {
                    "labels": ["0.0–0.2", "0.2–0.4", "0.4–0.6", "0.6–0.8", "0.8–1.0"],
                    "mean": [float(x) for x in mean_regional.tolist()],
                },
            },
            "qq": {
                "r_squared": {
                    "mean": float(np.mean(r2_arr)),
                    "std_dev": float(np.std(r2_arr)) if len(r2_arr) > 1 else 0.0,
                },
                "mse_from_diagonal": {
                    "mean": float(np.mean(mse_arr)),
                    "std_dev": float(np.std(mse_arr)) if len(mse_arr) > 1 else 0.0,
                },
            },
        }

    def _empty_deviation_metrics(self) -> Dict[str, Any]:
        empty_agg = {"mean": 0.0, "std_dev": 0.0, "cv": 0.0}
        return {
            "ecdf": {
                "ks_statistic": empty_agg.copy(),
                "mad": {**empty_agg},
                "regional_deviation": {"labels": ["0.0–0.2", "0.2–0.4", "0.4–0.6", "0.6–0.8", "0.8–1.0"], "mean": [0.0] * 5},
            },
            "qq": {
                "r_squared": {"mean": 0.0, "std_dev": 0.0},
                "mse_from_diagonal": {"mean": 0.0, "std_dev": 0.0},
            },
        }

    def analyze(self, numbers: List[float], provider: str) -> Dict[str, Any]:
        """Perform comprehensive statistical analysis. Does not include raw_data in response."""
        arr = np.array(numbers)
        
        analysis = {
            "provider": provider,
            "count": len(numbers),
            "basic_stats": self._basic_stats(arr),
            "distribution": self._distribution_analysis(arr),
            "range_behavior": self._range_behavior(arr),
            "independence": self._independence_analysis(arr),
            "stationarity": self._stationarity_analysis(arr),
            "spectral": self._spectral_analysis(arr),
            "nist_tests": self._nist_tests(arr),
        }
        
        return analysis
    
    @staticmethod
    def _is_integer_like(arr: np.ndarray) -> bool:
        """True if all values are integers (or whole-number floats). Used to choose discrete vs continuous mode/percentiles."""
        if len(arr) == 0:
            return False
        arr = np.asarray(arr, dtype=float)
        if not np.all(np.isfinite(arr)):
            return False
        return np.all(arr == np.round(arr))

    @staticmethod
    def _mode_discrete(arr: np.ndarray) -> float:
        """Mode for discrete data: most frequent value. Tie-break: smallest."""
        if len(arr) == 0:
            return float('nan')
        vals, counts = np.unique(arr, return_counts=True)
        max_count = np.max(counts)
        modes = vals[counts == max_count]
        return float(modes.min())

    @staticmethod
    def _mode_continuous(arr: np.ndarray, bins: int = 50) -> float:
        """Mode for continuous data: midpoint of the histogram bin with highest count."""
        if len(arr) == 0:
            return float('nan')
        counts, edges = np.histogram(arr, bins=min(bins, max(1, len(arr))))
        if np.max(counts) == 0:
            return float(np.median(arr))
        i = np.argmax(counts)
        return float((edges[i] + edges[i + 1]) / 2)

    def _basic_stats(self, arr: np.ndarray) -> Dict[str, float]:
        """Calculate basic descriptive statistics (sample variance/std with ddof=1).
        For integer-like data: mode = most frequent value; percentiles use actual data values (method='lower').
        For continuous data: mode = histogram bin midpoint; percentiles use linear interpolation."""
        discrete = self._is_integer_like(arr)
        if discrete:
            median = float(np.percentile(arr, 50, method='lower'))
            q25 = float(np.percentile(arr, 25, method='lower'))
            q50 = float(np.percentile(arr, 50, method='lower'))
            q75 = float(np.percentile(arr, 75, method='lower'))
            q95 = float(np.percentile(arr, 95, method='lower'))
            mode = self._mode_discrete(arr)
        else:
            median = float(np.median(arr))
            q25 = float(np.percentile(arr, 25))
            q50 = float(np.percentile(arr, 50))
            q75 = float(np.percentile(arr, 75))
            q95 = float(np.percentile(arr, 95))
            mode = self._mode_continuous(arr)
        return {
            "mean": float(np.mean(arr)),
            "median": median,
            "mode": mode,
            "std": float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0,
            "variance": float(np.var(arr, ddof=1)) if len(arr) > 1 else 0.0,
            "min": float(np.min(arr)),
            "max": float(np.max(arr)),
            "q25": q25,
            "q50": q50,
            "q75": q75,
            "q95": q95,
            "skewness": float(stats.skew(arr)),
            "kurtosis": float(stats.kurtosis(arr))
        }
    
    def _distribution_analysis(self, arr: np.ndarray) -> Dict[str, Any]:
        """Analyze distribution shape. Chart data capped at MAX_CHART_POINTS."""
        # Uniformity test (Kolmogorov-Smirnov)
        # Test against uniform distribution on the actual data range
        min_val = float(arr.min())
        max_val = float(arr.max())
        ks_stat, ks_p = kstest(arr, 'uniform', args=(min_val, max_val - min_val))
        
        # Histogram data for visualization
        hist_counts, hist_edges = np.histogram(arr, bins=50)
        
        # KDE approximation (sample points) - use MAX_CHART_POINTS
        n_kde = min(MAX_CHART_POINTS, len(arr) + 1)
        kde_x = np.linspace(arr.min(), arr.max(), n_kde)
        kde_y = stats.gaussian_kde(arr)(kde_x)
        
        # Q-Q plot data (against uniform distribution), downsampled
        sorted_arr = np.sort(arr)
        theoretical_quantiles = stats.uniform.ppf(
            np.linspace(0.01, 0.99, len(sorted_arr)),
            loc=min_val,
            scale=max_val - min_val
        )
        sample_list, theory_list = self._downsample(
            sorted_arr, np.array(theoretical_quantiles), MAX_CHART_POINTS
        )
        
        return {
            "is_uniform": {
                "ks_stat": float(ks_stat),
                "ks_p": float(ks_p)
            },
            "histogram": {
                "counts": hist_counts.tolist(),
                "edges": hist_edges.tolist()
            },
            "kde": {
                "x": kde_x.tolist(),
                "y": kde_y.tolist()
            },
            "qq_plot": {
                "sample": sample_list,
                "theoretical": theory_list
            }
        }
    
    def _range_behavior(self, arr: np.ndarray) -> Dict[str, Any]:
        """Analyze range and boundary behavior. ECDF capped at MAX_CHART_POINTS."""
        # ECDF (Empirical Cumulative Distribution Function)
        sorted_arr = np.sort(arr)
        ecdf_y = np.arange(1, len(sorted_arr) + 1) / len(sorted_arr)
        ecdf_x_list, ecdf_y_list = self._downsample(sorted_arr, ecdf_y, MAX_CHART_POINTS)
        
        # Boundary analysis
        min_val, max_val = arr.min(), arr.max()
        boundary_threshold = 0.01  # Consider values within 1% of boundaries
        near_min = np.sum(arr <= (min_val + boundary_threshold * (max_val - min_val)))
        near_max = np.sum(arr >= (max_val - boundary_threshold * (max_val - min_val)))
        
        # Edge histogram (zoomed into boundaries)
        edge_bins = 20
        edge_hist_counts, edge_hist_edges = np.histogram(
            arr, bins=edge_bins, range=(min_val, max_val)
        )
        
        return {
            "ecdf": {
                "x": ecdf_x_list,
                "y": ecdf_y_list
            },
            "boundaries": {
                "min": float(min_val),
                "max": float(max_val),
                "near_min_count": int(near_min),
                "near_max_count": int(near_max),
                "near_min_pct": float(near_min / len(arr) * 100),
                "near_max_pct": float(near_max / len(arr) * 100)
            },
            "edge_histogram": {
                "counts": edge_hist_counts.tolist(),
                "edges": edge_hist_edges.tolist()
            }
        }
    
    def _independence_analysis(self, arr: np.ndarray) -> Dict[str, Any]:
        """Analyze independence and correlation"""
        # Autocorrelation at different lags
        max_lag = min(50, len(arr) // 4)
        autocorrs = []
        lags = list(range(1, max_lag + 1))
        
        for lag in lags:
            if lag < len(arr):
                corr = np.corrcoef(arr[:-lag], arr[lag:])[0, 1]
                autocorrs.append(float(corr) if not np.isnan(corr) else 0.0)
            else:
                autocorrs.append(0.0)
        
        # Lag-1 scatter plot data (downsampled)
        lag1_x_arr = arr[:-1]
        lag1_y_arr = arr[1:]
        lag1_x_list, lag1_y_list = self._downsample(lag1_x_arr, lag1_y_arr, MAX_CHART_POINTS)
        
        # Time series data (downsampled)
        indices = np.arange(len(arr))
        idx_list = self._downsample_single(indices.astype(float), MAX_CHART_POINTS)
        values_list = self._downsample_single(arr, MAX_CHART_POINTS)
        
        return {
            "autocorrelation": {
                "lags": lags,
                "values": autocorrs
            },
            "lag1_scatter": {
                "x": lag1_x_list,
                "y": lag1_y_list
            },
            "time_series": {
                "index": idx_list,
                "values": values_list
            }
        }
    
    def _stationarity_analysis(self, arr: np.ndarray) -> Dict[str, Any]:
        """Analyze stationarity"""
        window_size = max(10, len(arr) // 20)
        
        # Rolling mean and variance
        df = pd.Series(arr)
        rolling_mean = df.rolling(window=window_size, center=True).mean()
        rolling_std = df.rolling(window=window_size, center=True).std()
        
        # Chunked analysis: divide into 4 chunks covering the full array (no dropped tail)
        chunks = np.array_split(arr, 4)
        
        chunk_stats = []
        for i, chunk in enumerate(chunks):
            if len(chunk) > 0:
                chunk_stats.append({
                    "chunk": i + 1,
                    "mean": float(np.mean(chunk)),
                    "std": float(np.std(chunk, ddof=1)) if len(chunk) > 1 else 0.0,
                    "min": float(np.min(chunk)),
                    "max": float(np.max(chunk))
                })
        
        # Downsample rolling series for visualization; drop NaN edges instead of filling with 0
        rolling_idx = np.arange(len(rolling_mean))
        valid = ~(np.isnan(rolling_mean.values) | np.isnan(rolling_std.values))
        idx_valid = rolling_idx[valid].astype(float)
        rm_valid_vals = rolling_mean.values[valid]
        rs_valid_vals = rolling_std.values[valid]
        rm_idx_list, rm_val_list = self._downsample(idx_valid, rm_valid_vals, MAX_CHART_POINTS)
        _, rs_val_list = self._downsample(idx_valid, rs_valid_vals, MAX_CHART_POINTS)
        
        return {
            "rolling_mean": {
                "index": rm_idx_list,
                "values": rm_val_list
            },
            "rolling_std": {
                "index": rm_idx_list,
                "values": rs_val_list
            },
            "chunks": chunk_stats
        }
    
    def _spectral_analysis(self, arr: np.ndarray) -> Dict[str, Any]:
        """Perform spectral analysis (FFT)"""
        # Remove mean for better FFT
        centered = arr - np.mean(arr)
        
        # Compute FFT
        fft_vals = fft(centered)
        fft_magnitude = np.abs(fft_vals)
        
        # Frequency domain
        n = len(arr)
        freqs = np.fft.fftfreq(n)
        
        # Only take positive frequencies
        positive_freq_idx = freqs > 0
        freqs_positive = freqs[positive_freq_idx]
        magnitude_positive = fft_magnitude[positive_freq_idx]
        
        # Periodogram (power spectrum), cap length for visualization
        power = magnitude_positive ** 2
        n_spec = min(len(freqs_positive), MAX_CHART_POINTS)
        if n_spec < len(freqs_positive):
            idx = np.linspace(0, len(freqs_positive) - 1, n_spec, dtype=int)
            idx = np.unique(idx)
            freqs_list = freqs_positive[idx].tolist()
            mag_list = magnitude_positive[idx].tolist()
            power_list = power[idx].tolist()
        else:
            freqs_list = freqs_positive.tolist()
            mag_list = magnitude_positive.tolist()
            power_list = power.tolist()
        
        return {
            "frequencies": freqs_list,
            "magnitude": mag_list,
            "power": power_list
        }
    
    def _numbers_to_binary(self, numbers: np.ndarray) -> List[int]:
        """Convert numbers to exact binary representation (IEEE 754 double precision)"""
        binary_sequence = []
        for num in numbers:
            # Convert to IEEE 754 double precision (64-bit) binary representation
            # Pack as double, then convert to binary string
            binary_bytes = struct.pack('>d', float(num))
            binary_bits = ''.join(format(byte, '08b') for byte in binary_bytes)
            # Add all bits to the sequence
            binary_sequence.extend([int(bit) for bit in binary_bits])
        return binary_sequence
    
    def _runs_test(self, binary_sequence: List[int]) -> Dict[str, Any]:
        """NIST Runs Test - tests for randomness by examining the total number of runs"""
        n = len(binary_sequence)
        if n < 2:
            return {"p_value": None, "statistic": None, "passed": False, "error": "Sequence too short"}
        
        # Count ones and zeros
        ones = sum(binary_sequence)
        zeros = n - ones
        
        if ones == 0 or zeros == 0:
            return {"p_value": None, "statistic": None, "passed": False, "error": "Sequence contains only one type of bit"}
        
        # Count runs (consecutive identical bits)
        runs = 1
        for i in range(1, n):
            if binary_sequence[i] != binary_sequence[i-1]:
                runs += 1
        
        # Expected number of runs
        expected_runs = (2 * ones * zeros) / n + 1
        
        # Variance
        variance = (2 * ones * zeros * (2 * ones * zeros - n)) / (n * n * (n - 1))
        
        if variance <= 0:
            return {"p_value": None, "statistic": None, "passed": False, "error": "Invalid variance"}
        
        # Z-statistic
        z_stat = (runs - expected_runs) / np.sqrt(variance)
        
        # Two-tailed test
        p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
        
        passed = p_value > 0.01  # NIST typically uses 0.01
        
        return {
            "p_value": float(p_value),
            "statistic": float(z_stat),
            "runs": int(runs),
            "expected_runs": float(expected_runs),
            "ones": int(ones),
            "zeros": int(zeros),
            "passed": bool(passed)
        }
    
    def _binary_matrix_rank_test(self, binary_sequence: List[int], matrix_size: int = 32) -> Dict[str, Any]:
        """NIST Binary Matrix Rank Test - tests for linear dependence among fixed-length substrings.
        Expected probabilities are only defined for 32x32 in this implementation."""
        if matrix_size != 32:
            return {"p_value": None, "statistic": None, "passed": False, "error": "Only matrix_size=32 is supported (NIST expected probabilities are for 32x32)"}
        n = len(binary_sequence)
        min_required = matrix_size * matrix_size
        if n < min_required:
            return {"p_value": None, "statistic": None, "passed": False, "error": f"Sequence too short (need at least {min_required} bits)"}
        
        # Number of matrices
        num_matrices = n // (matrix_size * matrix_size)
        if num_matrices < 1:
            return {"p_value": None, "statistic": None, "passed": False, "error": "Cannot form any matrices"}
        
        # Count ranks
        rank_counts = {matrix_size: 0, matrix_size - 1: 0, 0: 0}  # Full rank, rank-1, rank-0
        
        for i in range(num_matrices):
            start_idx = i * matrix_size * matrix_size
            # Extract matrix
            matrix = []
            for row in range(matrix_size):
                row_start = start_idx + row * matrix_size
                matrix.append(binary_sequence[row_start:row_start + matrix_size])
            
            # Convert to numpy array and compute rank
            matrix_arr = np.array(matrix, dtype=int)
            rank = np.linalg.matrix_rank(matrix_arr)
            
            if rank == matrix_size:
                rank_counts[matrix_size] += 1
            elif rank == matrix_size - 1:
                rank_counts[matrix_size - 1] += 1
            else:
                rank_counts[0] += 1
        
        # Expected frequencies (approximate for 32x32 matrices)
        # For full rank: ~0.2888, for rank-1: ~0.5776, for rank-0: ~0.1336
        # These are approximate values for 32x32 binary matrices
        p_full = 0.2888
        p_rank_minus_1 = 0.5776
        p_rank_0 = 0.1336
        
        expected_full = num_matrices * p_full
        expected_rank_minus_1 = num_matrices * p_rank_minus_1
        expected_rank_0 = num_matrices * p_rank_0
        
        # Chi-square statistic
        chi_square = (
            ((rank_counts[matrix_size] - expected_full) ** 2) / expected_full +
            ((rank_counts[matrix_size - 1] - expected_rank_minus_1) ** 2) / expected_rank_minus_1 +
            ((rank_counts[0] - expected_rank_0) ** 2) / expected_rank_0
        )
        
        # Degrees of freedom = 2 (3 categories - 1)
        p_value = 1 - chi2.cdf(chi_square, 2)
        
        passed = p_value > 0.01
        
        return {
            "p_value": float(p_value),
            "statistic": float(chi_square),
            "num_matrices": int(num_matrices),
            "full_rank_count": int(rank_counts[matrix_size]),
            "rank_minus_1_count": int(rank_counts[matrix_size - 1]),
            "rank_0_count": int(rank_counts[0]),
            "passed": bool(passed)
        }
    
    def _longest_run_of_ones_test(self, binary_sequence: List[int], block_size: int = 128) -> Dict[str, Any]:
        """NIST Longest Run of Ones Test - examines the longest consecutive sequence of 1s within blocks.
        Expected frequencies are only defined for block_size=128 in this implementation."""
        if block_size != 128:
            return {"p_value": None, "statistic": None, "passed": False, "error": "Only block_size=128 is supported (NIST expected frequencies are for M=128)"}
        n = len(binary_sequence)
        if n < block_size:
            return {"p_value": None, "statistic": None, "passed": False, "error": f"Sequence too short (need at least {block_size} bits)"}
        
        num_blocks = n // block_size
        if num_blocks < 1:
            return {"p_value": None, "statistic": None, "passed": False, "error": "Cannot form any blocks"}
        
        # Expected frequencies for run lengths (NIST SP 800-22, block_size=128)
        run_lengths = [4, 5, 6, 7, 8, 9]  # Run lengths <= 4, 5, 6, 7, 8, >=9
        expected_freqs = [0.1174, 0.2430, 0.2493, 0.1752, 0.1027, 0.1124]
        
        # Count longest runs in each block
        run_counts = {length: 0 for length in run_lengths}
        
        for i in range(num_blocks):
            start_idx = i * block_size
            block = binary_sequence[start_idx:start_idx + block_size]
            
            # Find longest run of ones
            max_run = 0
            current_run = 0
            for bit in block:
                if bit == 1:
                    current_run += 1
                    max_run = max(max_run, current_run)
                else:
                    current_run = 0
            
            # Categorize
            if max_run <= 4:
                run_counts[4] += 1
            elif max_run == 5:
                run_counts[5] += 1
            elif max_run == 6:
                run_counts[6] += 1
            elif max_run == 7:
                run_counts[7] += 1
            elif max_run == 8:
                run_counts[8] += 1
            else:  # >= 9
                run_counts[9] += 1
        
        # Chi-square statistic
        chi_square = 0.0
        for length in run_lengths:
            expected = num_blocks * expected_freqs[run_lengths.index(length)]
            observed = run_counts[length]
            if expected > 0:
                chi_square += ((observed - expected) ** 2) / expected
        
        # Degrees of freedom = 5 (6 categories - 1)
        p_value = 1 - chi2.cdf(chi_square, 5)
        
        passed = p_value > 0.01
        
        return {
            "p_value": float(p_value),
            "statistic": float(chi_square),
            "num_blocks": int(num_blocks),
            "run_counts": {str(k): int(v) for k, v in run_counts.items()},
            "passed": bool(passed)
        }
    
    def _approximate_entropy_test(self, binary_sequence: List[int], m: int = 2) -> Dict[str, Any]:
        """NIST Approximate Entropy Test - uses NIST SP 800-22 formula: chi2 = 2*n*(ln2 - ApEn), df = 2^m."""
        n = len(binary_sequence)
        min_required = 10 * (2 ** m)  # NIST recommends at least 10 * 2^m bits
        if n < min_required:
            return {"p_value": None, "statistic": None, "passed": False, "error": f"Sequence too short (need at least {min_required} bits for m={m})"}
        
        def count_patterns(pattern_length):
            pattern_counts = {}
            num_patterns = n - pattern_length + 1
            for i in range(num_patterns):
                pattern = tuple(binary_sequence[i:i + pattern_length])
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
            return pattern_counts, num_patterns
        
        patterns_m, num_patterns_m = count_patterns(m)
        patterns_m1, num_patterns_m1 = count_patterns(m + 1)
        
        def calculate_phi(pattern_counts, num_patterns):
            phi = 0.0
            for pattern, count in pattern_counts.items():
                if count > 0:
                    prob = count / num_patterns
                    phi += prob * np.log(prob + 1e-10)
            return phi
        
        phi_m = calculate_phi(patterns_m, num_patterns_m)
        phi_m1 = calculate_phi(patterns_m1, num_patterns_m1)
        ap_en = phi_m - phi_m1
        
        # NIST SP 800-22: chi2 = 2*n*(ln2 - ApEn), degrees of freedom = 2^m
        ln2 = np.log(2)
        chi2_stat = 2.0 * n * (ln2 - ap_en)
        if chi2_stat < 0:
            chi2_stat = 0.0
        df = 2 ** m
        p_value = float(1 - chi2.cdf(chi2_stat, df))
        passed = p_value > 0.01
        
        return {
            "p_value": float(p_value),
            "statistic": float(chi2_stat),
            "approximate_entropy": float(ap_en),
            "phi_m": float(phi_m),
            "phi_m1": float(phi_m1),
            "pattern_length_m": int(m),
            "pattern_length_m1": int(m + 1),
            "num_patterns_m": int(num_patterns_m),
            "num_patterns_m1": int(num_patterns_m1),
            "unique_patterns_m": int(len(patterns_m)),
            "unique_patterns_m1": int(len(patterns_m1)),
            "passed": bool(passed)
        }
    
    def _nist_tests(self, arr: np.ndarray) -> Dict[str, Any]:
        """Perform NIST statistical tests on binary representation of numbers"""
        # Convert to binary
        binary_sequence = self._numbers_to_binary(arr)
        
        # Run tests
        runs_result = self._runs_test(binary_sequence)
        matrix_rank_result = self._binary_matrix_rank_test(binary_sequence)
        longest_run_result = self._longest_run_of_ones_test(binary_sequence)
        approximate_entropy_result = self._approximate_entropy_test(binary_sequence)
        
        return {
            "runs_test": runs_result,
            "binary_matrix_rank_test": matrix_rank_result,
            "longest_run_of_ones_test": longest_run_result,
            "approximate_entropy_test": approximate_entropy_result,
            "binary_sequence_length": len(binary_sequence)
        }
    
    def analyze_multi_run(self, runs: List[List[float]], provider: str, num_runs: int) -> Dict[str, Any]:
        """Perform comprehensive statistical analysis across multiple runs"""
        if not runs or len(runs) == 0:
            raise ValueError("No runs provided")
        
        # Validate runs
        for idx, run in enumerate(runs):
            if not run or len(run) == 0:
                raise ValueError(f"Run {idx + 1} is empty")
            if not all(isinstance(x, (int, float)) for x in run):
                raise ValueError(f"Run {idx + 1} contains non-numeric values")
        
        # Analyze each run individually
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
            
            # Skip if array is invalid
            if len(arr) == 0 or np.any(np.isnan(arr)) or np.any(np.isinf(arr)):
                continue
            
            # Basic stats for this run
            run_mean = float(np.mean(arr))
            run_std = float(np.std(arr))
            run_skewness = float(stats.skew(arr))
            run_kurtosis = float(stats.kurtosis(arr))
            
            means.append(run_mean)
            std_devs.append(run_std)
            skewnesses.append(run_skewness)
            kurtoses.append(run_kurtosis)
            
            # Test results - Uniformity test (Kolmogorov-Smirnov)
            min_val = float(arr.min())
            max_val = float(arr.max())
            ks_stat, ks_p = kstest(arr, 'uniform', args=(min_val, max_val - min_val))
            ks_passed.append(ks_p > 0.05)
            
            # NIST tests
            nist_results = self._nist_tests(arr)
            runs_test_passed.append(nist_results.get("runs_test", {}).get("passed", False))
            matrix_rank_test_passed.append(nist_results.get("binary_matrix_rank_test", {}).get("passed", False))
            longest_run_test_passed.append(nist_results.get("longest_run_of_ones_test", {}).get("passed", False))
            approximate_entropy_test_passed.append(nist_results.get("approximate_entropy_test", {}).get("passed", False))
            
            # Autocorrelation analysis
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
                        # Check for significance (using approximate threshold)
                        if abs_corr > 0.2:  # Threshold for significance
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
            
            # ECDF data for this run (downsampled for visualization)
            sorted_arr = np.sort(arr)
            ecdf_y = np.arange(1, len(sorted_arr) + 1) / len(sorted_arr)
            ecdf_x_list, ecdf_y_list = self._downsample(sorted_arr, ecdf_y, MAX_CHART_POINTS)
            all_ecdf_data.append({
                "run": int(run_idx + 1),
                "x": [float(x) for x in ecdf_x_list],
                "y": [float(y) for y in ecdf_y_list]
            })
            
            # Full analysis for this run
            individual_analyses.append(self.analyze(run_numbers, provider))
        
        # Validate we have data to analyze
        if len(means) == 0:
            raise ValueError("No valid runs to analyze")
        
        # Convert to numpy arrays for statistics
        means_arr = np.array(means)
        std_devs_arr = np.array(std_devs)
        skewnesses_arr = np.array(skewnesses)
        kurtoses_arr = np.array(kurtoses)
        modes = [a.get("basic_stats", {}).get("mode", np.nan) for a in individual_analyses]
        modes_arr = np.array([m for m in modes if not (isinstance(m, float) and np.isnan(m))], dtype=float)
        if len(modes_arr) == 0:
            modes_arr = np.array(means_arr)  # fallback so structure exists
        
        # Helper function to calculate stats across runs for a metric
        def calc_metric_stats(metric_arr):
            if len(metric_arr) == 0:
                return {"mean": 0.0, "std_dev": 0.0, "range": 0.0}
            mean_val = float(np.mean(metric_arr))
            std_dev_val = float(np.std(metric_arr)) if len(metric_arr) > 1 else 0.0
            range_val = float(np.max(metric_arr) - np.min(metric_arr))
            return {
                "mean": mean_val,
                "std_dev": std_dev_val,
                "range": range_val
            }
        
        # Calculate aggregate statistics in new format
        aggregate_stats = {
            "mean": calc_metric_stats(means_arr),
            "std_dev": calc_metric_stats(std_devs_arr),
            "skewness": calc_metric_stats(skewnesses_arr),
            "kurtosis": calc_metric_stats(kurtoses_arr),
            "mode": calc_metric_stats(modes_arr),
        }
        
        # Test pass counts
        ks_passed_count = int(sum(ks_passed))
        runs_test_passed_count = int(sum(runs_test_passed))
        matrix_rank_test_passed_count = int(sum(matrix_rank_test_passed))
        longest_run_test_passed_count = int(sum(longest_run_test_passed))
        approximate_entropy_test_passed_count = int(sum(approximate_entropy_test_passed))
        
        # Calculate frequency histogram across all runs
        # Combine all numbers from all runs
        all_numbers = []
        for run_numbers in runs:
            all_numbers.extend(run_numbers)
        
        all_numbers_arr = np.array(all_numbers)
        
        # Statistics treating all numbers across all runs as a single stream
        combined_stream_stats = self._convert_numpy_types(self._basic_stats(all_numbers_arr)) if len(all_numbers_arr) > 0 else {}
        
        # Calculate frequency histogram
        # Use bins to handle continuous data - use 50 bins by default
        min_val = float(np.min(all_numbers_arr))
        max_val = float(np.max(all_numbers_arr))
        num_bins = min(50, len(np.unique(all_numbers_arr)))  # Use unique count if less than 50
        
        if num_bins > 0:
            counts, bin_edges = np.histogram(all_numbers_arr, bins=num_bins)
            bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
            
            frequency_histogram = {
                "bins": [float(x) for x in bin_centers.tolist()],
                "frequencies": [int(x) for x in counts.tolist()],
                "bin_edges": [float(x) for x in bin_edges.tolist()]
            }
        else:
            frequency_histogram = {
                "bins": [],
                "frequencies": [],
                "bin_edges": []
            }
        
        # Combined KDE across all runs (Phase 6 - for frontend KDE view)
        n_kde = min(MAX_CHART_POINTS, len(all_numbers_arr) + 1)
        combined_kde_x = np.linspace(min_val, max_val, n_kde)
        combined_kde_y = stats.gaussian_kde(all_numbers_arr)(combined_kde_x)
        combined_kde = {
            "x": [float(x) for x in combined_kde_x.tolist()],
            "y": [float(y) for y in combined_kde_y.tolist()]
        }
        
        # Convert aggregate_stats to ensure all numpy types are converted
        converted_aggregate_stats = self._convert_numpy_types(aggregate_stats)

        # Distribution deviation metrics (ECDF and Q-Q) across runs
        distribution_deviation = self._compute_distribution_deviation_metrics(runs)
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
        
        # Include individual_analyses with proper numpy type conversion
        converted_individual_analyses = []
        for analysis in individual_analyses:
            converted_analysis = self._convert_numpy_types(analysis)
            converted_individual_analyses.append(converted_analysis)
        result["individual_analyses"] = converted_individual_analyses
        
        return result
