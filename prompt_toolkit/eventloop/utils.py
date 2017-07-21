from __future__ import unicode_literals
import threading
from .future import Future

__all__ = (
    'ThreadWithFuture',
)


class ThreadWithFuture(object):
    """
    Wrapper around `Thread`.

    :param daemon: If `True`, start as daemon.
    """
    def __init__(self, target, daemon=False):
        self.target = target
        self.daemon = daemon
        self.future = Future()

    def start(self):
        """
        Start the thread, `self.future` will be set when the thread is done.
        """
        def run():
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
