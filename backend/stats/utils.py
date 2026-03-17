"""Shared utilities for statistics: downsampling and type conversion."""
import numpy as np
from typing import List, Tuple, Any

MAX_CHART_POINTS = 5000


def convert_numpy_types(obj: Any) -> Any:
    """Recursively convert numpy types to Python native types."""
    if isinstance(obj, (np.integer, np.int_, np.intc, np.intp, np.int8,
                       np.int16, np.int32, np.int64, np.uint8, np.uint16,
                       np.uint32, np.uint64)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float_, np.float16, np.float32, np.float64)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return [convert_numpy_types(item) for item in obj.tolist()]
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_numpy_types(item) for item in obj]
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
