"""LaTeX chart generation (matplotlib figures) for the PDF report."""
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from typing import Dict, Any, Optional


def generate_overlaid_ecdf_chart(analysis: Dict[str, Any], temp_dir: str) -> Optional[str]:
    """Generate overlaid ECDF chart with reference line."""
    ecdf_all_runs = analysis.get("ecdf_all_runs", [])
    if not ecdf_all_runs:
        return None
    fig, ax = plt.subplots(figsize=(10, 6))
    colors_list = plt.cm.tab10(np.linspace(0, 1, max(10, len(ecdf_all_runs))))
    for idx, run_data in enumerate(ecdf_all_runs):
        run_x = run_data.get("x", [])
        run_y = run_data.get("y", [])
        if run_x and run_y:
            step = max(1, len(run_x) // 1000) if len(run_x) > 1000 else 1
            run_num = run_data.get("run", idx + 1)
            color = colors_list[idx]
            ax.plot(run_x[::step], run_y[::step], linewidth=1.5, color=color, label=f'Run {run_num}', alpha=0.7)
    all_x_values = []
    for r in ecdf_all_runs:
        if r.get("x"):
            all_x_values.extend(r.get("x", []))
    if all_x_values:
        min_x, max_x = min(all_x_values), max(all_x_values)
        ax.plot([min_x, max_x], [0, 1], 'k--', linewidth=2, label='Uniform Distribution', alpha=0.8)
    ax.set_xlabel('Value')
    ax.set_ylabel('Cumulative Probability')
    ax.set_title('Overlaid ECDF Plot with Reference Line for Uniform Distribution')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_ylim([0, 1])
    filename = "ecdf_overlaid.png"
    filepath = os.path.join(temp_dir, filename)
    fig.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return filename


def generate_overlaid_qq_chart(analysis: Dict[str, Any], temp_dir: str) -> Optional[str]:
    """Generate overlaid Q-Q plot with reference line."""
    individual_analyses = analysis.get("individual_analyses", [])
    if not individual_analyses:
        return None
    fig, ax = plt.subplots(figsize=(10, 10))
    colors_list = plt.cm.tab10(np.linspace(0, 1, max(10, len(individual_analyses))))
    for idx, run_analysis in enumerate(individual_analyses):
        if "distribution" in run_analysis and "qq_plot" in run_analysis["distribution"]:
            theoretical = run_analysis["distribution"]["qq_plot"].get("theoretical", [])
            sample = run_analysis["distribution"]["qq_plot"].get("sample", [])
            if theoretical and sample:
                step = max(1, len(theoretical) // 500) if len(theoretical) > 500 else 1
                color = colors_list[idx]
                ax.scatter(theoretical[::step], sample[::step], alpha=0.3, s=15, color=color,
                           edgecolors='black', linewidth=0.3, label=f'Run {idx + 1}')
    ax.plot([0, 1], [0, 1], 'r--', linewidth=2, label='y=x (Uniform Reference)')
    ax.set_xlabel('Theoretical Quantiles (Uniform)')
    ax.set_ylabel('Sample Quantiles')
    ax.set_title('Overlaid Q-Q Plot with Reference Line for Uniform Distribution')
    ax.legend()
    ax.grid(True, alpha=0.3)
    filename = "qq_overlaid.png"
    filepath = os.path.join(temp_dir, filename)
    fig.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return filename


def generate_frequency_histogram_chart(analysis: Dict[str, Any], temp_dir: str) -> Optional[str]:
    """Generate frequency histogram chart across all runs."""
    frequency_histogram = analysis.get("frequency_histogram", {})
    bins = frequency_histogram.get("bins", [])
    frequencies = frequency_histogram.get("frequencies", [])
    bin_edges = frequency_histogram.get("bin_edges", [])
    if not bins or not frequencies or len(bins) == 0:
        return None
    fig, ax = plt.subplots(figsize=(10, 6))
    if bin_edges and len(bin_edges) > 1:
        widths = [bin_edges[i+1] - bin_edges[i] for i in range(len(bin_edges)-1)]
        ax.bar(bins, frequencies, width=widths, color='steelblue', edgecolor='black', alpha=0.7, align='center')
    else:
        avg_width = (max(bins) - min(bins)) / len(bins) * 0.8 if len(bins) > 1 else 0.01
        ax.bar(bins, frequencies, width=avg_width, color='steelblue', edgecolor='black', alpha=0.7)
    ax.set_xlabel('Value (Bin Center)')
    ax.set_ylabel('Frequency')
    ax.set_title('Frequency Histogram Across All Runs')
    ax.grid(True, alpha=0.3, axis='y')
    if len(bins) > 20:
        plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    filename = "frequency_histogram.png"
    filepath = os.path.join(temp_dir, filename)
    fig.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return filename


def generate_kde_chart(kde_data: Dict[str, Any], run_num: int, temp_dir: str) -> Optional[str]:
    """Generate KDE chart."""
    kde_x = kde_data.get("x", [])
    kde_y = kde_data.get("y", [])
    if not kde_x or not kde_y:
        return None
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(kde_x, kde_y, linewidth=2, color='darkblue')
    ax.fill_between(kde_x, kde_y, alpha=0.3, color='steelblue')
    ax.set_xlabel('Value')
    ax.set_ylabel('Density')
    ax.set_title('Kernel Density Estimate (KDE)')
    ax.grid(True, alpha=0.3)
    filename = f"kde_run{run_num}.png"
    filepath = os.path.join(temp_dir, filename)
    fig.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return filename


def generate_ecdf_chart(ecdf_data: Dict[str, Any], run_num: int, temp_dir: str) -> Optional[str]:
    """Generate ECDF chart."""
    ecdf_x = ecdf_data.get("x", [])
    ecdf_y = ecdf_data.get("y", [])
    if not ecdf_x or not ecdf_y:
        return None
    step = max(1, len(ecdf_x) // 1000) if len(ecdf_x) > 1000 else 1
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(ecdf_x[::step], ecdf_y[::step], linewidth=2, color='darkblue')
    ax.set_xlabel('Value')
    ax.set_ylabel('Cumulative Probability')
    ax.set_title('Empirical Cumulative Distribution Function (ECDF)')
    ax.grid(True, alpha=0.3)
    ax.set_ylim([0, 1])
    filename = f"ecdf_run{run_num}.png"
    filepath = os.path.join(temp_dir, filename)
    fig.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return filename


def generate_qq_chart(qq_data: Dict[str, Any], run_num: int, temp_dir: str) -> Optional[str]:
    """Generate Q-Q plot."""
    theoretical = qq_data.get("theoretical", [])
    sample = qq_data.get("sample", [])
    if not theoretical or not sample:
        return None
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.scatter(theoretical, sample, alpha=0.5, s=20, color='steelblue', edgecolors='black', linewidth=0.5)
    min_val = min(min(theoretical), min(sample))
    max_val = max(max(theoretical), max(sample))
    ax.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, label='y=x')
    ax.set_xlabel('Theoretical Quantiles (Uniform)')
    ax.set_ylabel('Sample Quantiles')
    ax.set_title('Q-Q Plot (Uniform Distribution)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    filename = f"qq_run{run_num}.png"
    filepath = os.path.join(temp_dir, filename)
    fig.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return filename


def generate_acf_chart(acf_data: Dict[str, Any], run_num: int, temp_dir: str) -> Optional[str]:
    """Generate ACF chart."""
    lags = acf_data.get("lags", [])
    acf_values = acf_data.get("values", [])
    if not lags or not acf_values:
        return None
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(lags, acf_values, width=0.8, color='steelblue', edgecolor='black', alpha=0.7)
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax.set_xlabel('Lag')
    ax.set_ylabel('Correlation')
    ax.set_title('Autocorrelation Function (ACF)')
    ax.grid(True, alpha=0.3, axis='y')
    filename = f"acf_run{run_num}.png"
    filepath = os.path.join(temp_dir, filename)
    fig.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return filename


def generate_lag1_scatter_chart(lag1_data: Dict[str, Any], run_num: int, temp_dir: str) -> Optional[str]:
    """Generate Lag-1 scatter plot."""
    lag1_x = lag1_data.get("x", [])
    lag1_y = lag1_data.get("y", [])
    if not lag1_x or not lag1_y:
        return None
    step = max(1, len(lag1_x) // 2000) if len(lag1_x) > 2000 else 1
    fig, ax = plt.subplots(figsize=(10, 10))
    ax.scatter(lag1_x[::step], lag1_y[::step], alpha=0.3, s=10, color='steelblue', edgecolors='none')
    ax.set_xlabel('X_n')
    ax.set_ylabel('X_{n+1}')
    ax.set_title('Lag-1 Scatter Plot')
    ax.grid(True, alpha=0.3)
    filename = f"lag1_run{run_num}.png"
    filepath = os.path.join(temp_dir, filename)
    fig.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return filename


def generate_time_series_chart(ts_data: Dict[str, Any], run_num: int, temp_dir: str) -> Optional[str]:
    """Generate time series plot."""
    indices = ts_data.get("index", [])
    values = ts_data.get("values", [])
    if not indices or not values:
        return None
    step = max(1, len(indices) // 2000) if len(indices) > 2000 else 1
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(indices[::step], values[::step], linewidth=0.5, color='steelblue', alpha=0.7)
    ax.set_xlabel('Index')
    ax.set_ylabel('Value')
    ax.set_title('Time Series Plot')
    ax.grid(True, alpha=0.3)
    filename = f"timeseries_run{run_num}.png"
    filepath = os.path.join(temp_dir, filename)
    fig.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return filename


def generate_rolling_stats_chart(stat_data: Dict[str, Any], run_num: int, temp_dir: str) -> Optional[str]:
    """Generate rolling statistics charts."""
    rolling_idx = stat_data["rolling_mean"].get("index", [])
    rolling_mean = stat_data["rolling_mean"].get("values", [])
    rolling_std = stat_data["rolling_std"].get("values", [])
    if not rolling_idx or not rolling_mean or not rolling_std:
        return None
    step = max(1, len(rolling_idx) // 2000) if len(rolling_idx) > 2000 else 1
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    ax1.plot(rolling_idx[::step], rolling_mean[::step], linewidth=1, color='steelblue', label='Rolling Mean')
    ax1.set_ylabel('Mean')
    ax1.set_title('Rolling Statistics')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax2.plot(rolling_idx[::step], rolling_std[::step], linewidth=1, color='darkred', label='Rolling Std')
    ax2.set_xlabel('Index')
    ax2.set_ylabel('Std Dev')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    plt.tight_layout()
    filename = f"rolling_run{run_num}.png"
    filepath = os.path.join(temp_dir, filename)
    fig.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return filename


def generate_fft_chart(spec_data: Dict[str, Any], run_num: int, temp_dir: str) -> Optional[str]:
    """Generate FFT magnitude spectrum chart."""
    freqs = spec_data.get("frequencies", [])
    magnitudes = spec_data.get("magnitude", [])
    if not freqs or not magnitudes:
        return None
    step = max(1, len(freqs) // 2000) if len(freqs) > 2000 else 1
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(freqs[::step], magnitudes[::step], linewidth=1, color='steelblue')
    ax.set_xlabel('Frequency')
    ax.set_ylabel('Magnitude')
    ax.set_title('FFT Magnitude Spectrum')
    ax.grid(True, alpha=0.3)
    filename = f"fft_run{run_num}.png"
    filepath = os.path.join(temp_dir, filename)
    fig.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return filename


def generate_power_spectrum_chart(spec_data: Dict[str, Any], run_num: int, temp_dir: str) -> Optional[str]:
    """Generate power spectrum chart."""
    freqs = spec_data.get("frequencies", [])
    powers = spec_data.get("power", [])
    if not freqs or not powers:
        return None
    step = max(1, len(freqs) // 2000) if len(freqs) > 2000 else 1
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(freqs[::step], powers[::step], linewidth=1, color='darkred')
    ax.set_xlabel('Frequency')
    ax.set_ylabel('Power')
    ax.set_title('Power Spectrum')
    ax.grid(True, alpha=0.3)
    filename = f"power_run{run_num}.png"
    filepath = os.path.join(temp_dir, filename)
    fig.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return filename
