"""
Win32 asyncio event loop.

Windows notes:
- Somehow it doesn't seem to work with the 'ProactorEventLoop'.
"""
from __future__ import unicode_literals

from ..input import Input
from .utils import AsyncioTimeout
from .base import EventLoop, INPUT_TIMEOUT
from .future import Future
from .win32 import _wait_for_handles

import asyncio
import six
import textwrap

__all__ = (
    'Win32AsyncioEventLoop',
)


class Win32AsyncioEventLoop(EventLoop):
    def __init__(self, loop=None):
        self.loop = loop or asyncio.get_event_loop()
        self.closed = False

        self._input = None
        self._input_ready_cb = None

        self._timeout = AsyncioTimeout(
            INPUT_TIMEOUT, self._timeout_handler, self.loop)

    try:
        six.exec_(textwrap.dedent('''
    async def run_as_coroutine(self, future):
        " Run the loop. "
        assert isinstance(future, Future)
        if self.closed:
            raise Exception('Event loop already closed.')

        try:
            # Wait for input in a different thread.
            if self._input:
                def wait_for_input():
                    input_handle = self._input.handle
                    cb = self._input_ready_cb
                    while not future.done():
                        h = _wait_for_handles([input_handle], 1000)
                        if h == input_handle and not future.done():
                            cb()
                            self._timeout.reset()

                self.run_in_executor(wait_for_input)

            # Create a new asyncio Future that blocks this coroutine until the
            # prompt_toolkit Future is ready.
            stopped_f = loop.create_future()

            # Block this coroutine until stop() has been called.
            @future.add_done_callback
            def done(_):
                stopped_f.set_result(None)

            # Wait until f has been set.
            await stopped_f
        finally:
            # Don't trigger any timeout events anymore.
            self._timeout.stop()
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
            self._input = None
            self._input_ready_cb = None

    def run_in_executor(self, callback, _daemon=False):
        self.loop.run_in_executor(None, callback)

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
