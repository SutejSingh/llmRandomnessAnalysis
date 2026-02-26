"""Tests for backend/stats/nist_tests.py - numbers_to_binary, runs_test, matrix_rank, longest_run, approximate_entropy, nist_tests."""
import numpy as np
import pytest

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


class TestNistTests:
    """Tests for nist_tests (orchestrator)."""

    def test_returns_all_subtests(self):
        arr = np.random.uniform(0, 1, 50)
        out = nist_mod.nist_tests(arr)
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
