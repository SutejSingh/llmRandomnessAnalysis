"""LaTeX table generation for the PDF report."""
from typing import Any, Dict, List

from .common import escape_latex


def _latex_float(value: Any, precision: int = 6) -> str:
    """Format a numeric cell for LaTeX; N/A for None/NaN (e.g. JSON after convert_numpy_types)."""
    if value is None:
        return "N/A"
    try:
        f = float(value)
    except (TypeError, ValueError):
        return str(value)
    if f != f:  # NaN
        return "N/A"
    return f"{f:.{precision}f}"


def _latex_cv_percent(value: Any) -> str:
    """Format CV as a percentage for LaTeX; N/A if missing/invalid."""
    if value is None:
        return "N/A"
    try:
        f = float(value)
    except (TypeError, ValueError):
        return "N/A"
    if f != f:
        return "N/A"
    return f"{f * 100:.2f}\\%"


def generate_aggregate_stats_table(analysis: Dict[str, Any]) -> str:
    """Generate LaTeX table for aggregate statistics."""
    agg_stats = analysis.get("aggregate_stats", {})
    latex = r"\begin{table}[H]" + "\n"
    latex += r"\centering" + "\n"
    latex += r"\begin{tabular}{lccc}" + "\n"
    latex += r"\toprule" + "\n"
    latex += r"Metric & Mean of Mean & Std Dev of Mean & Range \\" + "\n"
    latex += r"\midrule" + "\n"
    for metric in ["mean", "mode", "std_dev", "skewness", "kurtosis"]:
        if metric in agg_stats:
            metric_name = metric.replace("_", " ").title()
            mean_val = agg_stats[metric].get("mean", 0)
            std_dev_val = agg_stats[metric].get("std_dev", 0)
            range_val = agg_stats[metric].get("range", 0)
            latex += (
                f"{metric_name} & {_latex_float(mean_val)} & {_latex_float(std_dev_val)} & "
                f"{_latex_float(range_val)} \\\\\n"
            )
    latex += r"\bottomrule" + "\n"
    latex += r"\end{tabular}" + "\n"
    latex += r"\caption{Aggregate Statistics Across Runs}" + "\n"
    latex += r"\end{table}" + "\n\n"
    return latex


def generate_per_run_stats_table(analysis: Dict[str, Any]) -> str:
    """Generate LaTeX table for per-run statistics summary."""
    individual_analyses = analysis.get("individual_analyses", [])
    latex = r"\begin{table}[H]" + "\n"
    latex += r"\centering" + "\n"
    latex += r"\begin{tabular}{lrrrrrrc}" + "\n"
    latex += r"\toprule" + "\n"
    latex += r"Run & Mean & Mode & Std Dev & Min & Max & Range & KS Test \\" + "\n"
    latex += r"\midrule" + "\n"
    for idx, run_analysis in enumerate(individual_analyses):
        basic_stats = run_analysis.get("basic_stats", {})
        dist = run_analysis.get("distribution", {})
        is_uniform = dist.get("is_uniform", {})
        mean_val = basic_stats.get("mean", 0)
        mode_val = basic_stats.get("mode", 0)
        if (
            mode_val is None
            or mode_val == "N/A"
            or (isinstance(mode_val, float) and (mode_val != mode_val))
        ):
            mode_str = "N/A"
        else:
            mode_str = _latex_float(mode_val, 4)
        std_dev = basic_stats.get("std", 0)
        min_val = basic_stats.get("min", 0)
        max_val = basic_stats.get("max", 0)
        range_val = max_val - min_val
        ks_p = is_uniform.get("ks_p", 0)
        if isinstance(ks_p, (int, float)) and ks_p == ks_p:
            ks_pass = "Yes" if ks_p > 0.05 else "No"
        else:
            ks_pass = "N/A"
        latex += (
            f"{idx + 1} & {_latex_float(mean_val, 4)} & {mode_str} & {_latex_float(std_dev, 4)} & "
            f"{_latex_float(min_val, 4)} & {_latex_float(max_val, 4)} & {_latex_float(range_val, 4)} & {ks_pass} \\\\\n"
        )
    latex += r"\bottomrule" + "\n"
    latex += r"\end{tabular}" + "\n"
    latex += r"\caption{Per-Run Statistics Summary}" + "\n"
    latex += r"\end{table}" + "\n\n"
    return latex


