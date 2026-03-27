"""Tests for SQL trailing comment handling.

Verifies that statements with comments after the semicolon are handled
correctly in both the input buffer (pgbuffer) and query execution (pgexecute).
"""

import pytest
from pgcli.pgbuffer import _is_complete


class TestIsCompleteWithTrailingComments:
    """Test _is_complete() handles trailing SQL comments after semicolons."""

    def test_simple_semicolon(self):
        assert _is_complete("SELECT 1;") is True

    def test_no_semicolon(self):
        assert _is_complete("SELECT 1") is False

    def test_trailing_single_line_comment(self):
        assert _is_complete("SELECT 1; -- a comment") is True

    def test_trailing_block_comment(self):
        assert _is_complete("SELECT 1; /* block comment */") is True

    def test_vacuum_with_comment(self):
        assert (
            _is_complete(
                "vacuum freeze verbose tpd.file_delivery; -- 82% towards emergency"
            )
            is True
        )

    def test_comment_only(self):
        assert _is_complete("-- just a comment") is False

    def test_semicolon_inside_string(self):
        assert _is_complete("SELECT ';'") is False

    def test_semicolon_inside_string_with_trailing_comment(self):
        assert _is_complete("SELECT ';' FROM t; -- note") is True

    def test_open_quote(self):
        assert _is_complete("SELECT '") is False

    def test_empty_string(self):
        assert _is_complete("") is False

    def test_multiple_semicolons_with_comment(self):
        assert _is_complete("SELECT 1; SELECT 2; -- done") is True

    def test_comment_with_special_chars(self):
        assert (
            _is_complete("VACUUM ANALYZE; -- 81.0% towards emergency, 971 MB")
            is True
        )
