"""
Win32 asyncio event loop.

Windows notes:
- Somehow it doesn't seem to work with the 'ProactorEventLoop'.
"""
from __future__ import unicode_literals

from .base import EventLoop
from .context import wrap_in_current_context
from .future import Future
from .utils import ThreadWithFuture
from .win32 import wait_for_handles

import asyncio

__all__ = [
    'Win32AsyncioEventLoop',
]


class Win32AsyncioEventLoop(EventLoop):
    """
    Wrapper around the Asyncio event loop, but compatible with prompt_toolkit.
    """
    def __init__(self, loop=None):
        super(Win32AsyncioEventLoop, self).__init__()

        self.loop = loop or asyncio.get_event_loop()
        self.closed = False

        # Maps win32 handles to their callbacks.
        self._handle_callbacks = {}

    def close(self):
        # Note: we should not close the asyncio loop itself, because that one
        # was not created here.
        self.closed = True

    def run_until_complete(self, future, inputhook=None):
        if inputhook:
            raise ValueError("Win32AsyncioEventLoop doesn't support input hooks.")

        return self.loop.run_until_complete(future)

    def run_forever(self, inputhook=None):
        if inputhook:
            raise ValueError("Win32AsyncioEventLoop doesn't support input hooks.")

        self.loop.run_forever()

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
        callback = wrap_in_current_context(callback)
        self.loop.call_soon_threadsafe(callback)

    def add_reader(self, fd, callback):
        " Start watching the file descriptor for read availability. "
        callback = wrap_in_current_context(callback)
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

    def add_win32_handle(self, handle, callback):
        " Add a Win32 handle to the event loop. "
        callback = wrap_in_current_context(callback)
        self._handle_callbacks[handle] = callback

        # Add reader.
        def ready():
            # Tell the callback that input's ready.
            try:
                callback()
            finally:
                self.run_in_executor(wait)

        # Wait for the input to become ready.
        # (Use an executor for this, the Windows asyncio event loop doesn't
        # allow us to wait for handles like stdin.)
        def wait():
            if self._handle_callbacks.get(handle) != callback:
                return

            wait_for_handles([handle])
            self.call_from_executor(ready)

        self.run_in_executor(wait, _daemon=True)

    def remove_win32_handle(self, handle):
        " Remove a Win32 handle from the event loop. "
        if handle in self._handle_callbacks:
            del self._handle_callbacks[handle]
