"""
Posix asyncio event loop.
"""
from __future__ import unicode_literals

from ..input import Input
from .base import EventLoop
from .future import Future
import asyncio
import six
import textwrap

__all__ = (
    'PosixAsyncioEventLoop',
)


class PosixAsyncioEventLoop(EventLoop):
    def __init__(self, loop=None):
        self.loop = loop or asyncio.get_event_loop()
        self.closed = False

        self._input = None
        self._input_ready_cb = None

    try:
        six.exec_(textwrap.dedent('''
    async def run_as_coroutine(self, future):
        " Run the loop. "
        assert isinstance(future, Future)
        if self.closed:
            raise Exception('Event loop already closed.')

        # Create a new asyncio Future that blocks this coroutine until the
        # prompt_toolkit Future is ready.
        stopped_f = self.loop.create_future()

        # Block this coroutine until stop() has been called.
        @future.add_done_callback
        def done(_):
            stopped_f.set_result(None)

        # Wait until f has been set.
        await stopped_f
    '''), globals(), locals())
    except SyntaxError:
        def run_as_coroutine(self, future):
            " Run the loop. "
            assert isinstance(future, Future)
            raise NotImplementedError('`run_as_coroutine` requires at least Python 3.5.')

    def close(self):
        # Note: we should not close the asyncio loop itself, because that one
        # was not created here.
        self.closed = True

    def _timeout_handler(self):
        """
        When no input has been received for INPUT_TIMEOUT seconds,
        flush the input stream and fire the timeout event.
        """
        if self._input is not None:
            self._input.flush()

    def run_in_executor(self, callback, _daemon=False):
        self.loop.run_in_executor(None, callback)

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

        # Add reader.
        def ready():
            # Tell the callback that input's ready.
            input_ready_callback()

        self.add_reader(input.stdin.fileno(), ready)

        return previous_input, previous_cb

    def remove_input(self):
        if self._input:
            self.remove_reader(self._input.fileno())
            self._input = None
            self._input_ready_cb = None

