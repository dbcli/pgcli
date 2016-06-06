from __future__ import unicode_literals

from prompt_toolkit.layout.utils import split_lines
from prompt_toolkit.token import Token


def test_split_lines():
    lines = list(split_lines([(Token.A, 'line1\nline2\nline3')]))

    assert lines == [
        [(Token.A, 'line1')],
        [(Token.A, 'line2')],
        [(Token.A, 'line3')],
    ]


def test_split_lines_2():
    lines = list(split_lines([
        (Token.A, 'line1'),
        (Token.B, 'line2\nline3\nline4')
    ]))

    assert lines == [
        [(Token.A, 'line1'), (Token.B, 'line2')],
        [(Token.B, 'line3')],
        [(Token.B, 'line4')],
    ]


def test_split_lines_3():
    " Edge cases: inputs ending with newlines. "
    # -1-
    lines = list(split_lines([
        (Token.A, 'line1\nline2\n')
    ]))

    assert lines == [
        [(Token.A, 'line1')],
        [(Token.A, 'line2')],
        [(Token.A, '')],
    ]

    # -2-
    lines = list(split_lines([
        (Token.A, '\n'),
    ]))

    assert lines == [
        [],
        [(Token.A, '')],
    ]

    # -3-
    lines = list(split_lines([
        (Token.A, ''),
    ]))

    assert lines == [
        [(Token.A, '')],
    ]
