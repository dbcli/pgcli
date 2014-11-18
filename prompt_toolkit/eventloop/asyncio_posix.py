"""
Win32 asyncio event loop.

Windows notes:
- Somehow it doesn't seem to work with the 'ProactorEventLoop'.
"""
from __future__ import unicode_literals

from .asyncio_base import BaseAsyncioEventLoop
from ..terminal.vt100_input import InputStream

import os


__all__ = (
    'Win32AsyncioEventLoop',
)


class PosixAsyncioEventLoop(BaseAsyncioEventLoop):
    def __init__(self, input_processor, stdin, loop=None):
        super(PosixAsyncioEventLoop, self).__init__(input_processor, stdin)

        self._inputstream = InputStream(self.input_processor)

        # Create incremental decoder for decoding stdin.
        # We can not just do `os.read(stdin.fileno(), 1024).decode('utf-8')`, because
        # it could be that we are in the middle of a utf-8 byte sequence.
        self._stdin_decoder = self.stdin_decoder_cls()

    def wait_for_input(self, f_ready):
        def stdin_ready():
            data = self._read_from_stdin()
            self._inputstream.feed_and_flush(data)

            f_ready.set_result(None)  # Quit coroutine
            self.loop.remove_reader(self.stdin.fileno())

        self.loop.add_reader(self.stdin.fileno(), stdin_ready)

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
