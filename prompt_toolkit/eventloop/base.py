"""
Base event loop interface.

The naming convension is kept similar to asyncio as much as possible.

A special thanks to asyncio (tulip), Twisted, Tornado and Trollius for setting
a good example on how to implement event loops. Possible, in the future, we'll
run entirely on top of asyncio, but right now, we're still supporting Python 2.
"""
from __future__ import unicode_literals
from abc import ABCMeta, abstractmethod
from six import with_metaclass
from prompt_toolkit.log import logger

__all__ = (
    'EventLoop',
)


class EventLoop(with_metaclass(ABCMeta, object)):
    """
    Eventloop interface.
    """
    def __init__(self):
        self._exception_handler = None

    def run_until_complete(self, future):
        """
        Keep running until this future has been set.
        Return the Future's result, or raise its exception.
        """
        raise NotImplementedError(
            "This eventloop doesn't implement synchronous 'run_until_complete()'.")

    @abstractmethod
    def close(self):
        """
        Clean up of resources. Eventloop cannot be reused a second time after
        this call.
        """

    @abstractmethod
    def add_reader(self, fd, callback):
        """
        Start watching the file descriptor for read availability and then call
        the callback.
        """

    @abstractmethod
    def remove_reader(self, fd):
        """
        Stop watching the file descriptor for read availability.
        """

    @abstractmethod
    def set_input(self, input, input_ready_callback):
        """
        Tell the eventloop to read from this input object.

        :param input: :class:`~prompt_toolkit.input.Input` object.
        :param input_ready_callback: Called when the input is ready to read.
        """

    @abstractmethod
    def remove_input(self):
        """
        Remove the currently attached `Input`.

        Return the previous (input, input_ready_callback) tuple.
        This can be (None, None).
        """

    @abstractmethod
    def run_in_executor(self, callback, _daemon=False):
        """
        Run a long running function in a background thread. (This is
        recommended for code that could block the event loop.)
        Similar to Twisted's ``deferToThread``.
        """

    @abstractmethod
    def call_from_executor(self, callback, _max_postpone_until=None):
        """
        Call this function in the main event loop. Similar to Twisted's
        ``callFromThread``.

        :param _max_postpone_until: `None` or `time.time` value. For interal
            use. If the eventloop is saturated, consider this task to be low
            priority and postpone maximum until this timestamp. (For instance,
            repaint is done using low priority.)

            Note: In the past, this used to be a datetime.datetime instance,
                  but apparently, executing `time.time` is more efficient: it
                  does fewer system calls. (It doesn't read /etc/localtime.)
        """

    def create_future(self):
        """
        Create a `Future` object that is attached to this loop.
        This is the preferred way of creating futures.
        """
        from .future import Future
        return Future(loop=self)

    def set_exception_handler(self, handler):
        """
        Set the exception handler.
        """
        assert handler is None or callable(handler)
        self._exception_handler = handler

    def get_exception_handler(self):
        """
        Return the exception handler.
        """
        return self._exception_handler

    def call_exception_handler(self, context):
        """
        Call the current event loop exception handler.
        (Similar to ``asyncio.BaseEventLoop.call_exception_handler``.)
        """
        if self._exception_handler:
            try:
                self._exception_handler(context)
            except Exception:
                 logger.error('Exception in default exception handler',
                              exc_info=True)
        else:
            try:
                self.default_exception_handler(context)
            except Exception:
                logger.error('Exception in default exception handler '
                             'while handling an unexpected error '
                             'in custom exception handler',
                             exc_info=True)

    def default_exception_handler(self, context):
        """
        Default exception handling.

        Thanks to asyncio for this function!
        """
        message = context.get('message')
        if not message:
            message = 'Unhandled exception in event loop'

        exception = context.get('exception')
        if exception is not None:
            exc_info = (type(exception), exception, exception.__traceback__)
        else:
            exc_info = False

        log_lines = [message]
        for key in sorted(context):
            if key in ('message', 'exception'):
                continue
            value = context[key]
            value = repr(value)
            log_lines.append('{}: {}'.format(key, value))

        logger.error('\n'.join(log_lines), exc_info=exc_info)
