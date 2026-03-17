"""Distribution analysis: uniformity, ECDF, Q-Q, deviation metrics."""
import numpy as np
from scipy import stats
from scipy.stats import kstest
from typing import Dict, Any, List

from .utils import downsample, MAX_CHART_POINTS


def normalize_to_unit(arr: np.ndarray) -> np.ndarray:
    """Normalize array to [0, 1] using min/max of the run."""
    if len(arr) == 0:
        return arr
    lo, hi = arr.min(), arr.max()
    if hi <= lo:
        return np.full_like(arr, 0.5, dtype=float)
    return (arr - lo) / (hi - lo)


def ecdf_ks_statistic_normalized(u: np.ndarray) -> float:
    """Max vertical deviation (K-S statistic) for uniform [0,1]."""
    if len(u) == 0:
        return float('nan')
    u = np.asarray(u, dtype=float)
    if u.ndim > 1:
        u = u.ravel()
    u = np.sort(u)
    n = len(u)
    empirical = np.arange(1, n + 1, dtype=float) / n
    theoretical = u
    dev = np.abs(empirical - theoretical)
    dev_left = np.abs(np.arange(0, n, dtype=float) / n - theoretical)
    return float(np.max(np.maximum(dev, dev_left)))


def ecdf_mad_normalized(u: np.ndarray) -> float:
    """Mean absolute deviation: mean(|F_empirical - F_theoretical|)."""
    if len(u) == 0:
        return float('nan')
    u = np.asarray(u, dtype=float).ravel()
    u = np.sort(u)
    n = len(u)
    empirical = np.arange(1, n + 1, dtype=float) / n
    theoretical = u
    return float(np.mean(np.abs(empirical - theoretical)))


def ecdf_regional_deviation(u: np.ndarray, regions: int = 5) -> List[float]:
    """Break [0,1] into equal regions and compute mean absolute deviation in each."""
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
        is_last = i == regions - 1
        mask = (u >= low) & (u <= high) if is_last else (u >= low) & (u < high)
        if np.any(mask):
            out.append(float(np.mean(abs_dev[mask])))
        else:
            out.append(0.0)
    return out


def qq_r_squared_normalized(u: np.ndarray) -> float:
    """R² for Q-Q plot vs uniform (Blom theoretical quantiles)."""
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


def qq_mse_normalized(u: np.ndarray) -> float:
    """Mean squared error from diagonal in Q-Q plot."""
    if len(u) == 0:
        return float('nan')
    u = np.asarray(u, dtype=float).ravel()
    u = np.sort(u)
    n = len(u)
    theoretical = (np.arange(1, n + 1, dtype=float) - 0.5) / n
    return float(np.mean((u - theoretical) ** 2))


def empty_deviation_metrics() -> Dict[str, Any]:
    """Empty structure for distribution deviation metrics."""
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


def compute_distribution_deviation_metrics(runs: List[List[float]]) -> Dict[str, Any]:
    """Compute ECDF and Q-Q deviation metrics across runs (normalized to [0,1] per run)."""
    if not runs:
        return empty_deviation_metrics()
    ks_list = []
    mad_list = []
    regional_list = []
    r2_list = []
    mse_list = []
    for run in runs:
        arr = np.array(run, dtype=float)
        if len(arr) == 0 or np.any(np.isnan(arr)) or np.any(np.isinf(arr)):
            continue
        u = normalize_to_unit(arr)
        if len(u) < 2:
            continue
        ks_list.append(ecdf_ks_statistic_normalized(u))
        mad_list.append(ecdf_mad_normalized(u))
        regional_list.append(ecdf_regional_deviation(u, regions=5))
        r2_list.append(qq_r_squared_normalized(u))
        mse_list.append(qq_mse_normalized(u))
    if not ks_list:
        return empty_deviation_metrics()
    ks_arr = np.array(ks_list)
    mad_arr = np.array(mad_list)
    r2_arr = np.array(r2_list)
    mse_arr = np.array(mse_list)
    regional_arr = np.array(regional_list)
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


def distribution_analysis(arr: np.ndarray) -> Dict[str, Any]:
    """Analyze distribution shape. Chart data capped at MAX_CHART_POINTS."""
    min_val = float(arr.min())
    max_val = float(arr.max())
    ks_stat, ks_p = kstest(arr, 'uniform', args=(min_val, max_val - min_val))
    hist_counts, hist_edges = np.histogram(arr, bins=50)
    n_kde = min(MAX_CHART_POINTS, len(arr) + 1)
    kde_x = np.linspace(arr.min(), arr.max(), n_kde)
    kde_y = stats.gaussian_kde(arr)(kde_x)
    sorted_arr = np.sort(arr)
    theoretical_quantiles = stats.uniform.ppf(
        np.linspace(0.01, 0.99, len(sorted_arr)),
        loc=min_val,
        scale=max_val - min_val
    )
    sample_list, theory_list = downsample(
        sorted_arr, np.array(theoretical_quantiles), MAX_CHART_POINTS
    )
    return {
        "is_uniform": {"ks_stat": float(ks_stat), "ks_p": float(ks_p)},
        "histogram": {"counts": hist_counts.tolist(), "edges": hist_edges.tolist()},
        "kde": {"x": kde_x.tolist(), "y": kde_y.tolist()},
        "qq_plot": {"sample": sample_list, "theoretical": theory_list}
    }
