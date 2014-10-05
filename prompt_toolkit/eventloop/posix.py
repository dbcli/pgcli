from __future__ import unicode_literals
import os
import fcntl
import select
import signal
import errno

from codecs import getincrementaldecoder
from ..terminal.vt100_input import InputStream

from .base import BaseEventLoop

__all__ = (
    'PosixEventLoop',
    'call_on_sigwinch',
)


class PosixEventLoop(BaseEventLoop):
    stdin_decoder_cls = getincrementaldecoder('utf-8')

    def __init__(self, input_processor, stdin):
        super(PosixEventLoop, self).__init__(input_processor, stdin)

        self.inputstream = InputStream(self.input_processor)

        # Create a pipe for inter thread communication.
        self._schedule_pipe = os.pipe()
        fcntl.fcntl(self._schedule_pipe[0], fcntl.F_SETFL, os.O_NONBLOCK)

        # Create incremental decoder for decoding stdin.
        # We can not just do `os.read(stdin.fileno(), 1024).decode('utf-8')`, because
        # it could be that we are in the middle of a utf-8 byte sequence.
        self._stdin_decoder = self.stdin_decoder_cls()

    def loop(self):
        """
        The input 'event loop'.
        """
        if self.closed:
            raise Exception('Event loop already closed.')

        timeout = self.input_timeout

        while True:
            r, w, x = _select([self.stdin, self._schedule_pipe[0]], [], [], timeout)

            # If we got a character, feed it to the input stream. If we got
            # none, it means we got a repaint request.
            if self.stdin in r:
                c = self._read_from_stdin()

                if c:
                    # Feed input text.
                    self.inputstream.feed(c)

                    # Immediately flush the input.
                    self.inputstream.flush()

                return

            # If we receive something on our "call_from_executor" pipe, process
            # these callbacks in a thread safe way.
            elif self._schedule_pipe[0] in r:
                # Flush all the pipe content.
                os.read(self._schedule_pipe[0], 1024)

                # Process calls from executor.
                calls_from_executor, self._calls_from_executor = self._calls_from_executor, []
                for c in calls_from_executor:
                    c()
            else:
                # Fire input timeout event.
                self.onInputTimeout.fire()
                timeout = None

    def _read_from_stdin(self):
        """
        Read the input and return it.
        """
        # Note: the following works better than wrapping `self.stdin` like
        #       `codecs.getreader('utf-8')(stdin)` and doing `read(1)`.
        #       Somehow that causes some latency when the escape
        #       character is pressed. (Especially on combination with the `select`.
        try:
            bytes = os.read(self.stdin.fileno(), 1024)
        except OSError:
            # In case of SIGWINCH
            bytes = b''

        try:
            return self._stdin_decoder.decode(bytes)
        except UnicodeDecodeError:
            # When it's not possible to decode this bytes, reset the decoder.
            # The only occurence of this that I had was when using iTerm2 on OS
            # X, with "Option as Meta" checked (You should choose "Option as
            # +Esc".)
            self._stdin_decoder = self.stdin_decoder_cls()
            return ''

    def call_from_executor(self, callback):
        """
        Call this function in the main event loop.
        Similar to Twisted's ``callFromThread``.
        """
        self._calls_from_executor.append(callback)

        if self._schedule_pipe:
            os.write(self._schedule_pipe[1], b'x')

    def close(self):
        super(PosixEventLoop, self).close()

        # Close pipes.
        schedule_pipe = self._schedule_pipe
        self._schedule_pipe = None

        if schedule_pipe:
            os.close(schedule_pipe[0])
            os.close(schedule_pipe[1])


def _select(*args, **kwargs):
    """
    Wrapper around select.select.

    When the SIGWINCH signal is handled, other system calls, like select
    are aborted in Python. This wrapper will retry the system call.
    """
    while True:
        try:
            return select.select(*args, **kwargs)
        except select.error as e:
            # Retry select call when EINTR
            if e.args and e.args[0] == errno.EINTR:
                continue
            else:
                raise


class call_on_sigwinch(object):
    """
    Context manager which Installs a SIGWINCH callback.
    (This signal occurs when the terminal size changes.)
    """
    def __init__(self, callback):
        self.callback = callback

    def __enter__(self):
        self.previous_callback = signal.signal(signal.SIGWINCH, lambda *a: self.callback())

    def __exit__(self, *a, **kw):
        signal.signal(signal.SIGWINCH, self.previous_callback)
