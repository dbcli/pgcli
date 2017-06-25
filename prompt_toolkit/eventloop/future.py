"""
Future implementation for the prompt_toolkit eventloop.
"""
from __future__ import unicode_literals, print_function
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

    @classmethod
    def succeed(cls, result):
        """
        Returns a Future for which the result has been set to the given result.
        Similar to Twisted's `Deferred.succeed()`.
        """
        f = cls()
        f.set_result(result)
        return f

    @classmethod
    def fail(cls, result):
        """
        Returns a Future for which the error has been set to the given result.
        Similar to Twisted's `Deferred.fail()`.
        """
        f = cls()
        f.set_exception(result)
        return f

    def add_done_callback(self, callback):
        """
        Add a callback to be run when the future becomes done.  (This
        callback will be called with one argument only: this future
        object.)
        """
        self.done_callbacks.append(callback)

        # When a result has already been set. Call callback right away.
        if self._done:
            def call_cb():
                callback(self)

            self.loop.call_from_executor(call_cb)

    def set_result(self, result):
        " Mark the future done and set its result. "
        if self._result:
            raise InvalidStateError('Future result has been set already.')

        self._result = result
        self._done = True
        self._call_callbacks()

    def set_exception(self, exception):
        " Mark the future done and set an exception. "
        self._exception = exception
        self._done = True

        if self.done_callbacks:
            self._call_callbacks()
        else:
            # When an exception is set on a 'Future' object, but there
            # is no callback set to handle it, print the exception.
            # -- Uncomment for debugging. --

            #import traceback, sys
            #print(''.join(traceback.format_stack()), file=sys.__stderr__)
            #print('Uncollected error: %r' % (exception, ), file=sys.__stderr__)
            pass

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

    def to_asyncio_future(self):
        """
        Turn this `Future` into an asyncio `Future` object.
        """
        from asyncio import Future
        asyncio_f = Future()

        @self.add_done_callback
        def _(f):
            if f.exception():
                asyncio_f.set_exception(f.exception())
            else:
                asyncio_f.set_result(f.result())

        return asyncio_f

    @classmethod
    def from_asyncio_future(cls, asyncio_f, loop=None):
        """
        Return a prompt_toolkit `Future` from the given asyncio Future.
        """
        f = cls(loop=loop)

        @asyncio_f.add_done_callback
        def _(asyncio_f):
            if asyncio_f.exception():
                f.set_exception(asyncio_f.exception())
            else:
                f.set_result(asyncio_f.result())

        return f
