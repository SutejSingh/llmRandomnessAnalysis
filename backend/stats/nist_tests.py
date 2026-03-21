"""NIST randomness tests on binary representation of numbers.

These tests are intended to follow NIST SP 800-22 Rev. 1a-style definitions
for binary sequences, using significance alpha=0.01.
"""

import struct
from typing import Any, Dict, List

import numpy as np
from scipy import stats
from scipy.special import erfc, gammaincc
from scipy.stats import chi2


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


def frequency_test(binary_sequence: List[int]) -> Dict[str, Any]:
    """NIST Frequency (Monobit) Test.

    Tests whether the number of ones is approximately n/2.
    """
    n = len(binary_sequence)
    if n < 1:
        return {"p_value": None, "statistic": None, "passed": False, "error": "Sequence too short"}

    ones = int(sum(binary_sequence))
    zeros = int(n - ones)
    # S = (#1 - #0)
    s_obs = abs(ones - zeros) / np.sqrt(n)
    p_value = float(erfc(s_obs / np.sqrt(2)))
    passed = bool(p_value > 0.01)
    return {
        "p_value": p_value,
        "statistic": float(s_obs),
        "ones": ones,
        "zeros": zeros,
        "passed": passed,
    }


def frequency_within_block_test(binary_sequence: List[int], block_size: int = 20) -> Dict[str, Any]:
    """NIST Frequency Test within a Block.

    Partitions the sequence into non-overlapping blocks of size `block_size`.
    """
    n = len(binary_sequence)
    if n < block_size:
        return {
            "p_value": None,
            "statistic": None,
            "passed": False,
            "error": f"Sequence too short (need at least {block_size} bits)",
        }

    num_blocks = n // block_size
    if num_blocks < 1:
        return {"p_value": None, "statistic": None, "passed": False, "error": "Cannot form any blocks"}

    expected_ones = block_size / 2.0
    ones_per_block: List[int] = []
    chi_square = 0.0
    for i in range(num_blocks):
        start = i * block_size
        block = binary_sequence[start:start + block_size]
        ones_block = int(sum(block))
        ones_per_block.append(ones_block)
        chi_square += ((ones_block - expected_ones) ** 2)

    # χ² = 4 * Σ (π_i - 0.5)^2 * m = 4/m * Σ (ones_i - m/2)^2
    chi_square = 4.0 * chi_square / block_size
    # p = IGAMC(N/2, χ²/2) => chi2.sf(χ², df=N)
    p_value = float(chi2.sf(chi_square, df=num_blocks))
    passed = bool(p_value > 0.01)
    ones_preview = ones_per_block[:10]
    ones_tail_preview = ones_per_block[-10:] if len(ones_per_block) > 20 else []
    ones_summary = {
        "min": int(min(ones_per_block)) if ones_per_block else None,
        "max": int(max(ones_per_block)) if ones_per_block else None,
        "mean": float(np.mean(ones_per_block)) if ones_per_block else None,
        "preview": [int(x) for x in ones_preview],
        "tail_preview": [int(x) for x in ones_tail_preview] if ones_tail_preview else [],
    }
    return {
        "p_value": p_value,
        "statistic": float(chi_square),
        "num_blocks": int(num_blocks),
        "block_size": int(block_size),
        "ones_per_block_summary": ones_summary,
        "passed": passed,
    }


def _cumulative_sums_p_value(binary_sequence_pm1: np.ndarray) -> Dict[str, Any]:
    """Compute CUSUM p-value for one direction given Z_i in {-1, +1}."""
    n = int(len(binary_sequence_pm1))
    if n < 1:
        return {"p_value": None, "statistic": None, "passed": False, "error": "Sequence too short"}

    cumulative = np.cumsum(binary_sequence_pm1)
    abs_max = float(np.max(np.abs(cumulative)))
    if abs_max == 0.0:
        return {
            "p_value": 1.0,
            "statistic": 0.0,
            "passed": True,
        }

    sqrt_n = float(np.sqrt(n))
    z = abs_max
    # NIST uses the distribution of the maximum absolute partial sum.
    # This is implemented here using the summation form found in NIST SP 800-22 Rev 1a reference code.
    start1 = int(np.floor(0.25 * np.floor(-n / z + 1)))
    end1 = int(np.floor(0.25 * np.floor(n / z - 1)))
    terms_one = []
    for k in range(start1, end1 + 1):
        a = stats.norm.cdf((4 * k - 1) * z / sqrt_n)
        b = stats.norm.cdf((4 * k + 1) * z / sqrt_n)
        terms_one.append(b - a)

    start2 = int(np.floor(0.25 * np.floor(-n / z - 3)))
    end2 = int(np.floor(0.25 * np.floor(n / z) - 1))
    terms_two = []
    for k in range(start2, end2 + 1):
        a = stats.norm.cdf((4 * k + 1) * z / sqrt_n)
        b = stats.norm.cdf((4 * k + 3) * z / sqrt_n)
        terms_two.append(b - a)

    p_value = float(1.0 - float(np.sum(terms_one)) + float(np.sum(terms_two)))
    # Numerics: clamp to [0,1]
    p_value = max(0.0, min(1.0, p_value))
    passed = bool(p_value > 0.01)
    return {"p_value": p_value, "statistic": z, "passed": passed}


