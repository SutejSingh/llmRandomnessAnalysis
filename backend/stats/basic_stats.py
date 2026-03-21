"""Basic descriptive statistics."""
import numpy as np
from scipy import stats
from typing import Dict

from .utils import is_constant_sample


def basic_stats(arr: np.ndarray) -> Dict[str, float]:
    """Calculate basic descriptive statistics (sample variance/std with ddof=1)."""
    q50 = float(np.percentile(arr, 50))  # same as median (used for both median and q50)
    if len(arr) == 0:
        mode_val = float("nan")
    else:
        mode_val = float(stats.mode(arr, keepdims=False).mode)
    return {
        "mean": float(np.mean(arr)),
        "median": q50,
        "mode": mode_val,
        "std": float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0,
        "variance": float(np.var(arr, ddof=1)) if len(arr) > 1 else 0.0,
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "q25": float(np.percentile(arr, 25, method="higher")),
        "q50": q50,
        "q75": float(np.percentile(arr, 75, method="higher")),
        "q95": float(np.percentile(arr, 95, method="higher")),
        # Degenerate spread: sample skew/kurtosis divide by powers of s; undefined when s≈0.
        # Report NaN (JSON null after conversion) so UI shows N/A, not a misleading 0.
        "skewness": (
            float("nan") if is_constant_sample(arr) else float(stats.skew(arr))
        ),
        "kurtosis": (
            float("nan") if is_constant_sample(arr) else float(stats.kurtosis(arr))
        ),
    }
