from __future__ import unicode_literals

from prompt_toolkit.layout.utils import split_lines


def test_split_lines():
    lines = list(split_lines([('class:a', 'line1\nline2\nline3')]))

    assert lines == [
        [('class:a', 'line1')],
        [('class:a', 'line2')],
        [('class:a', 'line3')],
    ]


def test_split_lines_2():
    lines = list(split_lines([
        ('class:a', 'line1'),
        ('class:b', 'line2\nline3\nline4')
    ]))

    assert lines == [
        [('class:a', 'line1'), ('class:b', 'line2')],
        [('class:b', 'line3')],
        [('class:b', 'line4')],
    ]


def test_split_lines_3():
    " Edge cases: inputs ending with newlines. "
    # -1-
    lines = list(split_lines([
        ('class:a', 'line1\nline2\n')
    ]))

    assert lines == [
        [('class:a', 'line1')],
        [('class:a', 'line2')],
        [('class:a', '')],
    ]

    # -2-
    lines = list(split_lines([
        ('class:a', '\n'),
    ]))

    assert lines == [
        [],
        [('class:a', '')],
    ]

    # -3-
    lines = list(split_lines([
        ('class:a', ''),
    ]))

    assert lines == [
        [('class:a', '')],
    ]
