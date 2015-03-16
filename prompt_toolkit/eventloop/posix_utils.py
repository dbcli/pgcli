from __future__ import unicode_literals

from codecs import getincrementaldecoder
import os

__all__ = (
    'PosixStdinReader',
)


class PosixStdinReader(object):
    """
    Wrapper around stdin which reads (nonblocking) the next available 1024
    bytes and decodes it.
    """
    def __init__(self, stdin):
        self.stdin = stdin

        # Create incremental decoder for decoding stdin.
        # We can not just do `os.read(stdin.fileno(), 1024).decode('utf-8')`, because
        # it could be that we are in the middle of a utf-8 byte sequence.
        self._stdin_decoder_cls = getincrementaldecoder('utf-8')
        self._stdin_decoder = self._stdin_decoder_cls()

    def read(self):
        """
        Read the input and return it as a string.
        """
        # Note: the following works better than wrapping `self.stdin` like
        #       `codecs.getreader('utf-8')(stdin)` and doing `read(1)`.
        #       Somehow that causes some latency when the escape
        #       character is pressed. (Especially on combination with the `select`.)
        try:
            data = os.read(self.stdin.fileno(), 1024)
        except OSError:
            # In case of SIGWINCH
            data = b''

        try:
            return self._stdin_decoder.decode(data)
        except UnicodeDecodeError:
            # When it's not possible to decode this bytes, reset the decoder.
            # The only occurence of this that I had was when using iTerm2 on OS
            # X, with "Option as Meta" checked (You should choose "Option as
            # +Esc".)
            self._stdin_decoder = self._stdin_decoder_cls()
            return ''
