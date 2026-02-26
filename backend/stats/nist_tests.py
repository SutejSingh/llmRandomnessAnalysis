"""NIST randomness tests on binary representation of numbers."""
import struct
import numpy as np
from scipy import stats
from scipy.stats import chi2
from typing import Dict, Any, List


def numbers_to_binary(numbers: np.ndarray) -> List[int]:
    """Convert numbers to exact binary representation (IEEE 754 double precision)."""
    binary_sequence = []
    for num in numbers:
        binary_bytes = struct.pack('>d', float(num))
        binary_bits = ''.join(format(byte, '08b') for byte in binary_bytes)
        binary_sequence.extend([int(bit) for bit in binary_bits])
    return binary_sequence


def runs_test(binary_sequence: List[int]) -> Dict[str, Any]:
    """NIST Runs Test."""
    n = len(binary_sequence)
    if n < 2:
        return {"p_value": None, "statistic": None, "passed": False, "error": "Sequence too short"}
    ones = sum(binary_sequence)
    zeros = n - ones
    if ones == 0 or zeros == 0:
        return {"p_value": None, "statistic": None, "passed": False, "error": "Sequence contains only one type of bit"}
    runs = 1
    for i in range(1, n):
        if binary_sequence[i] != binary_sequence[i-1]:
            runs += 1
    expected_runs = (2 * ones * zeros) / n + 1
    variance = (2 * ones * zeros * (2 * ones * zeros - n)) / (n * n * (n - 1))
    if variance <= 0:
        return {"p_value": None, "statistic": None, "passed": False, "error": "Invalid variance"}
    z_stat = (runs - expected_runs) / np.sqrt(variance)
    p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
    passed = p_value > 0.01
    return {
        "p_value": float(p_value),
        "statistic": float(z_stat),
        "runs": int(runs),
        "expected_runs": float(expected_runs),
        "ones": int(ones),
        "zeros": int(zeros),
        "passed": bool(passed)
    }


def binary_matrix_rank_test(binary_sequence: List[int], matrix_size: int = 32) -> Dict[str, Any]:
    """NIST Binary Matrix Rank Test (32x32 supported)."""
    if matrix_size != 32:
        return {"p_value": None, "statistic": None, "passed": False, "error": "Only matrix_size=32 is supported"}
    n = len(binary_sequence)
    min_required = matrix_size * matrix_size
    if n < min_required:
        return {"p_value": None, "statistic": None, "passed": False, "error": f"Sequence too short (need at least {min_required} bits)"}
    num_matrices = n // (matrix_size * matrix_size)
    if num_matrices < 1:
        return {"p_value": None, "statistic": None, "passed": False, "error": "Cannot form any matrices"}
    rank_counts = {matrix_size: 0, matrix_size - 1: 0, 0: 0}
    for i in range(num_matrices):
        start_idx = i * matrix_size * matrix_size
        matrix = []
        for row in range(matrix_size):
            row_start = start_idx + row * matrix_size
            matrix.append(binary_sequence[row_start:row_start + matrix_size])
        matrix_arr = np.array(matrix, dtype=int)
        rank = np.linalg.matrix_rank(matrix_arr)
        if rank == matrix_size:
            rank_counts[matrix_size] += 1
        elif rank == matrix_size - 1:
            rank_counts[matrix_size - 1] += 1
        else:
            rank_counts[0] += 1
    p_full = 0.2888
    p_rank_minus_1 = 0.5776
    p_rank_0 = 0.1336
    expected_full = num_matrices * p_full
    expected_rank_minus_1 = num_matrices * p_rank_minus_1
    expected_rank_0 = num_matrices * p_rank_0
    chi_square = (
        ((rank_counts[matrix_size] - expected_full) ** 2) / expected_full +
        ((rank_counts[matrix_size - 1] - expected_rank_minus_1) ** 2) / expected_rank_minus_1 +
        ((rank_counts[0] - expected_rank_0) ** 2) / expected_rank_0
    )
    p_value = 1 - chi2.cdf(chi_square, 2)
    passed = p_value > 0.01
    return {
        "p_value": float(p_value),
        "statistic": float(chi_square),
        "num_matrices": int(num_matrices),
        "full_rank_count": int(rank_counts[matrix_size]),
        "rank_minus_1_count": int(rank_counts[matrix_size - 1]),
        "rank_0_count": int(rank_counts[0]),
        "passed": bool(passed)
    }


