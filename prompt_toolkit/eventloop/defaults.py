from __future__ import unicode_literals
from prompt_toolkit.utils import is_windows
from .base import EventLoop

__all__ = (
    'create_event_loop',
    'create_asyncio_event_loop',
    'get_event_loop',
    'set_event_loop',
)


def create_event_loop(inputhook=None, recognize_win32_paste=True):
    """
    Create and return an
    :class:`~prompt_toolkit.eventloop.base.EventLoop` instance.
    """
    if is_windows():
        from .win32 import Win32EventLoop
        return Win32EventLoop(inputhook=inputhook, recognize_paste=recognize_win32_paste)
    else:
        from .posix import PosixEventLoop
        return PosixEventLoop(inputhook=inputhook)


def create_asyncio_event_loop(loop=None):
    """
    Returns an asyncio :class:`~prompt_toolkit.eventloop.EventLoop` instance
    for usage in a :class:`~prompt_toolkit.application.Application`. It is a
    wrapper around an asyncio loop.

    :param loop: The asyncio eventloop (or `None` if the default asyncioloop
                 should be used.)
    """
    # Inline import, to make sure the rest doesn't break on Python 2. (Where
    # asyncio is not available.)
    if is_windows():
        from prompt_toolkit.eventloop.asyncio_win32 import Win32AsyncioEventLoop as AsyncioEventLoop
    else:
        from prompt_toolkit.eventloop.asyncio_posix import PosixAsyncioEventLoop as AsyncioEventLoop

    return AsyncioEventLoop(loop)


_loop = None
_loop_has_been_set = False


def get_event_loop():
    """
    Return the current event loop.
    This has to be called after setting an event loop, using `set_event_loop`.
    (Unline Asyncio, we don't set a default loop.)
    """
    global _loop, _loop_has_been_set

    # When this function is called for the first time, and no loop has been
    # set. Create one.
    if _loop is None and not _loop_has_been_set:
        _loop = create_event_loop()
        _loop_has_been_set = True

    if _loop is not None:
        return _loop
    else:
        raise ValueError('The event loop has been cleared. Passing the explicitely is required.')


def set_event_loop(loop):
    """
    Set the current event loop.

    :param loop: `EventLoop` instance or None. (Pass `None` to clear the
        current loop.)
    """
    assert loop is None or isinstance(loop, EventLoop)
    global _loop, _loop_has_been_set

    _loop = loop
    _loop_has_been_set = True