def generate_autocorr_table(analysis: Dict[str, Any]) -> str:
    """Generate LaTeX table for autocorrelation analysis by run."""
    autocorr_table = analysis.get("autocorrelation_table", [])
    latex = r"\begin{table}[H]" + "\n"
    latex += r"\centering" + "\n"
    latex += r"\begin{tabular}{lcc}" + "\n"
    latex += r"\toprule" + "\n"
    latex += r"Run & Significant Lags & Max Correlation \\" + "\n"
    latex += r"\midrule" + "\n"
    for entry in autocorr_table:
        run = entry.get("run", 0)
        sig_lags = entry.get("significant_lags", [])
        max_corr = entry.get("max_correlation", 0)
        if sig_lags and sig_lags[0] != "None":
            lags_str = ", ".join(map(str, sig_lags[:5]))
            if len(sig_lags) > 5:
                lags_str += "..."
        else:
            lags_str = "None"
        latex += f"{run} & {lags_str} & {_latex_float(max_corr)} \\\\\n"
    latex += r"\bottomrule" + "\n"
    latex += r"\end{tabular}" + "\n"
    latex += r"\caption{Autocorrelation Analysis by Run}" + "\n"
    latex += r"\end{table}" + "\n\n"
    return latex


def generate_distribution_deviation_tables(analysis: Dict[str, Any]) -> str:
    """Generate LaTeX tables for ECDF and Q-Q distribution deviation metrics."""
    dd = analysis.get("distribution_deviation", {})
    if not dd:
        return ""
    latex = ""
    ecdf = dd.get("ecdf", {})
    if ecdf:
        ks = ecdf.get("ks_statistic", {})
        mad = ecdf.get("mad", {})
        if ks or mad:
            latex += r"\begin{table}[H]" + "\n"
            latex += r"\centering" + "\n"
            latex += r"\begin{tabular}{lccc}" + "\n"
            latex += r"\toprule" + "\n"
            latex += r"Metric & Mean & Std Dev & CV \\" + "\n"
            latex += r"\midrule" + "\n"
            if ks:
                m, s, cv = ks.get("mean", 0), ks.get("std_dev", 0), ks.get("cv", 0)
                cv_pct = _latex_cv_percent(cv)
                latex += (
                    f"Max vertical deviation (K-S statistic) & {_latex_float(m)} & {_latex_float(s)} & {cv_pct} \\\\\n"
                )
            if mad:
                m, s, cv = mad.get("mean", 0), mad.get("std_dev", 0), mad.get("cv", 0)
                cv_pct = _latex_cv_percent(cv)
                latex += (
                    f"Mean absolute deviation (MAD) & {_latex_float(m)} & {_latex_float(s)} & {cv_pct} \\\\\n"
                )
            latex += r"\bottomrule" + "\n"
            latex += r"\end{tabular}" + "\n"
            latex += r"\caption{ECDF Deviation (Uniformity)}" + "\n"
            latex += r"\end{table}" + "\n\n"
        regional = ecdf.get("regional_deviation", {})
        labels = regional.get("labels", [])
        means = regional.get("mean", [])
        if labels and means:
            latex += r"\begin{table}[H]" + "\n"
            latex += r"\centering" + "\n"
            latex += r"\begin{tabular}{lc}" + "\n"
            latex += r"\toprule" + "\n"
            latex += r"Region & Mean deviation \\" + "\n"
            latex += r"\midrule" + "\n"
            for i, label in enumerate(labels):
                val = means[i] if i < len(means) else 0
                latex += f"{label} & {_latex_float(val)} \\\\\n"
            latex += r"\bottomrule" + "\n"
            latex += r"\end{tabular}" + "\n"
            latex += r"\caption{Regional ECDF Deviation}" + "\n"
            latex += r"\end{table}" + "\n\n"
    qq = dd.get("qq", {})
    if qq:
        r2 = qq.get("r_squared", {})
        mse = qq.get("mse_from_diagonal", {})
        if r2 or mse:
            latex += r"\begin{table}[H]" + "\n"
            latex += r"\centering" + "\n"
            latex += r"\begin{tabular}{lcc}" + "\n"
            latex += r"\toprule" + "\n"
            latex += r"Metric & Mean & Std Dev \\" + "\n"
            latex += r"\midrule" + "\n"
            if r2:
                m, s = r2.get("mean", 0), r2.get("std_dev", 0)
                latex += (
                    f"R$^2$ (coefficient of determination) & {_latex_float(m)} & {_latex_float(s)} \\\\\n"
                )
            if mse:
                m, s = mse.get("mean", 0), mse.get("std_dev", 0)
                latex += f"MSE from diagonal & {_latex_float(m)} & {_latex_float(s)} \\\\\n"
            latex += r"\bottomrule" + "\n"
            latex += r"\end{tabular}" + "\n"
            latex += r"\caption{Q-Q Plot Deviation (vs diagonal $y=x$)}" + "\n"
            latex += r"\end{table}" + "\n\n"
    return latex


