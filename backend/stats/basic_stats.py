"""Basic descriptive statistics."""
import numpy as np
from scipy import stats
from typing import Dict

def is_integer_like(arr: np.ndarray) -> bool:
    """True if all values are integers (or whole-number floats)."""
    if len(arr) == 0:
        return False
    arr = np.asarray(arr, dtype=float)
    if not np.all(np.isfinite(arr)):
        return False
    return np.all(arr == np.round(arr))


def mode_discrete(arr: np.ndarray) -> float:
    """Mode for discrete data: most frequent value. Tie-break: smallest."""
    if len(arr) == 0:
        return float('nan')
    vals, counts = np.unique(arr, return_counts=True)
    max_count = np.max(counts)
    modes = vals[counts == max_count]
    return float(modes.min())


def mode_continuous(arr: np.ndarray, bins: int = 50) -> float:
    """Mode for continuous data: midpoint of the histogram bin with highest count."""
    if len(arr) == 0:
        return float('nan')
    counts, edges = np.histogram(arr, bins=min(bins, max(1, len(arr))))
    if np.max(counts) == 0:
        return float(np.median(arr))
    i = np.argmax(counts)
    return float((edges[i] + edges[i + 1]) / 2)


def basic_stats(arr: np.ndarray) -> Dict[str, float]:
    """Calculate basic descriptive statistics (sample variance/std with ddof=1)."""
    discrete = is_integer_like(arr)
    if discrete:
        median = float(np.percentile(arr, 50, method='lower'))
        q25 = float(np.percentile(arr, 25, method='lower'))
        q50 = float(np.percentile(arr, 50, method='lower'))
        q75 = float(np.percentile(arr, 75, method='lower'))
        q95 = float(np.percentile(arr, 95, method='lower'))
        mode = mode_discrete(arr)
    else:
        median = float(np.median(arr))
        q25 = float(np.percentile(arr, 25))
        q50 = float(np.percentile(arr, 50))
        q75 = float(np.percentile(arr, 75))
        q95 = float(np.percentile(arr, 95))
        mode = mode_continuous(arr)
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
