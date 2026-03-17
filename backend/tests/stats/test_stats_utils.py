"""Tests for backend/stats/utils.py - convert_numpy_types, downsample, downsample_single."""
import numpy as np
import pytest

from stats.utils import (
    convert_numpy_types,
    downsample,
    downsample_single,
    MAX_CHART_POINTS,
)


class TestConvertNumpyTypes:
    """Tests for convert_numpy_types."""

    def test_numpy_int_converted_to_python_int(self):
        assert convert_numpy_types(np.int32(42)) == 42
        assert convert_numpy_types(np.int64(0)) == 0
        assert convert_numpy_types(np.uint8(255)) == 255

    def test_numpy_float_converted_to_python_float(self):
        assert convert_numpy_types(np.float64(3.14)) == 3.14
        assert convert_numpy_types(np.float32(0.0)) == 0.0

    def test_numpy_array_converted_recursively(self):
        arr = np.array([1, 2, np.float64(3.0)])
        result = convert_numpy_types(arr)
        assert result == [1, 2, 3.0]
        assert all(isinstance(x, (int, float)) for x in result)

    def test_dict_converted_recursively(self):
        d = {"a": np.int32(1), "b": np.float64(2.5), "nested": {"c": np.array([1, 2])}}
        result = convert_numpy_types(d)
        assert result == {"a": 1, "b": 2.5, "nested": {"c": [1, 2]}}

    def test_list_converted_recursively(self):
        lst = [np.int32(1), [np.float64(2.0), np.int64(3)]]
        assert convert_numpy_types(lst) == [1, [2.0, 3]]

    def test_tuple_converted_to_list_of_native_types(self):
        t = (np.int32(1), np.float64(2.0))
        result = convert_numpy_types(t)
        assert result == [1, 2.0]

    def test_plain_python_types_unchanged(self):
        assert convert_numpy_types(42) == 42
        assert convert_numpy_types(3.14) == 3.14
        assert convert_numpy_types("hello") == "hello"
        assert convert_numpy_types(None) is None
        assert convert_numpy_types(True) is True

    def test_empty_structures(self):
        assert convert_numpy_types([]) == []
        assert convert_numpy_types({}) == {}
        assert convert_numpy_types(np.array([])) == []


class TestDownsample:
    """Tests for downsample."""

    def test_short_arrays_returned_unchanged(self):
        x = np.array([1.0, 2.0, 3.0])
        y = np.array([10.0, 20.0, 30.0])
        out_x, out_y = downsample(x, y, max_points=100)
        assert out_x == [1.0, 2.0, 3.0]
        assert out_y == [10.0, 20.0, 30.0]

    def test_exact_max_points_returned_unchanged(self):
        n = 100
        x = np.arange(n, dtype=float)
        y = np.arange(n, dtype=float) * 2
        out_x, out_y = downsample(x, y, max_points=n)
        assert len(out_x) == n
        assert len(out_y) == n

    def test_long_arrays_downsampled_to_max_points(self):
        n = 10000
        x = np.arange(n, dtype=float)
        y = np.arange(n, dtype=float)
        out_x, out_y = downsample(x, y, max_points=500)
        assert len(out_x) <= 501  # may include last point
        assert len(out_y) <= 501
        assert out_x[0] == 0.0
        assert out_x[-1] == float(n - 1)
        assert out_y[0] == 0.0
        assert out_y[-1] == float(n - 1)

    def test_first_and_last_preserved(self):
        n = 2000
        x = np.linspace(0, 1, n)
        y = np.linspace(10, 20, n)
        out_x, out_y = downsample(x, y, max_points=50)
        assert out_x[0] == pytest.approx(0.0)
        assert out_x[-1] == pytest.approx(1.0)
        assert out_y[0] == pytest.approx(10.0)
        assert out_y[-1] == pytest.approx(20.0)

    def test_single_element_arrays(self):
        x = np.array([1.0])
        y = np.array([2.0])
        out_x, out_y = downsample(x, y, max_points=10)
        assert out_x == [1.0]
        assert out_y == [2.0]

    def test_mismatched_length_raises_or_uses_min(self):
        # When n > max_points we use indices into both arrays; if y is shorter we get IndexError.
        x = np.arange(100, dtype=float)
        y = np.arange(50, dtype=float)
        with pytest.raises(IndexError):
            downsample(x, y, max_points=20)


class TestDownsampleSingle:
    """Tests for downsample_single."""

    def test_short_array_returned_unchanged(self):
        arr = np.array([1.0, 2.0, 3.0])
        out = downsample_single(arr, max_points=100)
        assert out == [1.0, 2.0, 3.0]

    def test_long_array_downsampled(self):
        n = 5000
        arr = np.arange(n, dtype=float)
        out = downsample_single(arr, max_points=500)
        assert len(out) <= 501
        assert out[0] == 0.0
        assert out[-1] == float(n - 1)

    def test_empty_array(self):
        arr = np.array([], dtype=float)
        out = downsample_single(arr, max_points=10)
        assert out == []

    def test_single_element(self):
        arr = np.array([42.0])
        out = downsample_single(arr, max_points=10)
        assert out == [42.0]


class TestMaxChartPoints:
    """Sanity check constant."""
    def test_max_chart_points_positive(self):
        assert MAX_CHART_POINTS > 0
