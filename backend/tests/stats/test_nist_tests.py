"""Tests for backend/stats/nist_tests.py.

Validates Monobit, Block Frequency, CUSUM, Spectral/DFT, and Approximate Entropy
against independent reference calculations.
"""
import numpy as np
import pytest
from scipy.special import erfc, gammaincc
from scipy.stats import chi2, norm

from stats import nist_tests as nist_mod


class TestNumbersToBinary:
    """Tests for numbers_to_binary."""

    def test_empty_array_returns_empty_list(self):
        assert nist_mod.numbers_to_binary(np.array([])) == []

    def test_single_number_produces_64_bits(self):
        out = nist_mod.numbers_to_binary(np.array([0.5]))
        assert len(out) == 64
        assert all(b in (0, 1) for b in out)

    def test_multiple_numbers_concatenate(self):
        out = nist_mod.numbers_to_binary(np.array([0.0, 1.0]))
        assert len(out) == 128
        assert all(b in (0, 1) for b in out)

    def test_integer_converted_to_float_bits(self):
        out = nist_mod.numbers_to_binary(np.array([1]))
        assert len(out) == 64
        assert all(b in (0, 1) for b in out)

    def test_zero_and_one_different_sequences(self):
        b0 = nist_mod.numbers_to_binary(np.array([0.0]))
        b1 = nist_mod.numbers_to_binary(np.array([1.0]))
        assert b0 != b1


class TestRunsTest:
    """Tests for runs_test."""

    def test_too_short_returns_error(self):
        out = nist_mod.runs_test([])
        assert out["passed"] is False
        assert "error" in out
        assert "too short" in out["error"].lower() or "short" in out["error"].lower()
        out1 = nist_mod.runs_test([0])
        assert out1["passed"] is False
        assert "error" in out1

    def test_only_ones_returns_error(self):
        out = nist_mod.runs_test([1] * 100)
        assert out["passed"] is False
        assert "error" in out
        assert "one type" in out["error"].lower() or "only" in out["error"].lower()

    def test_only_zeros_returns_error(self):
        out = nist_mod.runs_test([0] * 100)
        assert out["passed"] is False
        assert "error" in out

    def test_alternating_bits(self):
        seq = [0, 1] * 50
        out = nist_mod.runs_test(seq)
        assert "p_value" in out
        assert "statistic" in out
        assert "runs" in out
        assert "passed" in out
        assert out["runs"] == 100
        assert out["ones"] == 50
        assert out["zeros"] == 50

    def test_random_like_sequence(self):
        seq = [0, 0, 1, 1, 0, 1, 0, 0, 1, 1, 1, 0]
        out = nist_mod.runs_test(seq)
        assert "p_value" in out
        assert out["p_value"] is not None
        assert "runs" in out
        assert out["runs"] >= 1


class TestBinaryMatrixRankTest:
    """Tests for binary_matrix_rank_test."""

    def test_only_32_supported(self):
        seq = [0, 1] * (32 * 32)
        out = nist_mod.binary_matrix_rank_test(seq, matrix_size=16)
        assert out["passed"] is False
        assert "error" in out
        assert "32" in out["error"]

    def test_too_short_returns_error(self):
        out = nist_mod.binary_matrix_rank_test([0, 1] * 100, matrix_size=32)
        assert out["passed"] is False
        assert "error" in out
        assert "short" in out["error"].lower() or str(32*32) in out["error"]

    def test_enough_bits_returns_result(self):
        n = 32 * 32 * 5
        seq = list(np.random.randint(0, 2, n))
        out = nist_mod.binary_matrix_rank_test(seq, matrix_size=32)
        assert "p_value" in out
        assert "num_matrices" in out
        assert "full_rank_count" in out
        assert "passed" in out
        assert out["num_matrices"] >= 1
    
    def test_all_zero_matrix_rank_counts(self):
        """Correctness: a 32x32 all-zero matrix has rank 0 (counts should reflect that)."""
        seq = [0] * (32 * 32)  # exactly one matrix
        out = nist_mod.binary_matrix_rank_test(seq, matrix_size=32)
        assert out["num_matrices"] == 1
        assert out["full_rank_count"] == 0
        assert out["rank_minus_1_count"] == 0
        assert out["rank_0_count"] == 1


