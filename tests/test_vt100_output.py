from __future__ import unicode_literals
from prompt_toolkit.output.vt100 import _get_closest_ansi_color


def test_get_closest_ansi_color():
    # White
    assert _get_closest_ansi_color(255, 255, 255) == 'ansiwhite'
    assert _get_closest_ansi_color(250, 250, 250) == 'ansiwhite'

    # Black
    assert _get_closest_ansi_color(0, 0, 0) == 'ansiblack'
    assert _get_closest_ansi_color(5, 5, 5) == 'ansiblack'

    # Green
    assert _get_closest_ansi_color(0, 255, 0) == 'ansibrightgreen'
    assert _get_closest_ansi_color(10, 255, 0) == 'ansibrightgreen'
    assert _get_closest_ansi_color(0, 255, 10) == 'ansibrightgreen'

    assert _get_closest_ansi_color(220, 220, 100) == 'ansiyellow'
