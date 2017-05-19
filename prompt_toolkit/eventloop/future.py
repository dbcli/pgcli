"""
Future implementation for the prompt_toolkit eventloop.
"""
from __future__ import unicode_literals
from .base import EventLoop
from .defaults import get_event_loop

__all__ = (
    'Future',
    'InvalidStateError',
)


class InvalidStateError(Exception):
    " The operation is not allowed in this state. "


class Future(object):
    """
    `Future` object for use with the prompt_toolkit event loops.  (Not by
    accident very similar to asyncio -- but much more limited in functionality.
    They are however not meant to be used interchangeable.)
    """
    def __init__(self, loop=None):
        assert loop is None or isinstance(loop, EventLoop)
        self.loop = loop or get_event_loop()
        self.done_callbacks = []
        self._result = None
        self._exception = None
        self._done = False

    def add_done_callback(self, callback):
        """
        Add a callback to be run when the future becomes done.  (This
        callback will be called with one argument only: this future
        object.)
        """
        self.done_callbacks.append(callback)

    def set_result(self, result):
        " Mark the future done and set its result. "
        self._result = result
        self._done = True
        self._call_callbacks()

    def set_exception(self, exception):
        " Mark the future done and set an exception. "
        self._exception = exception
        self._done = True
        self._call_callbacks()

    def _call_callbacks(self):
        def call_them_all():
            # They should be called in order.
            for cb in self.done_callbacks:
                cb(self)

        self.loop.call_from_executor(call_them_all)

    def result(self):
        " Return the result this future represents. "
        if not self._done:
            raise InvalidStateError

        if self._exception:
            raise self._exception
        else:
            return self._result

    def exception(self):
        " Return the exception that was set on this future. "
        if self._done:
            return self._exception
        else:
            raise InvalidStateError

    def done(self):
        """
        Return True if the future is done. Done means either that a result /
        exception are available, or that the future was cancelled.
        """
        return self._done
