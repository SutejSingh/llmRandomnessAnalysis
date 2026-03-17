"""
LaTeX PDF Generator for LLM Randomness Evaluation Report.
Orchestrates table and chart generation and compiles LaTeX to PDF.
"""
import subprocess
import tempfile
import shutil
import os
import glob
import threading
import logging
from typing import Dict, Any, List, Optional

from . import common
from . import latex_tables
from . import latex_charts

logger = logging.getLogger(__name__)


class LatexGenerator:
    """Class for generating LaTeX PDF reports from statistical analysis data."""

    def __init__(self):
        self._pdf_bytes: Optional[bytes] = None
        self._status: str = "pending"
        self._error: Optional[str] = None
        self._temp_dir: Optional[str] = None
        self._lock = threading.Lock()

    @staticmethod
    def escape_latex(text: str) -> str:
        """Escape special LaTeX characters."""
        return common.escape_latex(text)

    def get_status(self) -> str:
        with self._lock:
            return self._status

    def is_ready(self) -> bool:
        with self._lock:
            return self._status == "ready" and self._pdf_bytes is not None

    def get_error(self) -> Optional[str]:
        with self._lock:
            return self._error

    def get_pdf_bytes(self) -> Optional[bytes]:
        with self._lock:
            if self._status == "ready" and self._pdf_bytes is not None:
                return self._pdf_bytes
            return None

    def prepare_pdf(self, analysis: Dict[str, Any], runs_data: Optional[List[List[float]]] = None, async_prepare: bool = False):
        if async_prepare:
            thread = threading.Thread(
                target=self._prepare_pdf_sync,
                args=(analysis, runs_data),
                daemon=True
            )
            thread.start()
        else:
            self._prepare_pdf_sync(analysis, runs_data)

    def _prepare_pdf_sync(self, analysis: Dict[str, Any], runs_data: Optional[List[List[float]]] = None):
        with self._lock:
            if self._status == "in_progress":
                logger.warning("PDF generation already in progress, skipping")
                return
            self._status = "in_progress"
            self._error = None
            self._pdf_bytes = None
        temp_dir = None
        try:
            temp_dir = tempfile.mkdtemp()
            self._temp_dir = temp_dir
            pdf_bytes = self._generate_latex_pdf(analysis, runs_data or None, temp_dir)
            with self._lock:
                self._pdf_bytes = pdf_bytes
                self._status = "ready"
                self._error = None
                logger.info("PDF generation completed successfully")
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error generating PDF: {error_msg}", exc_info=True)
            with self._lock:
                self._status = "error"
                self._error = error_msg
                self._pdf_bytes = None
        finally:
            pass

    def _generate_latex_pdf(self, analysis: Dict[str, Any], runs_data: Optional[List[List[float]]] = None, temp_dir: str = "") -> bytes:
        latex_content = self._generate_latex_content(analysis, runs_data, temp_dir)
        tex_file = os.path.join(temp_dir, "report.tex")
        with open(tex_file, 'w', encoding='utf-8') as f:
            f.write(latex_content)
        pdflatex_cmd = self._find_pdflatex()
        if not pdflatex_cmd:
            raise RuntimeError(
                "pdflatex not found. Please install LaTeX:\n"
                "  macOS: brew install --cask mactex (or brew install basictex)\n"
                "  Linux: sudo apt-get install texlive-latex-base\n"
                "  Windows: Install MiKTeX or TeX Live"
            )
        result = subprocess.run(
            [pdflatex_cmd, '-interaction=nonstopmode', '-output-directory', temp_dir, tex_file],
            capture_output=True,
            text=True,
            cwd=temp_dir
        )
        if result.returncode != 0:
            raise RuntimeError(f"LaTeX compilation failed: {result.stderr}")
        pdf_file = os.path.join(temp_dir, "report.pdf")
        with open(pdf_file, 'rb') as f:
            pdf_bytes = f.read()
        return pdf_bytes

    def _find_pdflatex(self) -> Optional[str]:
        pdflatex_paths = ['pdflatex', '/Library/TeX/texbin/pdflatex', '/usr/local/texlive/*/bin/*/pdflatex']
        pdflatex_cmd = None
        for path in pdflatex_paths:
            if path == 'pdflatex':
                result_check = subprocess.run(['which', 'pdflatex'], capture_output=True)
                if result_check.returncode == 0:
                    pdflatex_cmd = 'pdflatex'
                    break
            elif os.path.exists(path):
                pdflatex_cmd = path
                break
        if not pdflatex_cmd:
            for pattern in ['/usr/local/texlive/*/bin/*/pdflatex', '/usr/texbin/pdflatex']:
                matches = glob.glob(pattern)
                if matches:
                    pdflatex_cmd = matches[0]
                    break
        return pdflatex_cmd

    def _normalize_analysis_to_multi_run(self, analysis: Dict[str, Any], runs_data: Optional[List[List[float]]] = None) -> Dict[str, Any]:
        if not analysis:
            return analysis
        individual = analysis.get("individual_analyses", [])
        if isinstance(individual, list) and len(individual) > 0 and analysis.get("aggregate_stats") is not None:
            return analysis
        basic = analysis.get("basic_stats", {})
        if not basic:
            return analysis
        dist = analysis.get("distribution", {})
        is_uniform = dist.get("is_uniform", {})
        nist = analysis.get("nist_tests", {})
        range_behavior = analysis.get("range_behavior", {})
        independence = analysis.get("independence", {})
        ks_p = is_uniform.get("ks_p", 0)
        ks_pass = "1/1" if (isinstance(ks_p, (int, float)) and ks_p > 0.05) else "0/1"
        def nist_pass(key):
            t = nist.get(key, {})
            return "1/1" if t.get("passed", False) else "0/1"
        test_results = {
            "ks_uniformity_passed": ks_pass,
            "runs_test_passed": nist_pass("runs_test"),
            "binary_matrix_rank_test_passed": nist_pass("binary_matrix_rank_test"),
            "longest_run_of_ones_test_passed": nist_pass("longest_run_of_ones_test"),
            "approximate_entropy_test_passed": nist_pass("approximate_entropy_test"),
        }
        mean_val = basic.get("mean", 0)
        mode_val = basic.get("mode", 0)
        if mode_val == "N/A" or (isinstance(mode_val, float) and (mode_val != mode_val)):
            mode_val = 0
        std_val = basic.get("std", 0)
        skew_val = basic.get("skewness", 0)
        kurt_val = basic.get("kurtosis", 0)
        aggregate_stats = {
            "mean": {"mean": mean_val, "std_dev": 0.0, "range": 0.0},
            "mode": {"mean": mode_val, "std_dev": 0.0, "range": 0.0},
            "std_dev": {"mean": std_val, "std_dev": 0.0, "range": 0.0},
            "skewness": {"mean": skew_val, "std_dev": 0.0, "range": 0.0},
            "kurtosis": {"mean": kurt_val, "std_dev": 0.0, "range": 0.0},
        }
        autocorr = independence.get("autocorrelation", {})
        lags = autocorr.get("lags", [])
        values = autocorr.get("values", [])
        significant_lags = []
        max_corr = 0.0
        if lags and values:
            for lag, corr in zip(lags, values):
                if abs(corr) > 0.2:
                    significant_lags.append(lag)
                if abs(corr) > max_corr:
                    max_corr = abs(corr)
        autocorrelation_table = [{
            "run": 1,
            "significant_lags": significant_lags if significant_lags else ["None"],
            "max_correlation": float(max_corr)
        }]
        ecdf = range_behavior.get("ecdf", {})
        ecdf_x = ecdf.get("x", [])
        ecdf_y = ecdf.get("y", [])
        ecdf_all_runs = [{"run": 1, "x": ecdf_x, "y": ecdf_y}] if (ecdf_x and ecdf_y) else []
        hist = dist.get("histogram", {})
        counts = hist.get("counts", [])
        edges = hist.get("edges", [])
        if counts and edges and len(edges) == len(counts) + 1:
            bin_centers = [(edges[i] + edges[i + 1]) / 2 for i in range(len(edges) - 1)]
            frequency_histogram = {"bins": bin_centers, "frequencies": list(counts), "bin_edges": list(edges)}
        else:
            frequency_histogram = {"bins": [], "frequencies": [], "bin_edges": []}
        normalized = dict(analysis)
        normalized["num_runs"] = 1
        count_per_run = analysis.get("count_per_run") or analysis.get("count")
        if count_per_run is None and runs_data and runs_data[0]:
            count_per_run = len(runs_data[0])
        normalized["count_per_run"] = count_per_run or 0
        normalized["test_results"] = test_results
        normalized["aggregate_stats"] = aggregate_stats
        normalized["combined_stream_stats"] = dict(basic)
        normalized["individual_analyses"] = [analysis]
        normalized["autocorrelation_table"] = autocorrelation_table
        normalized["ecdf_all_runs"] = ecdf_all_runs
        normalized["frequency_histogram"] = frequency_histogram
        return normalized

    def _generate_latex_content(self, analysis: Dict[str, Any], runs_data: Optional[List[List[float]]] = None, temp_dir: str = "") -> str:
        analysis = self._normalize_analysis_to_multi_run(analysis, runs_data)
        latex = r"""\documentclass[11pt,a4paper]{article}
        \usepackage[utf8]{inputenc}
        \usepackage[T1]{fontenc}
        \usepackage{geometry}
        \usepackage{graphicx}
        \usepackage{booktabs}
        \usepackage{longtable}
        \usepackage{array}
        \usepackage{multirow}
        \usepackage{xcolor}
        \usepackage{amsmath}
        \usepackage{float}
        \usepackage{caption}
        \geometry{margin=1in}

        \title{LLM Randomness Evaluation report}
        \author{}
        \date{\today}

        \begin{document}

        \maketitle

    """
        latex += r"\section{Multi-Run Analysis}" + "\n\n"
        latex += r"\subsection{Test Results}" + "\n\n"
        test_results = analysis.get("test_results", {})
        num_runs = analysis.get("num_runs", 3)
        test_mapping = {
            "ks_uniformity_passed": ("Kolmogorov-Smirnov Uniformity Test", 0.05),
            "runs_test_passed": ("NIST Runs Test", 0.01),
            "binary_matrix_rank_test_passed": ("NIST Binary Matrix Rank Test", 0.01),
            "longest_run_of_ones_test_passed": ("NIST Longest Run of Ones Test", 0.01),
            "approximate_entropy_test_passed": ("NIST Approximate Entropy Test", 0.01),
        }
        for test_key, (display_name, p_threshold) in test_mapping.items():
            passed_value = test_results.get(test_key, f"0/{num_runs}")
            latex += f"\\textbf{{{display_name}}}\\\\[0.5em]\n"
            latex += f"{passed_value} runs passed (p > {p_threshold:.2f})\\\\[1em]\n\n"
        combined = analysis.get("combined_stream_stats", {})
        if combined:
            latex += r"\subsection{Statistics Across All Runs (Combined Stream)}" + "\n\n"
            latex += "These statistics are calculated from all numbers across all runs treated as a single stream of data.\\\\[0.5em]\n\n"
            latex += latex_tables.generate_descriptive_stats_table(combined, caption="Statistics on the combined stream (all runs concatenated)")
        latex += r"\subsection{Aggregate Statistics Across Runs}" + "\n\n"
        latex += latex_tables.generate_aggregate_stats_table(analysis)
        latex += r"\subsection{Per-Run Statistics Summary}" + "\n\n"
        latex += latex_tables.generate_per_run_stats_table(analysis)
        latex += r"\subsection{Autocorrelation Analysis by Run}" + "\n\n"
        latex += latex_tables.generate_autocorr_table(analysis)
        if analysis.get("distribution_deviation"):
            latex += r"\subsection{Distribution Deviation Metrics}" + "\n\n"
            latex += latex_tables.generate_distribution_deviation_tables(analysis)
        latex += r"\subsection{Multi-Run Summary Charts}" + "\n\n"
        if "frequency_histogram" in analysis:
            hist_path = latex_charts.generate_frequency_histogram_chart(analysis, temp_dir)
            if hist_path:
                latex += r"\begin{figure}[H]" + "\n\centering" + "\n"
                latex += f"\\includegraphics[width=0.8\\textwidth]{{{hist_path}}}" + "\n"
                latex += r"\caption{Frequency Histogram Across All Runs}" + "\n\end{figure}" + "\n\n"
        if "ecdf_all_runs" in analysis:
            ecdf_path = latex_charts.generate_overlaid_ecdf_chart(analysis, temp_dir)
            if ecdf_path:
                latex += r"\begin{figure}[H]" + "\n\centering" + "\n"
                latex += f"\\includegraphics[width=0.8\\textwidth]{{{ecdf_path}}}" + "\n"
                latex += r"\caption{Overlaid ECDF Plot with Reference Line for Uniform Distribution}" + "\n\end{figure}" + "\n\n"
        if "individual_analyses" in analysis:
            qq_path = latex_charts.generate_overlaid_qq_chart(analysis, temp_dir)
            if qq_path:
                latex += r"\begin{figure}[H]" + "\n\centering" + "\n"
                latex += f"\\includegraphics[width=0.8\\textwidth]{{{qq_path}}}" + "\n"
                latex += r"\caption{Overlaid Q-Q Plot with Reference Line for Uniform Distribution}" + "\n\end{figure}" + "\n\n"
        if "individual_analyses" in analysis:
            for run_idx, run_analysis in enumerate(analysis["individual_analyses"]):
                latex += f"\\newpage\n\\section{{Per-Run Analysis: Run {run_idx + 1}}}\n\n"
                latex += self._generate_per_run_analysis(run_analysis, run_idx + 1, temp_dir)
        latex += r"\end{document}"
        return latex

    def _generate_per_run_analysis(self, run_analysis: Dict[str, Any], run_num: int, temp_dir: str) -> str:
        latex = ""
        latex += r"\subsection{Category 1: Descriptive Statistics}" + "\n\n"
        basic_stats = run_analysis.get("basic_stats", {})
        latex += latex_tables.generate_descriptive_stats_table(basic_stats)
        latex += r"\subsection{Category 2: Distributional Tests}" + "\n\n"
        dist = run_analysis.get("distribution", {})
        if "kde" in dist:
            kde_path = latex_charts.generate_kde_chart(dist["kde"], run_num, temp_dir)
            if kde_path:
                latex += r"\begin{figure}[H]" + "\n\centering" + "\n"
                latex += f"\\includegraphics[width=0.8\\textwidth]{{{kde_path}}}" + "\n"
                latex += r"\caption{Kernel Density Estimate (KDE)}" + "\n\end{figure}" + "\n\n"
        if "range_behavior" in run_analysis and "ecdf" in run_analysis["range_behavior"]:
            ecdf_path = latex_charts.generate_ecdf_chart(run_analysis["range_behavior"]["ecdf"], run_num, temp_dir)
            if ecdf_path:
                latex += r"\begin{figure}[H]" + "\n\centering" + "\n"
                latex += f"\\includegraphics[width=0.8\\textwidth]{{{ecdf_path}}}" + "\n"
                latex += r"\caption{Empirical Cumulative Distribution Function (ECDF)}" + "\n\end{figure}" + "\n\n"
        if "qq_plot" in dist:
            qq_path = latex_charts.generate_qq_chart(dist["qq_plot"], run_num, temp_dir)
            if qq_path:
                latex += r"\begin{figure}[H]" + "\n\centering" + "\n"
                latex += f"\\includegraphics[width=0.8\\textwidth]{{{qq_path}}}" + "\n"
                latex += r"\caption{Q-Q Plot (Uniform Distribution)}" + "\n\end{figure}" + "\n\n"
        if "is_uniform" in dist:
            is_uniform = dist["is_uniform"]
            ks_p = is_uniform.get("ks_p", "N/A")
            ks_stat = is_uniform.get("ks_stat", "N/A")
            latex += f"\\textbf{{Kolmogorov-Smirnov Test:}}\\\\[0.5em]\n"
            latex += f"P-value: {ks_p:.6f}\\\\[0.5em]\n" if isinstance(ks_p, (int, float)) else f"P-value: {ks_p}\\\\[0.5em]\n"
            latex += f"Statistic: {ks_stat:.6f}\\\\[1em]\n\n" if isinstance(ks_stat, (int, float)) else f"Statistic: {ks_stat}\\\\[1em]\n\n"
        latex += r"\subsection{Category 3: Independence Tests}" + "\n\n"
        ind = run_analysis.get("independence", {})
        if "autocorrelation" in ind:
            acf_path = latex_charts.generate_acf_chart(ind["autocorrelation"], run_num, temp_dir)
            if acf_path:
                latex += r"\begin{figure}[H]" + "\n\centering" + "\n"
                latex += f"\\includegraphics[width=0.8\\textwidth]{{{acf_path}}}" + "\n"
                latex += r"\caption{Autocorrelation Function (ACF)}" + "\n\end{figure}" + "\n\n"
        if "lag1_scatter" in ind:
            lag1_path = latex_charts.generate_lag1_scatter_chart(ind["lag1_scatter"], run_num, temp_dir)
            if lag1_path:
                latex += r"\begin{figure}[H]" + "\n\centering" + "\n"
                latex += f"\\includegraphics[width=0.8\\textwidth]{{{lag1_path}}}" + "\n"
                latex += r"\caption{Lag-1 Scatter Plot}" + "\n\end{figure}" + "\n\n"
        latex += r"\subsection{Category 4: Temporal Analysis}" + "\n\n"
        if "time_series" in ind:
            ts_path = latex_charts.generate_time_series_chart(ind["time_series"], run_num, temp_dir)
            if ts_path:
                latex += r"\begin{figure}[H]" + "\n\centering" + "\n"
                latex += f"\\includegraphics[width=0.8\\textwidth]{{{ts_path}}}" + "\n"
                latex += r"\caption{Time Series Plot}" + "\n\end{figure}" + "\n\n"
        stat = run_analysis.get("stationarity", {})
        if "rolling_mean" in stat and "rolling_std" in stat:
            rolling_path = latex_charts.generate_rolling_stats_chart(stat, run_num, temp_dir)
            if rolling_path:
                latex += r"\begin{figure}[H]" + "\n\centering" + "\n"
                latex += f"\\includegraphics[width=0.8\\textwidth]{{{rolling_path}}}" + "\n"
                latex += r"\caption{Rolling Mean and Standard Deviation}" + "\n\end{figure}" + "\n\n"
        latex += r"\subsection{Category 5: Spectral Analysis}" + "\n\n"
        spec = run_analysis.get("spectral", {})
        if "frequencies" in spec and "magnitude" in spec:
            fft_path = latex_charts.generate_fft_chart(spec, run_num, temp_dir)
            if fft_path:
                latex += r"\begin{figure}[H]" + "\n\centering" + "\n"
                latex += f"\\includegraphics[width=0.8\\textwidth]{{{fft_path}}}" + "\n"
                latex += r"\caption{FFT Magnitude Spectrum}" + "\n\end{figure}" + "\n\n"
        if "frequencies" in spec and "power" in spec:
            power_path = latex_charts.generate_power_spectrum_chart(spec, run_num, temp_dir)
            if power_path:
                latex += r"\begin{figure}[H]" + "\n\centering" + "\n"
                latex += f"\\includegraphics[width=0.8\\textwidth]{{{power_path}}}" + "\n"
                latex += r"\caption{Power Spectrum}" + "\n\end{figure}" + "\n\n"
        latex += r"\subsection{Category 6: NIST Binary Tests}" + "\n\n"
        nist = run_analysis.get("nist_tests", {})
        nist_tables = []
        if "runs_test" in nist:
            nist_tables.append(("Runs Test", nist["runs_test"]))
        if "binary_matrix_rank_test" in nist:
            nist_tables.append(("Binary Matrix Rank Test", nist["binary_matrix_rank_test"]))
        if "approximate_entropy_test" in nist:
            nist_tables.append(("Approximate Entropy Test", nist["approximate_entropy_test"]))
        if "longest_run_of_ones_test" in nist:
            nist_tables.append(("Longest Run of Ones Test", nist["longest_run_of_ones_test"]))
        if nist_tables:
            latex += latex_tables.generate_nist_tables_grid(nist_tables)
        return latex

    def cleanup(self):
        with self._lock:
            if self._temp_dir and os.path.exists(self._temp_dir):
                try:
                    shutil.rmtree(self._temp_dir)
                    logger.info(f"Cleaned up temporary directory: {self._temp_dir}")
                except Exception as e:
                    logger.warning(f"Error cleaning up temp directory: {e}")
                self._temp_dir = None

    def __del__(self):
        self.cleanup()
