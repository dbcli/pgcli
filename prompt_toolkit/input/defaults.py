from __future__ import unicode_literals
from prompt_toolkit.utils import is_windows
from prompt_toolkit.eventloop.context import TaskLocal, TaskLocalNotSetError
from .base import Input
import sys

__all__ = (
    'create_input',
    'get_default_input',
    'set_default_input',
)


def create_input(stdin=None):
    stdin = stdin or sys.stdin

    if is_windows():
        from .win32 import Win32Input
        return Win32Input(stdin)
    else:
        from .vt100 import Vt100Input
        return Vt100Input(stdin)


_default_input = TaskLocal()


def get_default_input():
    """
    Get the input class to be used by default.

    Called when creating a new Application(), when no `Input` has been passed.
    """
    try:
        value = _default_input.get()
    except TaskLocalNotSetError:
        return create_input()
    else:
        return value


def set_default_input(input):
    """
    Set the default `Output` class.
    """
    assert isinstance(input, Input)
    _default_input.set(input)
