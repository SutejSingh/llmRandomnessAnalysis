"""Stationarity analysis (rolling stats, chunks)."""
import numpy as np
import pandas as pd
from typing import Dict, Any

from .utils import downsample, MAX_CHART_POINTS


def stationarity_analysis(arr: np.ndarray) -> Dict[str, Any]:
    """Analyze stationarity."""
    window_size = max(10, len(arr) // 20)
    df = pd.Series(arr)
    rolling_mean = df.rolling(window=window_size, center=True).mean()
    rolling_std = df.rolling(window=window_size, center=True).std()
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
    rolling_idx = np.arange(len(rolling_mean))
    valid = ~(np.isnan(rolling_mean.values) | np.isnan(rolling_std.values))
    idx_valid = rolling_idx[valid].astype(float)
    rm_valid_vals = rolling_mean.values[valid]
    rs_valid_vals = rolling_std.values[valid]
    rm_idx_list, rm_val_list = downsample(idx_valid, rm_valid_vals, MAX_CHART_POINTS)
    _, rs_val_list = downsample(idx_valid, rs_valid_vals, MAX_CHART_POINTS)
    return {
        "rolling_mean": {"index": rm_idx_list, "values": rm_val_list},
        "rolling_std": {"index": rm_idx_list, "values": rs_val_list},
        "chunks": chunk_stats
    }