def generate_descriptive_stats_table(basic_stats: Dict[str, Any], caption: str = "Descriptive Statistics") -> str:
    """Generate LaTeX table for descriptive statistics."""
    latex = r"\begin{table}[H]" + "\n"
    latex += r"\centering" + "\n"
    latex += r"\begin{tabular}{lr}" + "\n"
    latex += r"\toprule" + "\n"
    latex += r"Metric & Value \\" + "\n"
    latex += r"\midrule" + "\n"
    stats_list = [
        ("Mean", basic_stats.get("mean", 0)),
        ("Mode", basic_stats.get("mode", "N/A")),
        ("Median", basic_stats.get("median", 0)),
        ("Standard Deviation", basic_stats.get("std", 0)),
        ("Variance", basic_stats.get("variance", 0)),
        ("Min", basic_stats.get("min", 0)),
        ("Max", basic_stats.get("max", 0)),
        ("Range", basic_stats.get("max", 0) - basic_stats.get("min", 0)),
        ("Q25", basic_stats.get("q25", 0)),
        ("Q75", basic_stats.get("q75", 0)),
        ("Q95", basic_stats.get("q95", 0)),
        ("Skewness", basic_stats.get("skewness", 0)),
        ("Kurtosis", basic_stats.get("kurtosis", 0)),
    ]
    for metric, value in stats_list:
        if isinstance(value, (int, float)) and value == value:
            latex += f"{metric} & {value:.6f} \\\\\n"
        else:
            latex += f"{metric} & {value} \\\\\n"
    latex += r"\bottomrule" + "\n"
    latex += r"\end{tabular}" + "\n"
    latex += f"\\caption{{{caption}}}" + "\n"
    latex += r"\end{table}" + "\n\n"
    return latex


def generate_nist_test_table_content(nist_test: Dict[str, Any], test_name: str) -> str:
    """Generate LaTeX table content for NIST test results (for use in minipage)."""
    if "error" in nist_test and nist_test["error"]:
        return f"\\textbf{{{escape_latex(test_name)}:}}\\\\[0.5em]\nError: {escape_latex(str(nist_test['error']))}"
    latex = r"\begin{tabular}{lr}" + "\n"
    latex += r"\toprule" + "\n"
    latex += r"Metric & Value \\" + "\n"
    latex += r"\midrule" + "\n"
    p_value = nist_test.get('p_value', 0)
    if isinstance(p_value, (int, float)):
        latex += f"P-value & {p_value:.6f} \\\\\n"
    else:
        latex += f"P-value & {p_value} \\\\\n"
    if "statistic" in nist_test:
        stat = nist_test.get('statistic', 0)
        if isinstance(stat, (int, float)):
            latex += f"Statistic & {stat:.6f} \\\\\n"
        else:
            latex += f"Statistic & {stat} \\\\\n"
    if "passed" in nist_test:
        result = "Passed" if nist_test.get("passed", False) else "Failed"
        latex += f"Result & {result} \\\\\n"
    latex += r"\bottomrule" + "\n"
    latex += r"\end{tabular}" + "\n"
    latex += f"\\captionof{{table}}{{{escape_latex(test_name)}}}" + "\n"
    return latex


def generate_nist_tables_grid(nist_tables: List[tuple]) -> str:
    """Generate NIST test tables in a 2x2 grid layout."""
    if not nist_tables:
        return ""
    latex = ""
    for i in range(0, len(nist_tables), 2):
        latex += r"\begin{table}[H]" + "\n"
        latex += r"\centering" + "\n"
        test_name1, nist_test1 = nist_tables[i]
        latex += r"\begin{minipage}{0.48\textwidth}" + "\n"
        latex += r"\centering" + "\n"
        latex += generate_nist_test_table_content(nist_test1, test_name1)
        latex += r"\end{minipage}" + "\n"
        latex += r"\hfill" + "\n"
        if i + 1 < len(nist_tables):
            test_name2, nist_test2 = nist_tables[i + 1]
            latex += r"\begin{minipage}{0.48\textwidth}" + "\n"
            latex += r"\centering" + "\n"
            latex += generate_nist_test_table_content(nist_test2, test_name2)
            latex += r"\end{minipage}" + "\n"
        latex += r"\end{table}" + "\n\n"
    return latex