def longest_run_of_ones_test(binary_sequence: List[int], block_size: int = 128) -> Dict[str, Any]:
    """NIST Longest Run of Ones Test (block_size=128 supported)."""
    if block_size != 128:
        return {"p_value": None, "statistic": None, "passed": False, "error": "Only block_size=128 is supported"}
    n = len(binary_sequence)
    if n < block_size:
        return {"p_value": None, "statistic": None, "passed": False, "error": f"Sequence too short (need at least {block_size} bits)"}
    num_blocks = n // block_size
    if num_blocks < 1:
        return {"p_value": None, "statistic": None, "passed": False, "error": "Cannot form any blocks"}
    run_lengths = [4, 5, 6, 7, 8, 9]
    expected_freqs = [0.1174, 0.2430, 0.2493, 0.1752, 0.1027, 0.1124]
    run_counts = {length: 0 for length in run_lengths}
    for i in range(num_blocks):
        start_idx = i * block_size
        block = binary_sequence[start_idx:start_idx + block_size]
        max_run = 0
        current_run = 0
        for bit in block:
            if bit == 1:
                current_run += 1
                max_run = max(max_run, current_run)
            else:
                current_run = 0
        if max_run <= 4:
            run_counts[4] += 1
        elif max_run == 5:
            run_counts[5] += 1
        elif max_run == 6:
            run_counts[6] += 1
        elif max_run == 7:
            run_counts[7] += 1
        elif max_run == 8:
            run_counts[8] += 1
        else:
            run_counts[9] += 1
    chi_square = 0.0
    for length in run_lengths:
        expected = num_blocks * expected_freqs[run_lengths.index(length)]
        observed = run_counts[length]
        if expected > 0:
            chi_square += ((observed - expected) ** 2) / expected
    p_value = 1 - chi2.cdf(chi_square, 5)
    passed = p_value > 0.01
    return {
        "p_value": float(p_value),
        "statistic": float(chi_square),
        "num_blocks": int(num_blocks),
        "run_counts": {str(k): int(v) for k, v in run_counts.items()},
        "passed": bool(passed)
    }


def approximate_entropy_test(binary_sequence: List[int], m: int = 2) -> Dict[str, Any]:
    """NIST Approximate Entropy Test."""
    n = len(binary_sequence)
    min_required = 10 * (2 ** m)
    if n < min_required:
        return {"p_value": None, "statistic": None, "passed": False, "error": f"Sequence too short (need at least {min_required} bits for m={m})"}

    def count_patterns(pattern_length):
        pattern_counts = {}
        num_patterns = n - pattern_length + 1
        for i in range(num_patterns):
            pattern = tuple(binary_sequence[i:i + pattern_length])
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        return pattern_counts, num_patterns

    patterns_m, num_patterns_m = count_patterns(m)
    patterns_m1, num_patterns_m1 = count_patterns(m + 1)

    def calculate_phi(pattern_counts, num_patterns):
        phi = 0.0
        for pattern, count in pattern_counts.items():
            if count > 0:
                prob = count / num_patterns
                phi += prob * np.log(prob + 1e-10)
        return phi

    phi_m = calculate_phi(patterns_m, num_patterns_m)
    phi_m1 = calculate_phi(patterns_m1, num_patterns_m1)
    ap_en = phi_m - phi_m1
    ln2 = np.log(2)
    chi2_stat = 2.0 * n * (ln2 - ap_en)
    if chi2_stat < 0:
        chi2_stat = 0.0
    df = 2 ** m
    p_value = float(1 - chi2.cdf(chi2_stat, df))
    passed = p_value > 0.01
    return {
        "p_value": float(p_value),
        "statistic": float(chi2_stat),
        "approximate_entropy": float(ap_en),
        "phi_m": float(phi_m),
        "phi_m1": float(phi_m1),
        "pattern_length_m": int(m),
        "pattern_length_m1": int(m + 1),
        "num_patterns_m": int(num_patterns_m),
        "num_patterns_m1": int(num_patterns_m1),
        "unique_patterns_m": int(len(patterns_m)),
        "unique_patterns_m1": int(len(patterns_m1)),
        "passed": bool(passed)
    }


def nist_tests(arr: np.ndarray) -> Dict[str, Any]:
    """Perform NIST statistical tests on binary representation of numbers."""
    binary_sequence = numbers_to_binary(arr)
    return {
        "runs_test": runs_test(binary_sequence),
        "binary_matrix_rank_test": binary_matrix_rank_test(binary_sequence),
        "longest_run_of_ones_test": longest_run_of_ones_test(binary_sequence),
        "approximate_entropy_test": approximate_entropy_test(binary_sequence),
        "binary_sequence_length": len(binary_sequence)
    }
