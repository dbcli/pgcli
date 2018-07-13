from __future__ import unicode_literals
from prompt_toolkit.application.current import get_app
from prompt_toolkit.eventloop.context import TaskLocal, TaskLocalNotSetError
from prompt_toolkit.utils import is_windows
from .base import Input
import sys

__all__ = [
    'create_input',
    'create_pipe_input',
    'get_default_input',
    'set_default_input',
]


def create_input(stdin=None):
    stdin = stdin or sys.stdin

    if is_windows():
        from .win32 import Win32Input
        return Win32Input(stdin)
    else:
        from .vt100 import Vt100Input
        return Vt100Input(stdin)


def create_pipe_input():
    """
    Create an input pipe.
    This is mostly useful for unit testing.
    """
    if is_windows():
        from .win32_pipe import Win32PipeInput
        return Win32PipeInput()
    else:
        from .posix_pipe import PosixPipeInput
        return PosixPipeInput()


_default_input = TaskLocal()


def get_default_input():
    """
    Get the input class to be used by default.

    Called when creating a new Application(), when no `Input` has been passed.
    """
    # Other create/return the default input.
    try:
        value = _default_input.get()
    except TaskLocalNotSetError:
        # If an application is already running, take the input from there.
        # (This is important for the "ENTER for continue" prompts after
        # executing system commands and displaying readline-style completions.)
        app = get_app(return_none=True)
        if app:
            return app.input

        return create_input()
    else:
        return value


def set_default_input(input):
    """
    Set the default `Output` class.

    (Used for instance, for the telnet submodule.)
    """
    assert isinstance(input, Input)
    _default_input.set(input)