def cumulative_sums_test(binary_sequence: List[int]) -> Dict[str, Any]:
    """NIST Cumulative Sums Test (CUSUM).

    Computes the test for both the forward and backward directions and
    aggregates pass/fail accordingly.
    """
    n = len(binary_sequence)
    if n < 1:
        return {"p_value": None, "statistic": None, "passed": False, "error": "Sequence too short"}

    binary_sequence_pm1 = np.array([1 if b == 1 else -1 for b in binary_sequence], dtype=float)
    forward = _cumulative_sums_p_value(binary_sequence_pm1)
    backward = _cumulative_sums_p_value(binary_sequence_pm1[::-1])

    p_forward = forward.get("p_value")
    p_backward = backward.get("p_value")
    z_forward = forward.get("statistic")
    z_backward = backward.get("statistic")

    # Aggregate: consider the sequence to fail if either direction fails.
    passed = bool((p_forward is not None and p_forward > 0.01) and (p_backward is not None and p_backward > 0.01))
    p_value = min(float(p_forward), float(p_backward)) if p_forward is not None and p_backward is not None else None

    return {
        "p_value": p_value,
        "statistic": float(max(z_forward, z_backward)) if z_forward is not None and z_backward is not None else None,
        "p_value_forward": float(p_forward) if p_forward is not None else None,
        "p_value_backward": float(p_backward) if p_backward is not None else None,
        "z_forward": float(z_forward) if z_forward is not None else None,
        "z_backward": float(z_backward) if z_backward is not None else None,
        "passed": passed,
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
    """NIST Approximate Entropy Test (ApEn) for binary sequences.

    Uses circular overlapping patterns (i.e., the sequence is wrapped so there
    are exactly N overlapping m-bit (and (m+1)-bit) patterns, where N is the
    sequence length).
    """
    n = int(len(binary_sequence))
    min_required = int(10 * (2 ** m))
    if n < min_required:
        return {
            "p_value": None,
            "statistic": None,
            "passed": False,
            "error": f"Sequence too short (need at least {min_required} bits for m={m})",
        }

    # Append m+1 bits so that slicing of length m and m+1 patterns is circular.
    bits = list(binary_sequence)  # ensure indexable
    bits_aug = bits + bits[:m + 1]

    vobs_m = np.zeros(2 ** m, dtype=int)
    vobs_m1 = np.zeros(2 ** (m + 1), dtype=int)

    for i in range(n):
        idx_m = 0
        for j in range(m):
            idx_m = (idx_m << 1) | bits_aug[i + j]
        vobs_m[idx_m] += 1

        idx_m1 = 0
        for j in range(m + 1):
            idx_m1 = (idx_m1 << 1) | bits_aug[i + j]
        vobs_m1[idx_m1] += 1

    # phi(m) = sum_{i=0}^{2^m-1} (C_i/N)*ln(C_i/N)
    # (terms where C_i=0 contribute 0).
    counts_m = vobs_m.astype(float)
    counts_m1 = vobs_m1.astype(float)
    p_m = counts_m / n
    p_m1 = counts_m1 / n

    mask_m = counts_m > 0
    mask_m1 = counts_m1 > 0
    phi_m = float(np.sum(p_m[mask_m] * np.log(p_m[mask_m])))
    phi_m1 = float(np.sum(p_m1[mask_m1] * np.log(p_m1[mask_m1])))

    ap_en = phi_m - phi_m1
    x_obs = float(2.0 * n * (np.log(2.0) - ap_en))
    x_obs = max(0.0, x_obs)  # numeric safety
    p_value = float(gammaincc(2 ** (m - 1), x_obs / 2.0))
    passed = bool(p_value > 0.01)
    return {
        "p_value": p_value,
        "statistic": x_obs,
        "approximate_entropy": float(ap_en),
        "phi_m": phi_m,
        "phi_m1": phi_m1,
        "pattern_length_m": int(m),
        "pattern_length_m1": int(m + 1),
        "unique_patterns_m": int(np.count_nonzero(vobs_m)),
        "unique_patterns_m1": int(np.count_nonzero(vobs_m1)),
        "passed": passed,
    }


def nist_tests(arr: np.ndarray) -> Dict[str, Any]:
    """Perform NIST statistical tests on binary representation of numbers."""
    binary_sequence = numbers_to_binary(arr)
    return {
        "frequency_test": frequency_test(binary_sequence),
        "frequency_within_block_test": frequency_within_block_test(binary_sequence),
        "cumulative_sums_test": cumulative_sums_test(binary_sequence),
        "spectral_test": spectral_test(binary_sequence),
        "runs_test": runs_test(binary_sequence),
        "binary_matrix_rank_test": binary_matrix_rank_test(binary_sequence),
        "longest_run_of_ones_test": longest_run_of_ones_test(binary_sequence),
        "approximate_entropy_test": approximate_entropy_test(binary_sequence),
        "binary_sequence_length": len(binary_sequence)
    }


def spectral_test(binary_sequence: List[int]) -> Dict[str, Any]:
    """NIST Discrete Fourier Transform (DFT) / Spectral Test."""
    n = len(binary_sequence)
    if n < 2:
        return {"p_value": None, "statistic": None, "passed": False, "error": "Sequence too short"}

    x = [1 if b == 1 else -1 for b in binary_sequence]
    spectral = np.fft.fft(x)
    m = int(np.floor(n / 2))
    modulus = np.abs(spectral[:m])

    tau = float(np.sqrt(np.log(1 / 0.05) * n))
    n0 = 0.95 * (n / 2.0)
    n1 = int(np.sum(modulus < tau))
    d = (n1 - n0) / np.sqrt(n * 0.95 * 0.05 / 4.0)
    p_value = float(erfc(abs(d) / np.sqrt(2)))
    passed = bool(p_value > 0.01)
    return {
        "p_value": p_value,
        "statistic": float(d),
        "tau": tau,
        "n0": float(n0),
        "n1": int(n1),
        "passed": passed,
    }
