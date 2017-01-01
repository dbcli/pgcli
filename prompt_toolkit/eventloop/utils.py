from __future__ import unicode_literals
import time

__all__ = (
    'TimeIt',
    'AsyncioTimeout',
)


class TimeIt(object):
    """
    Context manager that times the duration of the code body.
    The `duration` attribute will contain the execution time in seconds.
    """
    def __init__(self):
        self.duration = None

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args):
        self.end = time.time()
        self.duration = self.end - self.start


class AsyncioTimeout(object):
    """
    Call the `timeout` function when the timeout expires.
    Every call of the `start` method, resets the timeout and starts a new
    timer.

    :param loop: The asyncio loop.
    """
    def __init__(self, timeout, callback, loop):
        from asyncio import BaseEventLoop
        assert isinstance(timeout, (float, int))
        assert callable(callback)
        assert isinstance(loop, BaseEventLoop)

        self.timeout = timeout
        self.callback = callback
        self.loop = loop

        self.counter = 0
        self.running = False

    def reset(self):
        """
        Reset the timeout. Starts a new timer.
        """
        self.running = True
        self.counter += 1
        local_counter = self.counter

        def timer_timeout():
            if self.counter == local_counter and self.running:
                self.callback()

        self.loop.call_later(self.timeout, timer_timeout)

    def stop(self):
        """
        Ignore timeout. Don't call the callback anymore.
        """
        self.running = False
