"""Range and boundary behavior analysis."""
import numpy as np
from typing import Dict, Any

from .utils import downsample, MAX_CHART_POINTS


def range_behavior(arr: np.ndarray) -> Dict[str, Any]:
    """Analyze range and boundary behavior. ECDF capped at MAX_CHART_POINTS."""
    sorted_arr = np.sort(arr)
    ecdf_y = np.arange(1, len(sorted_arr) + 1) / len(sorted_arr)
    ecdf_x_list, ecdf_y_list = downsample(sorted_arr, ecdf_y, MAX_CHART_POINTS)
    min_val, max_val = arr.min(), arr.max()
    boundary_threshold = 0.01
    near_min = np.sum(arr <= (min_val + boundary_threshold * (max_val - min_val)))
    near_max = np.sum(arr >= (max_val - boundary_threshold * (max_val - min_val)))
    edge_bins = 20
    edge_hist_counts, edge_hist_edges = np.histogram(
        arr, bins=edge_bins, range=(min_val, max_val)
    )
    return {
        "ecdf": {"x": ecdf_x_list, "y": ecdf_y_list},
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
