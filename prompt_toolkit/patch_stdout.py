"""
patch_stdout
============

This implements a context manager that ensures that print statements within
it won't destroy the user interface. The context manager will replace
`sys.stdout` by something that draws the output above the current prompt,
rather than overwriting the UI.

Usage::

    with patch_stdout():
        ...
        application.run()
        ...

Multiple applications can run in the body of the context manager, one after the
other.
"""
from __future__ import unicode_literals
from .application import run_in_terminal
from .eventloop import get_event_loop

from contextlib import contextmanager
import threading
import sys

__all__ = [
    'patch_stdout',
    'StdoutProxy',
]


@contextmanager
def patch_stdout(raw=False):
    """
    Replace `sys.stdout` by an :class:`_StdoutProxy` instance.

    Writing to this proxy will make sure that the text appears above the
    prompt, and that it doesn't destroy the output from the renderer.  If no
    application is curring, the behaviour should be identical to writing to
    `sys.stdout` directly.

    :param raw: (`bool`) When True, vt100 terminal escape sequences are not
                removed/escaped.
    """
    proxy = StdoutProxy(raw=raw)

    original_stdout = sys.stdout
    original_stderr = sys.stderr

    # Enter.
    sys.stdout = proxy
    sys.stderr = proxy

    try:
        yield
    finally:
        # Exit.
        proxy.flush()

        sys.stdout = original_stdout
        sys.stderr = original_stderr


class StdoutProxy(object):
    """
    Proxy object for stdout which captures everything and prints output above
    the current application.
    """
    def __init__(self, raw=False, original_stdout=None):
        assert isinstance(raw, bool)
        original_stdout = original_stdout or sys.__stdout__

        self.original_stdout = original_stdout

        self._lock = threading.RLock()
        self._raw = raw
        self._buffer = []

        # errors/encoding attribute for compatibility with sys.__stdout__.
        self.errors = original_stdout.errors
        self.encoding = original_stdout.encoding

    def _write_and_flush(self, text):
        """
        Write the given text to stdout and flush.
        If an application is running, use `run_in_terminal`.
        """
        def write_and_flush():
            self.original_stdout.write(text)
            self.original_stdout.flush()

        def write_and_flush_in_loop():
            # If an application is running, use `run_in_terminal`, otherwise
            # call it directly.
            run_in_terminal(write_and_flush, in_executor=False)

        # Make sure `write_and_flush` is executed *in* the event loop, not in
        # another thread.
        get_event_loop().call_from_executor(write_and_flush_in_loop)

    def _write(self, data):
        """
        Note: print()-statements cause to multiple write calls.
              (write('line') and write('\n')). Of course we don't want to call
              `run_in_terminal` for every individual call, because that's too
              expensive, and as long as the newline hasn't been written, the
              text itself is again overwritten by the rendering of the input
              command line. Therefor, we have a little buffer which holds the
              text until a newline is written to stdout.
        """
        if '\n' in data:
            # When there is a newline in the data, write everything before the
            # newline, including the newline itself.
            before, after = data.rsplit('\n', 1)
            to_write = self._buffer + [before, '\n']
            self._buffer = [after]

            text = ''.join(to_write)
            self._write_and_flush(text)
        else:
            # Otherwise, cache in buffer.
            self._buffer.append(data)

    def _flush(self):
        text = ''.join(self._buffer)
        self._buffer = []
        self._write_and_flush(text)

    def write(self, data):
        with self._lock:
            self._write(data)

    def flush(self):
        """
        Flush buffered output.
        """
        with self._lock:
            self._flush()
