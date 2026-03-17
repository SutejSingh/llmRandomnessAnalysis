"""Tests for backend/reporting/common.py - escape_latex."""
import pytest

from reporting.common import escape_latex


class TestEscapeLatex:
    def test_empty_string(self):
        assert escape_latex("") == ""

    def test_ampersand(self):
        assert escape_latex("a & b") == r"a \& b"

    def test_percent(self):
        assert escape_latex("50%") == r"50\%"

    def test_dollar(self):
        assert escape_latex("$100") == r"\$100"

    def test_hash(self):
        assert escape_latex("#tag") == r"\#tag"

    def test_underscore(self):
        assert escape_latex("a_b") == r"a\_b"

    def test_curly_braces(self):
        assert escape_latex("{x}") == r"\{x\}"

    def test_backslash(self):
        # Replacement contains { and }, which get escaped too
        assert escape_latex("\\") == r"\textbackslash\{\}"

    def test_multiple_special(self):
        s = "Price: $10 & 50% off"
        out = escape_latex(s)
        assert r"\$" in out
        assert r"\&" in out
        assert r"\%" in out

    def test_plain_text_unchanged(self):
        assert escape_latex("Hello World 123") == "Hello World 123"

    def test_caret(self):
        assert r"\textasciicircum" in escape_latex("^")

    def test_tilde(self):
        assert r"\textasciitilde" in escape_latex("~")
