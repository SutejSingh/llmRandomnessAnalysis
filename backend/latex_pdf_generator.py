"""
LaTeX PDF Generator for LLM Randomness Evaluation Report
This module generates LaTeX code and compiles it to PDF
"""
import subprocess
import tempfile
import shutil
import os
import glob
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
from typing import Dict, Any, List, Optional
import threading
import logging

logger = logging.getLogger(__name__)


class LatexGenerator:
    """Class for generating LaTeX PDF reports from statistical analysis data"""
    
    def __init__(self):
        """Initialize the LatexGenerator"""
        self._pdf_bytes: Optional[bytes] = None
        self._status: str = "pending"  # pending, in_progress, ready, error
        self._error: Optional[str] = None
        self._temp_dir: Optional[str] = None
        self._lock = threading.Lock()
    
    @staticmethod
    def escape_latex(text: str) -> str:
        """Escape special LaTeX characters"""
        special_chars = {
            '&': r'\&',
            '%': r'\%',
            '$': r'\$',
            '#': r'\#',
            '^': r'\textasciicircum{}',
            '_': r'\_',
            '{': r'\{',
            '}': r'\}',
            '~': r'\textasciitilde{}',
            '\\': r'\textbackslash{}',
        }
        for char, replacement in special_chars.items():
            text = text.replace(char, replacement)
        return text
    
    def get_status(self) -> str:
        """Get the current PDF generation status"""
        with self._lock:
            return self._status
    
    def is_ready(self) -> bool:
        """Check if PDF is ready"""
        with self._lock:
            return self._status == "ready" and self._pdf_bytes is not None
    
    def get_error(self) -> Optional[str]:
        """Get error message if generation failed"""
        with self._lock:
            return self._error
    
    def get_pdf_bytes(self) -> Optional[bytes]:
        """Get the prepared PDF bytes if ready"""
        with self._lock:
            if self._status == "ready" and self._pdf_bytes is not None:
                return self._pdf_bytes
            return None
    
    def prepare_pdf(self, analysis: Dict[str, Any], runs_data: List[List[float]], async_prepare: bool = False):
        """
        Prepare PDF from analysis data
        
        Args:
            analysis: Analysis data dictionary
            runs_data: List of runs (list of numbers)
            async_prepare: If True, prepare PDF in background thread
        """
        if async_prepare:
            # Start background thread
            thread = threading.Thread(
                target=self._prepare_pdf_sync,
                args=(analysis, runs_data),
                daemon=True
            )
            thread.start()
        else:
            self._prepare_pdf_sync(analysis, runs_data)
    
    def _prepare_pdf_sync(self, analysis: Dict[str, Any], runs_data: List[List[float]]):
        """Synchronously prepare PDF (internal method)"""
        with self._lock:
            if self._status == "in_progress":
                logger.warning("PDF generation already in progress, skipping")
                return
            self._status = "in_progress"
            self._error = None
            self._pdf_bytes = None
        
        temp_dir = None
        try:
            # Create temporary directory for LaTeX compilation
            temp_dir = tempfile.mkdtemp()
            self._temp_dir = temp_dir
            
            # Generate PDF
            pdf_bytes = self._generate_latex_pdf(analysis, runs_data, temp_dir)
            
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
            # Clean up temporary directory after a delay to allow PDF to be read
            # We'll clean it up when the object is destroyed or when a new PDF is generated
            pass
    
    def _generate_latex_pdf(self, analysis: Dict[str, Any], runs_data: List[List[float]], temp_dir: str) -> bytes:
        """
        Generate LaTeX code and compile to PDF
        
        Args:
            analysis: Analysis data dictionary
            runs_data: List of runs (list of numbers)
            temp_dir: Temporary directory for files
            
        Returns:
            PDF bytes
        """
        # Create LaTeX document
        latex_content = self._generate_latex_content(analysis, runs_data, temp_dir)
        
        # Write LaTeX file
        tex_file = os.path.join(temp_dir, "report.tex")
        with open(tex_file, 'w', encoding='utf-8') as f:
            f.write(latex_content)
        
        # Compile LaTeX to PDF
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
        
        # Read PDF
        pdf_file = os.path.join(temp_dir, "report.pdf")
        with open(pdf_file, 'rb') as f:
            pdf_bytes = f.read()
        
        return pdf_bytes
    
    def _find_pdflatex(self) -> Optional[str]:
        """Find pdflatex executable"""
        pdflatex_paths = [
            'pdflatex',  # Try PATH first
            '/Library/TeX/texbin/pdflatex',  # macOS MacTeX
            '/usr/local/texlive/*/bin/*/pdflatex',  # TeX Live
        ]
        
        pdflatex_cmd = None
        for path in pdflatex_paths:
            if path == 'pdflatex':
                # Check if it's in PATH
                result_check = subprocess.run(['which', 'pdflatex'], capture_output=True)
                if result_check.returncode == 0:
                    pdflatex_cmd = 'pdflatex'
                    break
            elif os.path.exists(path):
                pdflatex_cmd = path
                break
        
        # Try glob pattern for TeX Live
        if not pdflatex_cmd:
            for pattern in ['/usr/local/texlive/*/bin/*/pdflatex', '/usr/texbin/pdflatex']:
                matches = glob.glob(pattern)
                if matches:
                    pdflatex_cmd = matches[0]
                    break
        
        return pdflatex_cmd
    
    def _generate_latex_content(self, analysis: Dict[str, Any], runs_data: List[List[float]], temp_dir: str) -> str:
        """Generate LaTeX document content"""
        
        # Start LaTeX document
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
        
        # Multi-Run Analysis Section (First Page)
        latex += r"\section{Multi-Run Analysis}" + "\n\n"
        
        # Test Results Section
        latex += r"\subsection{Test Results}" + "\n\n"
        
        test_results = analysis.get("test_results", {})
        num_runs = analysis.get("num_runs", 3)
        
        # Mapping of test result keys to display names and p-value thresholds
        test_mapping = {
            "ks_uniformity_passed": ("Kolmogorov-Smirnov Uniformity Test", 0.05),
            "runs_test_passed": ("NIST Runs Test", 0.01),
            "binary_matrix_rank_test_passed": ("NIST Binary Matrix Rank Test", 0.01),
            "longest_run_of_ones_test_passed": ("NIST Longest Run of Ones Test", 0.01),
            "approximate_entropy_test_passed": ("NIST Approximate Entropy Test", 0.01),
        }
        
        # Iterate through available tests dynamically
        for test_key, (display_name, p_threshold) in test_mapping.items():
            if test_key in test_results:
                passed_value = test_results.get(test_key, f"0/{num_runs}")
                latex += f"\\textbf{{{display_name}}}\\\\[0.5em]\n"
                latex += f"{passed_value} runs passed (p > {p_threshold:.2f})\\\\[1em]\n\n"
        
        # Aggregate Statistics Table
        latex += r"\subsection{Aggregate Statistics Across Runs}" + "\n\n"
        latex += self._generate_aggregate_stats_table(analysis)
        
        # Per-Run Statistics Summary Table
        latex += r"\subsection{Per-Run Statistics Summary}" + "\n\n"
        latex += self._generate_per_run_stats_table(analysis)
        
        # Autocorrelation Analysis by Run Table
        latex += r"\subsection{Autocorrelation Analysis by Run}" + "\n\n"
        latex += self._generate_autocorr_table(analysis)
        
        # Charts for Multi-run summary
        latex += r"\subsection{Multi-Run Summary Charts}" + "\n\n"
        
        # Frequency Histogram
        if "frequency_histogram" in analysis:
            hist_path = self._generate_frequency_histogram_chart(analysis, temp_dir)
            if hist_path:
                latex += r"\begin{figure}[H]" + "\n"
                latex += r"\centering" + "\n"
                latex += f"\\includegraphics[width=0.8\\textwidth]{{{hist_path}}}" + "\n"
                latex += r"\caption{Frequency Histogram Across All Runs}" + "\n"
                latex += r"\end{figure}" + "\n\n"
        
        # Overlaid ECDF
        if "ecdf_all_runs" in analysis:
            ecdf_path = self._generate_overlaid_ecdf_chart(analysis, temp_dir)
            if ecdf_path:
                latex += r"\begin{figure}[H]" + "\n"
                latex += r"\centering" + "\n"
                latex += f"\\includegraphics[width=0.8\\textwidth]{{{ecdf_path}}}" + "\n"
                latex += r"\caption{Overlaid ECDF Plot with Reference Line for Uniform Distribution}" + "\n"
                latex += r"\end{figure}" + "\n\n"
        
        # Overlaid Q-Q Plot
        if "individual_analyses" in analysis:
            qq_path = self._generate_overlaid_qq_chart(analysis, temp_dir)
            if qq_path:
                latex += r"\begin{figure}[H]" + "\n"
                latex += r"\centering" + "\n"
                latex += f"\\includegraphics[width=0.8\\textwidth]{{{qq_path}}}" + "\n"
                latex += r"\caption{Overlaid Q-Q Plot with Reference Line for Uniform Distribution}" + "\n"
                latex += r"\end{figure}" + "\n\n"
        
        # Per-Run Analysis Sections
        if "individual_analyses" in analysis:
            for run_idx, run_analysis in enumerate(analysis["individual_analyses"]):
                latex += f"\\newpage\n\\section{{Per-Run Analysis: Run {run_idx + 1}}}\n\n"
                latex += self._generate_per_run_analysis(run_analysis, run_idx + 1, temp_dir)
        
        # End document
        latex += r"\end{document}"
        
        return latex
    
    def _generate_aggregate_stats_table(self, analysis: Dict[str, Any]) -> str:
        """Generate LaTeX table for aggregate statistics"""
        agg_stats = analysis.get("aggregate_stats", {})
        
        latex = r"\begin{table}[H]" + "\n"
        latex += r"\centering" + "\n"
        latex += r"\begin{tabular}{lccc}" + "\n"
        latex += r"\toprule" + "\n"
        latex += r"Metric & Mean of Mean & Std Dev of Mean & Range \\" + "\n"
        latex += r"\midrule" + "\n"
        
        for metric in ["mean", "std_dev", "skewness", "kurtosis"]:
            if metric in agg_stats:
                metric_name = metric.replace("_", " ").title()
                mean_val = agg_stats[metric].get("mean", 0)
                std_dev_val = agg_stats[metric].get("std_dev", 0)
                range_val = agg_stats[metric].get("range", 0)
                latex += f"{metric_name} & {mean_val:.6f} & {std_dev_val:.6f} & {range_val:.6f} \\\\\n"
        
        latex += r"\bottomrule" + "\n"
        latex += r"\end{tabular}" + "\n"
        latex += r"\caption{Aggregate Statistics Across Runs}" + "\n"
        latex += r"\end{table}" + "\n\n"
        
        return latex
    
    def _generate_per_run_stats_table(self, analysis: Dict[str, Any]) -> str:
        """Generate LaTeX table for per-run statistics summary"""
        individual_analyses = analysis.get("individual_analyses", [])
        
        # Use makebox to ensure headers are at least as wide as the data
        # Data format is .4f (e.g., "0.5562") which is ~6 chars, so use 1.0cm width
        latex = r"\begin{table}[H]" + "\n"
        latex += r"\centering" + "\n"
        latex += r"\begin{tabular}{lrrrrrc}" + "\n"
        latex += r"\toprule" + "\n"
        latex += r"Run & Mean & Std Dev & Min & Max & Range & KS Test \\" + "\n"
        latex += r"\midrule" + "\n"
        
        for idx, run_analysis in enumerate(individual_analyses):
            basic_stats = run_analysis.get("basic_stats", {})
            dist = run_analysis.get("distribution", {})
            is_uniform = dist.get("is_uniform", {})
            
            mean_val = basic_stats.get("mean", 0)
            std_dev = basic_stats.get("std", 0)
            min_val = basic_stats.get("min", 0)
            max_val = basic_stats.get("max", 0)
            range_val = max_val - min_val
            ks_p = is_uniform.get("ks_p", 0)
            ks_pass = "Yes" if ks_p > 0.05 else "No"
            
            latex += f"{idx + 1} & {mean_val:.4f} & {std_dev:.4f} & {min_val:.4f} & {max_val:.4f} & {range_val:.4f} & {ks_pass} \\\\\n"
        
        latex += r"\bottomrule" + "\n"
        latex += r"\end{tabular}" + "\n"
        latex += r"\caption{Per-Run Statistics Summary}" + "\n"
        latex += r"\end{table}" + "\n\n"
        
        return latex
    
    def _generate_autocorr_table(self, analysis: Dict[str, Any]) -> str:
        """Generate LaTeX table for autocorrelation analysis by run"""
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
                lags_str = ", ".join(map(str, sig_lags[:5]))  # Limit to first 5
                if len(sig_lags) > 5:
                    lags_str += "..."
            else:
                lags_str = "None"
            
            latex += f"{run} & {lags_str} & {max_corr:.6f} \\\\\n"
        
        latex += r"\bottomrule" + "\n"
        latex += r"\end{tabular}" + "\n"
        latex += r"\caption{Autocorrelation Analysis by Run}" + "\n"
        latex += r"\end{table}" + "\n\n"
        
        return latex
    
    def _generate_overlaid_ecdf_chart(self, analysis: Dict[str, Any], temp_dir: str) -> str:
        """Generate overlaid ECDF chart with reference line"""
        ecdf_all_runs = analysis.get("ecdf_all_runs", [])
        if not ecdf_all_runs:
            return None
        
        fig, ax = plt.subplots(figsize=(10, 6))
        colors_list = plt.cm.tab10(np.linspace(0, 1, len(ecdf_all_runs)))
        
        for idx, run_data in enumerate(ecdf_all_runs):
            run_x = run_data.get("x", [])
            run_y = run_data.get("y", [])
            if run_x and run_y:
                step = max(1, len(run_x) // 1000) if len(run_x) > 1000 else 1
                run_num = run_data.get("run", idx + 1)
                ax.plot(run_x[::step], run_y[::step], linewidth=1.5, 
                       color=colors_list[idx], label=f'Run {run_num}', alpha=0.7)
        
        # Add reference line for uniform distribution
        all_x_values = []
        for r in ecdf_all_runs:
            if r.get("x"):
                all_x_values.extend(r.get("x", []))
        if all_x_values:
            min_x = min(all_x_values)
            max_x = max(all_x_values)
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
    
    def _generate_overlaid_qq_chart(self, analysis: Dict[str, Any], temp_dir: str) -> str:
        """Generate overlaid Q-Q plot with reference line"""
        individual_analyses = analysis.get("individual_analyses", [])
        if not individual_analyses:
            return None
        
        fig, ax = plt.subplots(figsize=(10, 10))
        colors_list = plt.cm.tab10(np.linspace(0, 1, len(individual_analyses)))
        
        for idx, run_analysis in enumerate(individual_analyses):
            if "distribution" in run_analysis and "qq_plot" in run_analysis["distribution"]:
                theoretical = run_analysis["distribution"]["qq_plot"].get("theoretical", [])
                sample = run_analysis["distribution"]["qq_plot"].get("sample", [])
                if theoretical and sample:
                    step = max(1, len(theoretical) // 500) if len(theoretical) > 500 else 1
                    ax.scatter(theoretical[::step], sample[::step], alpha=0.3, s=15,
                             color=colors_list[idx], edgecolors='black', linewidth=0.3,
                             label=f'Run {idx + 1}')
        
        # Add diagonal reference line
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
    
    def _generate_frequency_histogram_chart(self, analysis: Dict[str, Any], temp_dir: str) -> str:
        """Generate frequency histogram chart across all runs"""
        frequency_histogram = analysis.get("frequency_histogram", {})
        bins = frequency_histogram.get("bins", [])
        frequencies = frequency_histogram.get("frequencies", [])
        bin_edges = frequency_histogram.get("bin_edges", [])
        
        if not bins or not frequencies or len(bins) == 0:
            return None
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Calculate bar widths from bin_edges if available, otherwise estimate
        if bin_edges and len(bin_edges) > 1:
            widths = [bin_edges[i+1] - bin_edges[i] for i in range(len(bin_edges)-1)]
            # Use bar chart with proper widths
            ax.bar(bins, frequencies, width=widths, color='steelblue', edgecolor='black', alpha=0.7, align='center')
        else:
            # Fallback: estimate width from bin centers
            if len(bins) > 1:
                avg_width = (max(bins) - min(bins)) / len(bins) * 0.8  # 0.8 for spacing
            else:
                avg_width = 0.01
            ax.bar(bins, frequencies, width=avg_width, color='steelblue', edgecolor='black', alpha=0.7)
        
        ax.set_xlabel('Value (Bin Center)')
        ax.set_ylabel('Frequency')
        ax.set_title('Frequency Histogram Across All Runs')
        ax.grid(True, alpha=0.3, axis='y')
        
        # Rotate x-axis labels if there are many bins
        if len(bins) > 20:
            plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        
        filename = "frequency_histogram.png"
        filepath = os.path.join(temp_dir, filename)
        fig.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        return filename
    
    def _generate_per_run_analysis(self, run_analysis: Dict[str, Any], run_num: int, temp_dir: str) -> str:
        """Generate LaTeX content for per-run analysis"""
        latex = ""
        
        # Category 1: Descriptive Statistics
        latex += r"\subsection{Category 1: Descriptive Statistics}" + "\n\n"
        basic_stats = run_analysis.get("basic_stats", {})
        latex += self._generate_descriptive_stats_table(basic_stats)
        
        # Category 2: Distributional Tests
        latex += r"\subsection{Category 2: Distributional Tests}" + "\n\n"
        dist = run_analysis.get("distribution", {})
        
        # KDE chart
        if "kde" in dist:
            kde_path = self._generate_kde_chart(dist["kde"], run_num, temp_dir)
            if kde_path:
                latex += r"\begin{figure}[H]" + "\n"
                latex += r"\centering" + "\n"
                latex += f"\\includegraphics[width=0.8\\textwidth]{{{kde_path}}}" + "\n"
                latex += r"\caption{Kernel Density Estimate (KDE)}" + "\n"
                latex += r"\end{figure}" + "\n\n"
        
        # ECDF chart
        if "range_behavior" in run_analysis and "ecdf" in run_analysis["range_behavior"]:
            ecdf_path = self._generate_ecdf_chart(run_analysis["range_behavior"]["ecdf"], run_num, temp_dir)
            if ecdf_path:
                latex += r"\begin{figure}[H]" + "\n"
                latex += r"\centering" + "\n"
                latex += f"\\includegraphics[width=0.8\\textwidth]{{{ecdf_path}}}" + "\n"
                latex += r"\caption{Empirical Cumulative Distribution Function (ECDF)}" + "\n"
                latex += r"\end{figure}" + "\n\n"
        
        # Q-Q Plot
        if "qq_plot" in dist:
            qq_path = self._generate_qq_chart(dist["qq_plot"], run_num, temp_dir)
            if qq_path:
                latex += r"\begin{figure}[H]" + "\n"
                latex += r"\centering" + "\n"
                latex += f"\\includegraphics[width=0.8\\textwidth]{{{qq_path}}}" + "\n"
                latex += r"\caption{Q-Q Plot (Uniform Distribution)}" + "\n"
                latex += r"\end{figure}" + "\n\n"
        
        # KS test
        if "is_uniform" in dist:
            is_uniform = dist["is_uniform"]
            ks_p = is_uniform.get("ks_p", "N/A")
            ks_stat = is_uniform.get("ks_stat", "N/A")
            latex += f"\\textbf{{Kolmogorov-Smirnov Test:}}\\\\[0.5em]\n"
            if isinstance(ks_p, (int, float)):
                latex += f"P-value: {ks_p:.6f}\\\\[0.5em]\n"
            else:
                latex += f"P-value: {ks_p}\\\\[0.5em]\n"
            if isinstance(ks_stat, (int, float)):
                latex += f"Statistic: {ks_stat:.6f}\\\\[1em]\n\n"
            else:
                latex += f"Statistic: {ks_stat}\\\\[1em]\n\n"
        
        # Category 3: Independence Tests
        latex += r"\subsection{Category 3: Independence Tests}" + "\n\n"
        ind = run_analysis.get("independence", {})
        
        # ACF chart
        if "autocorrelation" in ind:
            acf_path = self._generate_acf_chart(ind["autocorrelation"], run_num, temp_dir)
            if acf_path:
                latex += r"\begin{figure}[H]" + "\n"
                latex += r"\centering" + "\n"
                latex += f"\\includegraphics[width=0.8\\textwidth]{{{acf_path}}}" + "\n"
                latex += r"\caption{Autocorrelation Function (ACF)}" + "\n"
                latex += r"\end{figure}" + "\n\n"
        
        # Lag-1 Scatter plot
        if "lag1_scatter" in ind:
            lag1_path = self._generate_lag1_scatter_chart(ind["lag1_scatter"], run_num, temp_dir)
            if lag1_path:
                latex += r"\begin{figure}[H]" + "\n"
                latex += r"\centering" + "\n"
                latex += f"\\includegraphics[width=0.8\\textwidth]{{{lag1_path}}}" + "\n"
                latex += r"\caption{Lag-1 Scatter Plot}" + "\n"
                latex += r"\end{figure}" + "\n\n"
        
        # Category 4: Temporal Analysis
        latex += r"\subsection{Category 4: Temporal Analysis}" + "\n\n"
        
        # Time series plot
        if "time_series" in ind:
            ts_path = self._generate_time_series_chart(ind["time_series"], run_num, temp_dir)
            if ts_path:
                latex += r"\begin{figure}[H]" + "\n"
                latex += r"\centering" + "\n"
                latex += f"\\includegraphics[width=0.8\\textwidth]{{{ts_path}}}" + "\n"
                latex += r"\caption{Time Series Plot}" + "\n"
                latex += r"\end{figure}" + "\n\n"
        
        # Rolling mean and std plots
        stat = run_analysis.get("stationarity", {})
        if "rolling_mean" in stat and "rolling_std" in stat:
            rolling_path = self._generate_rolling_stats_chart(stat, run_num, temp_dir)
            if rolling_path:
                latex += r"\begin{figure}[H]" + "\n"
                latex += r"\centering" + "\n"
                latex += f"\\includegraphics[width=0.8\\textwidth]{{{rolling_path}}}" + "\n"
                latex += r"\caption{Rolling Mean and Standard Deviation}" + "\n"
                latex += r"\end{figure}" + "\n\n"
        
        # Chunked statistics (if available)
        # TODO: Add chunked statistics if available in analysis
        
        # Category 5: Spectral Analysis
        latex += r"\subsection{Category 5: Spectral Analysis}" + "\n\n"
        spec = run_analysis.get("spectral", {})
        
        # FFT Magnitude Spectrum
        if "frequencies" in spec and "magnitude" in spec:
            fft_path = self._generate_fft_chart(spec, run_num, temp_dir)
            if fft_path:
                latex += r"\begin{figure}[H]" + "\n"
                latex += r"\centering" + "\n"
                latex += f"\\includegraphics[width=0.8\\textwidth]{{{fft_path}}}" + "\n"
                latex += r"\caption{FFT Magnitude Spectrum}" + "\n"
                latex += r"\end{figure}" + "\n\n"
        
        # Power spectrum
        if "frequencies" in spec and "power" in spec:
            power_path = self._generate_power_spectrum_chart(spec, run_num, temp_dir)
            if power_path:
                latex += r"\begin{figure}[H]" + "\n"
                latex += r"\centering" + "\n"
                latex += f"\\includegraphics[width=0.8\\textwidth]{{{power_path}}}" + "\n"
                latex += r"\caption{Power Spectrum}" + "\n"
                latex += r"\end{figure}" + "\n\n"
        
        # Category 6: NIST Binary Tests
        latex += r"\subsection{Category 6: NIST Binary Tests}" + "\n\n"
        nist = run_analysis.get("nist_tests", {})
        
        # Collect all NIST test tables
        nist_tables = []
        
        # Runs test
        if "runs_test" in nist:
            nist_tables.append(("Runs Test", nist["runs_test"]))
        
        # Binary Matrix Rank
        if "binary_matrix_rank_test" in nist:
            nist_tables.append(("Binary Matrix Rank Test", nist["binary_matrix_rank_test"]))
        
        # Approximate Entropy
        if "approximate_entropy_test" in nist:
            nist_tables.append(("Approximate Entropy Test", nist["approximate_entropy_test"]))
        
        # Longest Run of Ones
        if "longest_run_of_ones_test" in nist:
            nist_tables.append(("Longest Run of Ones Test", nist["longest_run_of_ones_test"]))
        
        # Display tables in 2x2 grid
        if nist_tables:
            latex += self._generate_nist_tables_grid(nist_tables)
        
        return latex
    
    def _generate_descriptive_stats_table(self, basic_stats: Dict[str, Any]) -> str:
        """Generate LaTeX table for descriptive statistics"""
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
            if isinstance(value, (int, float)):
                latex += f"{metric} & {value:.6f} \\\\\n"
            else:
                latex += f"{metric} & {value} \\\\\n"
        
        latex += r"\bottomrule" + "\n"
        latex += r"\end{tabular}" + "\n"
        latex += r"\caption{Descriptive Statistics}" + "\n"
        latex += r"\end{table}" + "\n\n"
        
        return latex
    
    # Chart generation methods
    def _generate_kde_chart(self, kde_data: Dict[str, Any], run_num: int, temp_dir: str) -> str:
        """Generate KDE chart"""
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
    
    def _generate_ecdf_chart(self, ecdf_data: Dict[str, Any], run_num: int, temp_dir: str) -> str:
        """Generate ECDF chart"""
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
    
    def _generate_qq_chart(self, qq_data: Dict[str, Any], run_num: int, temp_dir: str) -> str:
        """Generate Q-Q plot"""
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
    
    def _generate_acf_chart(self, acf_data: Dict[str, Any], run_num: int, temp_dir: str) -> str:
        """Generate ACF chart"""
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
    
    def _generate_lag1_scatter_chart(self, lag1_data: Dict[str, Any], run_num: int, temp_dir: str) -> str:
        """Generate Lag-1 scatter plot"""
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
    
    def _generate_time_series_chart(self, ts_data: Dict[str, Any], run_num: int, temp_dir: str) -> str:
        """Generate time series plot"""
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
    
    def _generate_rolling_stats_chart(self, stat_data: Dict[str, Any], run_num: int, temp_dir: str) -> str:
        """Generate rolling statistics charts"""
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
    
    def _generate_fft_chart(self, spec_data: Dict[str, Any], run_num: int, temp_dir: str) -> str:
        """Generate FFT magnitude spectrum chart"""
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
    
    def _generate_power_spectrum_chart(self, spec_data: Dict[str, Any], run_num: int, temp_dir: str) -> str:
        """Generate power spectrum chart"""
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
    
    def _generate_nist_test_table_content(self, nist_test: Dict[str, Any], test_name: str) -> str:
        """Generate LaTeX table content for NIST test results (without table environment, for use in minipage)"""
        if "error" in nist_test and nist_test["error"]:
            return f"\\textbf{{{test_name}:}}\\\\[0.5em]\nError: {self.escape_latex(str(nist_test['error']))}"
        
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
        latex += f"\\captionof{{table}}{{{self.escape_latex(test_name)}}}" + "\n"
        
        return latex
    
    def _generate_nist_tables_grid(self, nist_tables: List[tuple]) -> str:
        """Generate NIST test tables in a 2x2 grid layout"""
        if not nist_tables:
            return ""
        
        latex = ""
        
        # Process tables in pairs (2 per row)
        for i in range(0, len(nist_tables), 2):
            latex += r"\begin{table}[H]" + "\n"
            latex += r"\centering" + "\n"
            
            # First table in the row
            test_name1, nist_test1 = nist_tables[i]
            latex += r"\begin{minipage}{0.48\textwidth}" + "\n"
            latex += r"\centering" + "\n"
            latex += self._generate_nist_test_table_content(nist_test1, test_name1)
            latex += r"\end{minipage}" + "\n"
            latex += r"\hfill" + "\n"
            
            # Second table in the row (if exists)
            if i + 1 < len(nist_tables):
                test_name2, nist_test2 = nist_tables[i + 1]
                latex += r"\begin{minipage}{0.48\textwidth}" + "\n"
                latex += r"\centering" + "\n"
                latex += self._generate_nist_test_table_content(nist_test2, test_name2)
                latex += r"\end{minipage}" + "\n"
            
            latex += r"\end{table}" + "\n\n"
        
        return latex
    
    def cleanup(self):
        """Clean up temporary files"""
        with self._lock:
            if self._temp_dir and os.path.exists(self._temp_dir):
                try:
                    shutil.rmtree(self._temp_dir)
                    logger.info(f"Cleaned up temporary directory: {self._temp_dir}")
                except Exception as e:
                    logger.warning(f"Error cleaning up temp directory: {e}")
                self._temp_dir = None
    
    def __del__(self):
        """Cleanup on destruction"""
        self.cleanup()


# Backward compatibility: Keep the old function interface
def generate_latex_pdf(analysis: Dict[str, Any], runs_data: List[List[float]], temp_dir: str) -> bytes:
    """
    Generate LaTeX code and compile to PDF (backward compatibility function)
    
    Args:
        analysis: Analysis data dictionary
        runs_data: List of runs (list of numbers)
        temp_dir: Temporary directory for files
        
    Returns:
        PDF bytes
    """
    generator = LatexGenerator()
    return generator._generate_latex_pdf(analysis, runs_data, temp_dir)
