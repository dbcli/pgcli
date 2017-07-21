"""
Posix asyncio event loop.
"""
from __future__ import unicode_literals

from ..input import Input
from .base import EventLoop
from .future import Future
from .utils import ThreadWithFuture
import asyncio

__all__ = (
    'PosixAsyncioEventLoop',
)


class PosixAsyncioEventLoop(EventLoop):
    """
    Wrapper around the Asyncio event loop, but compatible with prompt_toolkit.
    """
    def __init__(self, loop=None):
        super(PosixAsyncioEventLoop, self).__init__()

        self.loop = loop or asyncio.get_event_loop()
        self.closed = False

        self._input = None
        self._input_fd = None
        self._input_ready_cb = None

    def close(self):
        # Note: we should not close the asyncio loop itself, because that one
        # was not created here.
        self.closed = True

    def run_until_complete(self, future):
        return self.loop.run_until_complete(future)

    def run_in_executor(self, callback, _daemon=False):
        if _daemon:
            # Asyncio doesn't support 'daemon' executors.
            th = ThreadWithFuture(callback, daemon=True)
            self.call_from_executor(th.start)
            return th.future
        else:
            asyncio_f = self.loop.run_in_executor(None, callback)
            return Future.from_asyncio_future(asyncio_f, loop=self)

    def call_from_executor(self, callback, _max_postpone_until=None):
        """
        Call this function in the main event loop.
        Similar to Twisted's ``callFromThread``.
        """
        self.loop.call_soon_threadsafe(callback)

    def add_reader(self, fd, callback):
        " Start watching the file descriptor for read availability. "
        self.loop.add_reader(fd, callback)

    def remove_reader(self, fd):
        " Stop watching the file descriptor for read availability. "
        self.loop.remove_reader(fd)

    def add_signal_handler(self, signum, handler):
        return self.loop.add_signal_handler(signum, handler)

    def set_input(self, input, input_ready_callback):
        """
        Tell the eventloop to read from this input object.

        :param input: `Input` object.
        :param input_ready_callback: Called when the input is ready to read.
        """
        assert isinstance(input, Input)
        assert callable(input_ready_callback)

        # Remove previous
        previous_input, previous_cb = self.remove_input()

        # Set current.
        self._input = input
        self._input_ready_cb = input_ready_callback
        self._input_fd = input.fileno()

        # Add reader.
        def ready():
            # Tell the callback that input's ready.
            input_ready_callback()

        self.add_reader(self._input_fd, ready)

        return previous_input, previous_cb

    def remove_input(self):
        if self._input:
            previous_input = self._input
            previous_cb = self._input_ready_cb

            self.remove_reader(self._input_fd)
            self._input = None
            self._input_fd = None
            self._input_ready_cb = None

            return previous_input, previous_cb
        else:
            return None, None

    def get_exception_handler(self):
        return self.loop.get_exception_handler()

    def set_exception_handler(self, handler):
        self.loop.set_exception_handler(handler)

    def call_exception_handler(self, context):
        self.loop.call_exception_handler(context)

    def default_exception_handler(self, context):
        self.loop.default_exception_handler(context)