class TestLongestRunOfOnesTest:
    """Tests for longest_run_of_ones_test."""

    def test_only_128_supported(self):
        seq = [0, 1] * 100
        out = nist_mod.longest_run_of_ones_test(seq, block_size=64)
        assert out["passed"] is False
        assert "error" in out
        assert "128" in out["error"]

    def test_too_short_returns_error(self):
        out = nist_mod.longest_run_of_ones_test([0, 1] * 50, block_size=128)
        assert out["passed"] is False
        assert "error" in out

    def test_enough_bits_returns_result(self):
        seq = list(np.random.randint(0, 2, 128 * 10))
        out = nist_mod.longest_run_of_ones_test(seq, block_size=128)
        assert "p_value" in out
        assert "num_blocks" in out
        assert "run_counts" in out
        assert out["num_blocks"] >= 1
    
    def test_all_zero_blocks_bucket_into_leq4(self):
        """Correctness: if there are no ones, max_run=0 so each block should count toward the <=4 bucket."""
        seq = [0] * (128 * 3)  # 3 blocks
        out = nist_mod.longest_run_of_ones_test(seq, block_size=128)
        assert out["num_blocks"] == 3
        # run_counts keys are strings in output
        assert out["run_counts"]["4"] == 3


class TestApproximateEntropyTest:
    """Tests for approximate_entropy_test."""

    def test_too_short_returns_error(self):
        out = nist_mod.approximate_entropy_test([0, 1] * 5, m=2)
        assert out["passed"] is False
        assert "error" in out
        assert "short" in out["error"].lower() or str(10 * (2**2)) in out["error"]

    def test_enough_bits_returns_result(self):
        n = 10 * (2 ** 2) + 100
        seq = list(np.random.randint(0, 2, n))
        out = nist_mod.approximate_entropy_test(seq, m=2)
        assert "p_value" in out
        assert "approximate_entropy" in out
        assert "passed" in out

    def test_approximate_entropy_matches_reference_circular_counting(self):
        """Reference check for circular overlapping patterns (wrap-around)."""
        m = 2
        n = 100
        seq = ([0, 1] * (n // 2))  # deterministic, balanced

        # --- Reference implementation (independent from backend code style) ---
        bits = list(seq)
        bits_aug = bits + bits[: m + 1]
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

        p_m = vobs_m.astype(float) / n
        p_m1 = vobs_m1.astype(float) / n
        phi_m = np.sum(p_m[p_m > 0] * np.log(p_m[p_m > 0]))
        phi_m1 = np.sum(p_m1[p_m1 > 0] * np.log(p_m1[p_m1 > 0]))
        ap_en = phi_m - phi_m1
        x_obs = 2.0 * n * (np.log(2.0) - ap_en)
        x_obs = max(0.0, x_obs)
        p_value_ref = float(gammaincc(2 ** (m - 1), x_obs / 2.0))

        out = nist_mod.approximate_entropy_test(seq, m=m)
        assert out["passed"] == (p_value_ref > 0.01)
        assert out["p_value"] == pytest.approx(p_value_ref, rel=1e-10, abs=1e-12)
        assert out["statistic"] == pytest.approx(x_obs, rel=1e-10, abs=1e-12)


class TestNistTests:
    """Tests for nist_tests (orchestrator)."""

    def test_returns_all_subtests(self):
        arr = np.random.uniform(0, 1, 50)
        out = nist_mod.nist_tests(arr)
        assert "frequency_test" in out
        assert "frequency_within_block_test" in out
        assert "cumulative_sums_test" in out
        assert "spectral_test" in out
        assert "runs_test" in out
        assert "binary_matrix_rank_test" in out
        assert "longest_run_of_ones_test" in out
        assert "approximate_entropy_test" in out
        assert "binary_sequence_length" in out
        assert out["binary_sequence_length"] == 50 * 64

    def test_small_array_nist_may_fail_but_structure_present(self):
        arr = np.array([0.5, 0.5, 0.5])
        out = nist_mod.nist_tests(arr)
        assert out["runs_test"].get("error") or "p_value" in out["runs_test"]
        assert out["binary_matrix_rank_test"].get("error") or "p_value" in out["binary_matrix_rank_test"]

    def test_nist_tests_correctness_single_run_structure(self):
        """Single-run: nist_tests returns all test keys; runs_test has runs/ones/zeros when no error."""
        arr = np.random.uniform(0, 1, 500)  # enough for some NIST tests
        out = nist_mod.nist_tests(arr)
        assert "frequency_test" in out
        assert "frequency_within_block_test" in out
        assert "cumulative_sums_test" in out
        assert "spectral_test" in out
        assert "runs_test" in out
        assert "binary_matrix_rank_test" in out
        assert "longest_run_of_ones_test" in out
        assert "approximate_entropy_test" in out
        assert "binary_sequence_length" in out
        if "error" not in out["runs_test"]:
            assert "runs" in out["runs_test"]
            assert "ones" in out["runs_test"]
            assert "zeros" in out["runs_test"]
            assert out["runs_test"]["ones"] + out["runs_test"]["zeros"] == out["binary_sequence_length"]


class TestFrequencyAndSpectralTests:
    """Reference-correctness tests for the newly added NIST tests."""

    def test_frequency_test_matches_reference_balanced_and_all_zeros(self):
        n = 100
        seq_balanced = [0, 1] * (n // 2)
        seq_zeros = [0] * n

        def ref_freq(bits):
            ones = sum(bits)
            zeros = len(bits) - ones
            s_obs = abs(ones - zeros) / np.sqrt(len(bits))
            p = float(erfc(s_obs / np.sqrt(2)))
            return p, s_obs

        out_bal = nist_mod.frequency_test(seq_balanced)
        p_ref, s_ref = ref_freq(seq_balanced)
        assert out_bal["p_value"] == pytest.approx(p_ref, rel=1e-12)
        assert out_bal["statistic"] == pytest.approx(s_ref, rel=1e-12)
        assert out_bal["passed"] is True

        out_zero = nist_mod.frequency_test(seq_zeros)
        p_ref0, _ = ref_freq(seq_zeros)
        assert out_zero["p_value"] == pytest.approx(p_ref0, rel=1e-12)
        assert out_zero["passed"] is False

    def test_frequency_within_block_matches_reference_balanced_and_all_ones(self):
        block_size = 20
        n = 400  # 20 blocks
        seq_balanced = [0, 1] * (n // 2)  # each 20-bit block has 10 ones
        seq_ones = [1] * n

        def ref_block_freq(bits):
            m = block_size
            num_blocks = len(bits) // m
            ones_counts = [sum(bits[i * m:(i + 1) * m]) for i in range(num_blocks)]
            expected = m / 2.0
            chi_sq = 4.0 * sum((c - expected) ** 2 for c in ones_counts) / m
            p = float(chi2.sf(chi_sq, df=num_blocks))
            return p, chi_sq

        out_bal = nist_mod.frequency_within_block_test(seq_balanced, block_size=block_size)
        p_ref, chi_sq_ref = ref_block_freq(seq_balanced)
        assert out_bal["p_value"] == pytest.approx(p_ref, rel=1e-12)
        assert out_bal["statistic"] == pytest.approx(chi_sq_ref, rel=1e-12)
        assert out_bal["passed"] is True

        out_ones = nist_mod.frequency_within_block_test(seq_ones, block_size=block_size)
        p_ref0, chi_sq_ref0 = ref_block_freq(seq_ones)
        assert out_ones["p_value"] == pytest.approx(p_ref0, rel=1e-12)
        assert out_ones["statistic"] == pytest.approx(chi_sq_ref0, rel=1e-12)
        assert out_ones["passed"] is False

    def test_cumulative_sums_test_matches_reference_forward_backward(self):
        n = 200
        seq_alt = [0, 1] * (n // 2)
        seq_ones = [1] * n

        def ref_cusum(bits):
            x = np.array([1 if b == 1 else -1 for b in bits], dtype=float)
            z = float(np.max(np.abs(np.cumsum(x))))
            if z == 0.0:
                return 1.0, 0.0
            sqrt_n = np.sqrt(len(bits))

            start1 = int(np.floor(0.25 * np.floor(-len(bits) / z + 1)))
            end1 = int(np.floor(0.25 * np.floor(len(bits) / z - 1)))
            s1 = 0.0
            for k in range(start1, end1 + 1):
                a = norm.cdf((4 * k - 1) * z / sqrt_n)
                b = norm.cdf((4 * k + 1) * z / sqrt_n)
                s1 += b - a

            start2 = int(np.floor(0.25 * np.floor(-len(bits) / z - 3)))
            end2 = int(np.floor(0.25 * np.floor(len(bits) / z) - 1))
            s2 = 0.0
            for k in range(start2, end2 + 1):
                a = norm.cdf((4 * k + 1) * z / sqrt_n)
                b = norm.cdf((4 * k + 3) * z / sqrt_n)
                s2 += b - a

            p = float(1.0 - s1 + s2)
            p = max(0.0, min(1.0, p))
            return p, z

        out_alt = nist_mod.cumulative_sums_test(seq_alt)
        p_f_ref, z_f_ref = ref_cusum(seq_alt)
        p_b_ref, z_b_ref = ref_cusum(list(reversed(seq_alt)))
        assert out_alt["p_value_forward"] == pytest.approx(p_f_ref, rel=1e-12)
        assert out_alt["z_forward"] == pytest.approx(z_f_ref, rel=1e-12)
        assert out_alt["p_value_backward"] == pytest.approx(p_b_ref, rel=1e-12)
        assert out_alt["z_backward"] == pytest.approx(z_b_ref, rel=1e-12)
        assert out_alt["p_value"] == pytest.approx(min(p_f_ref, p_b_ref), rel=1e-12)

        out_ones = nist_mod.cumulative_sums_test(seq_ones)
        p_f_ref0, _ = ref_cusum(seq_ones)
        assert out_ones["p_value_forward"] == pytest.approx(p_f_ref0, rel=1e-12)
        assert out_ones["passed"] is False

    def test_spectral_test_matches_reference(self):
        n = 512
        seq = [0, 1] * (n // 2)  # periodic -> should deviate from randomness

        def ref_spectral(bits):
            x = np.array([1 if b == 1 else -1 for b in bits], dtype=float)
            spectral = np.fft.fft(x)
            m = int(np.floor(len(bits) / 2))
            modulus = np.abs(spectral[:m])
            tau = np.sqrt(np.log(1 / 0.05) * len(bits))
            n0 = 0.95 * (len(bits) / 2.0)
            n1 = int(np.sum(modulus < tau))
            d = (n1 - n0) / np.sqrt(len(bits) * 0.95 * 0.05 / 4.0)
            p = float(erfc(abs(d) / np.sqrt(2)))
            return p, d, tau, n0, n1

        out = nist_mod.spectral_test(seq)
        p_ref, d_ref, tau_ref, n0_ref, n1_ref = ref_spectral(seq)
        assert out["p_value"] == pytest.approx(p_ref, rel=1e-12)
        assert out["statistic"] == pytest.approx(d_ref, rel=1e-12)
        assert out["tau"] == pytest.approx(tau_ref, rel=1e-12)
        assert out["n0"] == pytest.approx(n0_ref, rel=1e-12)
        assert out["n1"] == pytest.approx(n1_ref, rel=1e-12)
