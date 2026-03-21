"""Shared utilities for statistics: downsampling and type conversion."""
import math
import numpy as np
from typing import List, Tuple, Any

MAX_CHART_POINTS = 5000


def is_constant_sample(arr: np.ndarray) -> bool:
    """
    True when the sample is degenerate for spread-based statistics: fewer than 2 points,
    exact constants, or near-constant (range negligible vs magnitude).

    Used to avoid scipy.stats.skew/kurtosis (we report NaN instead), scipy.stats.kstest
    on Uniform(loc, scale) with scale==0, and numpy.corrcoef with zero variance.
    """
    arr = np.asarray(arr, dtype=float).ravel()
    if arr.size < 2:
        return True
    if not np.all(np.isfinite(arr)):
        return False
    ptp = float(np.ptp(arr))
    if ptp == 0.0:
        return True
    ref_scale = max(float(np.max(np.abs(arr))), 1.0)
    # Near-constant: avoids scipy "nearly identical" moment warnings
    if ptp <= 1e-12 * ref_scale:
        return True
    return False


def _json_safe_float(f: float) -> Any:
    """JSON cannot encode NaN or Infinity; emit null for those."""
    if math.isnan(f) or math.isinf(f):
        return None
    return f


def convert_numpy_types(obj: Any) -> Any:
    """Recursively convert numpy types to Python native types."""
    if isinstance(obj, (np.integer, np.int_, np.intc, np.intp, np.int8,
                       np.int16, np.int32, np.int64, np.uint8, np.uint16,
                       np.uint32, np.uint64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float_, np.float16, np.float32, np.float64)):
        return _json_safe_float(float(obj))
    elif isinstance(obj, np.ndarray):
        return [convert_numpy_types(item) for item in obj.tolist()]
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, float):
        return _json_safe_float(obj)
    else:
        return obj


def downsample(x: np.ndarray, y: np.ndarray, max_points: int) -> Tuple[List[float], List[float]]:
    """Downsample two equal-length arrays to at most max_points, preserving first and last."""
    n = len(x)
    if n <= max_points:
        return x.tolist(), y.tolist()
    indices = np.linspace(0, n - 1, max_points, dtype=int)
    indices = np.unique(indices)
    if indices[-1] != n - 1:
        indices = np.append(indices, n - 1)
    return x[indices].tolist(), y[indices].tolist()


def downsample_single(arr: np.ndarray, max_points: int) -> List[float]:
    """Downsample a single array to at most max_points, preserving first and last."""
    n = len(arr)
    if n <= max_points:
        return arr.tolist()
    indices = np.linspace(0, n - 1, max_points, dtype=int)
    indices = np.unique(indices)
    if indices[-1] != n - 1:
        indices = np.append(indices, n - 1)
    return arr[indices].tolist()
