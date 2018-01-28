from __future__ import unicode_literals
from prompt_toolkit.utils import is_windows
from .base import EventLoop
import threading

__all__ = [
    'create_event_loop',
    'create_asyncio_event_loop',
    'use_asyncio_event_loop',
    'get_event_loop',
    'set_event_loop',
    'run_in_executor',
    'call_from_executor',
    'run_until_complete',
]


def create_event_loop(recognize_win32_paste=True):
    """
    Create and return an
    :class:`~prompt_toolkit.eventloop.base.EventLoop` instance.
    """
    if is_windows():
        from .win32 import Win32EventLoop
        return Win32EventLoop(recognize_paste=recognize_win32_paste)
    else:
        from .posix import PosixEventLoop
        return PosixEventLoop()


def _get_asyncio_loop_cls():
    # Inline import, to make sure the rest doesn't break on Python 2. (Where
    # asyncio is not available.)
    if is_windows():
        from prompt_toolkit.eventloop.asyncio_win32 import Win32AsyncioEventLoop as AsyncioEventLoop
    else:
        from prompt_toolkit.eventloop.asyncio_posix import PosixAsyncioEventLoop as AsyncioEventLoop
    return AsyncioEventLoop


def create_asyncio_event_loop(loop=None):
    """
    Returns an asyncio :class:`~prompt_toolkit.eventloop.EventLoop` instance
    for usage in a :class:`~prompt_toolkit.application.Application`. It is a
    wrapper around an asyncio loop.

    :param loop: The asyncio eventloop (or `None` if the default asyncioloop
                 should be used.)
    """
    AsyncioEventLoop = _get_asyncio_loop_cls()
    return AsyncioEventLoop(loop)


def use_asyncio_event_loop(loop=None):
    """
    Use the asyncio event loop for prompt_toolkit applications.
    """
    # Don't create a new loop if the current one uses asyncio already.
    current_loop = get_event_loop()
    if current_loop and isinstance(current_loop, _get_asyncio_loop_cls()):
        return

    set_event_loop(create_asyncio_event_loop(loop))


_loop = None
_loop_lock = threading.RLock()


def get_event_loop():
    """
    Return the current event loop.
    This will create a new loop if no loop was set yet.
    """
    # When this function is called for the first time, and no loop has been
    # set: create one.
    global _loop

    with _loop_lock:
        # The following two lines are not atomic. I ended up in a situation
        # where two threads were calling `get_event_loop()` at the same time,
        # and that way we had two event loop instances. On one of the
        # instances, `call_from_executor` was called, but never executed
        # because that loop was not running.
        if _loop is None:
            _loop = create_event_loop()

        return _loop


def set_event_loop(loop):
    """
    Set the current event loop.

    :param loop: `EventLoop` instance or None. (Pass `None` to clear the
        current loop.)
    """
    assert loop is None or isinstance(loop, EventLoop)
    global _loop
    _loop = loop


def run_in_executor(callback, _daemon=False):
    """
    Run a long running function in a background thread.
    """
    return get_event_loop().run_in_executor(callback, _daemon=_daemon)


def call_from_executor(callback, _max_postpone_until=None):
    """
    Call this function in the main event loop.
    """
    return get_event_loop().call_from_executor(
        callback, _max_postpone_until=_max_postpone_until)


def run_until_complete(future, inputhook=None):
    """
    Keep running until this future has been set.
    Return the Future's result, or raise its exception.
    """
    return get_event_loop().run_until_complete(future, inputhook=inputhook)
