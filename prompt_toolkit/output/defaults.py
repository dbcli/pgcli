from __future__ import unicode_literals
import os
import sys
from prompt_toolkit.utils import is_windows, is_conemu_ansi
from prompt_toolkit.filters import to_simple_filter
from six import PY2

__all__ = (
    'create_output',
)


def create_output(stdout=None, true_color=False, ansi_colors_only=None):
    """
    Return an :class:`~prompt_toolkit.output.Output` instance for the command
    line.

    :param true_color: When True, use 24bit colors instead of 256 colors.
        (`bool` or :class:`~prompt_toolkit.filters.SimpleFilter`.)
    :param ansi_colors_only: When True, restrict to 16 ANSI colors only.
        (`bool` or :class:`~prompt_toolkit.filters.SimpleFilter`.)
    """
    stdout = stdout or sys.__stdout__
    true_color = to_simple_filter(true_color)

    if is_windows():
        from .conemu import ConEmuOutput
        from .win32 import Win32Output
        from .windows10 import is_win_vt100_enabled, Windows10_Output

        if is_win_vt100_enabled():
            return Windows10_Output(stdout)
        if is_conemu_ansi():
            return ConEmuOutput(stdout)
        else:
            return Win32Output(stdout)
    else:
        from .vt100 import Vt100_Output
        term = os.environ.get('TERM', '')
        if PY2:
            term = term.decode('utf-8')

        return Vt100_Output.from_pty(
            stdout, true_color=true_color,
            ansi_colors_only=ansi_colors_only, term=term)
