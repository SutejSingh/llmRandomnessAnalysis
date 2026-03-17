"""Spectral analysis (FFT)."""
import numpy as np
from scipy.fft import fft
from typing import Dict, Any

from .utils import MAX_CHART_POINTS


def spectral_analysis(arr: np.ndarray) -> Dict[str, Any]:
    """Perform spectral analysis (FFT)."""
    centered = arr - np.mean(arr)
    fft_vals = fft(centered)
    fft_magnitude = np.abs(fft_vals)
    n = len(arr)
    freqs = np.fft.fftfreq(n)
    positive_freq_idx = freqs > 0
    freqs_positive = freqs[positive_freq_idx]
    magnitude_positive = fft_magnitude[positive_freq_idx]
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
