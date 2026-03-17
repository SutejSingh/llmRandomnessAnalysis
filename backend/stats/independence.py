"""Independence and autocorrelation analysis."""
import numpy as np
from typing import Dict, Any

from .utils import downsample, downsample_single, MAX_CHART_POINTS


def independence_analysis(arr: np.ndarray) -> Dict[str, Any]:
    """Analyze independence and correlation."""
    max_lag = min(50, len(arr) // 4)
    autocorrs = []
    lags = list(range(1, max_lag + 1))
    for lag in lags:
        if lag < len(arr):
            corr = np.corrcoef(arr[:-lag], arr[lag:])[0, 1]
            autocorrs.append(float(corr) if not np.isnan(corr) else 0.0)
        else:
            autocorrs.append(0.0)
    lag1_x_arr = arr[:-1]
    lag1_y_arr = arr[1:]
    lag1_x_list, lag1_y_list = downsample(lag1_x_arr, lag1_y_arr, MAX_CHART_POINTS)
    indices = np.arange(len(arr))
    idx_list = downsample_single(indices.astype(float), MAX_CHART_POINTS)
    values_list = downsample_single(arr, MAX_CHART_POINTS)
    return {
        "autocorrelation": {"lags": lags, "values": autocorrs},
        "lag1_scatter": {"x": lag1_x_list, "y": lag1_y_list},
        "time_series": {"index": idx_list, "values": values_list}
    }
