"""
Abstraction of CLI Input.
"""
from __future__ import unicode_literals

from .utils import DummyContext, is_windows
from abc import ABCMeta, abstractmethod
from six import with_metaclass

import os
import sys

if is_windows():
    from .terminal.win32_input import raw_mode, cooked_mode
else:
    from .terminal.vt100_input import raw_mode, cooked_mode

__all__ = (
    'Input',
    'StdinInput',
    'PipeInput',
)


class Input(with_metaclass(ABCMeta, object)):
    """
    Abstraction for any CLI input.

    An instance of this class can be given to the constructor of a
    `CommandLineInterface` and will also be passed to the eventloop.
    """
    @abstractmethod
    def fileno(self):
        """
        Fileno for putting this in an event loop.
        """

    @abstractmethod
    def read(self):
        """
        Return text from the input.
        """

    @abstractmethod
    def raw_mode(self):
        """
        Context manager that turns the input into raw mode.
        """

    @abstractmethod
    def cooked_mode(self):
        """
        Context manager that turns the input into cooked mode.
        """


class StdinInput(Input):
    """
    Simple wrapper around stdin.
    """
    def __init__(self, stdin=None):
        self.stdin = stdin or sys.stdin

    def raw_mode(self):
        return raw_mode(self.stdin.fileno())

    def cooked_mode(self):
        return cooked_mode(self.stdin.fileno())

    def fileno(self):
        return self.stdin.fileno()

    def read(self):
        return self.stdin.read()


class PipeInput(Input):
    """
    Input that is send through a pipe.
    This is useful if we want to send the input programatically into the
    interface, but still use the eventloop.

    Usage::

        input = PipeInput()
        input.send('inputdata')
    """
    def __init__(self):
        self._r, self._w = os.pipe()

    def fileno(self):
        return self._r

    def read(self):
        return os.read(self._r)

    def send(self, data):
        os.write(self._w, data.encode('utf-8'))

    def raw_mode(self):
        return DummyContext()

    def cooked_mode(self):
        return DummyContext()
