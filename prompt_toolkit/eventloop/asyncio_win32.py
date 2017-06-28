"""
Win32 asyncio event loop.

Windows notes:
- Somehow it doesn't seem to work with the 'ProactorEventLoop'.
"""
from __future__ import unicode_literals

from ..input import Input
from .base import EventLoop
from .future import Future

import asyncio

__all__ = (
    'Win32AsyncioEventLoop',
)


class Win32AsyncioEventLoop(EventLoop):
    """
    Wrapper around the Asyncio event loop, but compatible with prompt_toolkit.
    """
    def __init__(self, loop=None):
        super(Win32AsyncioEventLoop, self).__init__()

        self.loop = loop or asyncio.get_event_loop()
        self.closed = False

        self._input = None
        self._input_ready_cb = None

    def close(self):
        # Note: we should not close the asyncio loop itself, because that one
        # was not created here.
        self.closed = True

    def set_input(self, input, input_ready_callback):
        """
        Tell the eventloop to read from this input object.

        :param input: `Input` object.
        :param input_ready_callback: Called when the input is ready to read.
        """
        assert isinstance(input, Input)
        assert callable(input_ready_callback)

        # Remove previous
        if self._input:
            previous_input = self._input
            previous_cb = self._input_ready_cb
            self.remove_input()
        else:
            previous_input = None
            previous_cb = None

        # Set current.
        self._input = input
        self._input_ready_cb = input_ready_callback

        return previous_input, previous_cb

    def remove_input(self):
        if self._input:
            previous_input = self._input
            previous_cb = self._input_ready_cb

            self._input = None
            self._input_ready_cb = None

            return previous_input, previous_cb
        else:
            return None, None

    def run_in_executor(self, callback, _daemon=False):
        asyncio_f = self.loop.run_in_executor(None, callback)
        return Future.from_asyncio_future(asyncio_f, loop=self)

    def call_from_executor(self, callback, _max_postpone_until=None):
        self.loop.call_soon_threadsafe(callback)

    def add_reader(self, fd, callback):
        " Start watching the file descriptor for read availability. "
        self.loop.add_reader(fd, callback)

    def remove_reader(self, fd):
        " Stop watching the file descriptor for read availability. "
        self.loop.remove_reader(fd)

    def add_signal_handler(self, signum, handler):
        return self.loop.add_signal_handler(signum, handler)

    def get_exception_handler(self):
        return self.loop.get_exception_handler()

    def set_exception_handler(self, handler):
        self.loop.set_exception_handler(handler)

    def call_exception_handler(self, context):
        self.loop.call_exception_handler(context)

    def default_exception_handler(self, context):
        self.loop.default_exception_handler(context)
