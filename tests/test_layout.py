from __future__ import unicode_literals

from prompt_toolkit.layout import Layout, InvalidLayoutError
from prompt_toolkit.layout.containers import HSplit, VSplit, Window
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.layout.utils import split_lines
import pytest


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


def test_layout_class():
    c1 = BufferControl()
    c2 = BufferControl()
    c3 = BufferControl()
    win1 = Window(content=c1)
    win2 = Window(content=c2)
    win3 = Window(content=c3)

    layout = Layout(container=VSplit([
        HSplit([
            win1,
            win2
        ]),
        win3
    ]))

    # Listing of windows/controls.
    assert list(layout.find_all_windows()) == [win1, win2, win3]
    assert list(layout.find_all_controls()) == [c1, c2, c3]

    # Focussing something.
    layout.focus(c1)
    assert layout.has_focus(c1)
    assert layout.has_focus(win1)
    assert layout.current_control == c1
    assert layout.previous_control == c1

    layout.focus(c2)
    assert layout.has_focus(c2)
    assert layout.has_focus(win2)
    assert layout.current_control == c2
    assert layout.previous_control == c1

    layout.focus(win3)
    assert layout.has_focus(c3)
    assert layout.has_focus(win3)
    assert layout.current_control == c3
    assert layout.previous_control == c2

    # Pop focus. This should focus the previous control again.
    layout.focus_last()
    assert layout.has_focus(c2)
    assert layout.has_focus(win2)
    assert layout.current_control == c2
    assert layout.previous_control == c1


def test_create_invalid_layout():
    with pytest.raises(InvalidLayoutError):
        Layout(HSplit([]))
