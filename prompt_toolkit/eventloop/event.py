"""
Asyncronous event implementation.
"""
from __future__ import unicode_literals
from .future import Future

__all__ = [
    'Event'
]


class Event(object):
    """
    Like `asyncio.event`.

    The state is intially false.
    """
    def __init__(self):
        self._state = False
        self._waiting_futures = []

    def is_set(self):
        return self._state

    def clear(self):
        self._state = False

    def set(self):
        self._state = True
        futures = self._waiting_futures
        self._waiting_futures = []

        for f in futures:
            f.set_result(None)

    def wait(self):
        if self._state:
            return Future.succeed(None)
        else:
            f = Future()
            self._waiting_futures.append(f)
            return f
