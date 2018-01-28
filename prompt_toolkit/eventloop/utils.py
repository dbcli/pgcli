from __future__ import unicode_literals
import threading
from .future import Future
from .context import get_context_id, context

__all__ = [
    'ThreadWithFuture',
]


class ThreadWithFuture(object):
    """
    Wrapper around `Thread`.

    :param daemon: If `True`, start as daemon.
    """
    def __init__(self, target, daemon=False):
        self.target = target
        self.daemon = daemon
        self.future = Future()

        self._ctx_id = get_context_id()

    def start(self):
        """
        Start the thread, `self.future` will be set when the thread is done.
        """
        def run():
            # Mark this context (and thus `Application`) active in the current
            # thread.
            with context(self._ctx_id):
                try:
                    result = self.target()
                except BaseException as e:
                    self.future.set_exception(e)
                else:
                    self.future.set_result(result)

        t = threading.Thread(target=run)
        if self.daemon:
            t.daemon = True
        t.start()
