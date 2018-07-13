from .vt100 import Vt100Input
from ..utils import DummyContext
import os

__all__ = [
    'PosixPipeInput',
]


class PosixPipeInput(Vt100Input):
    """
    Input that is send through a pipe.
    This is useful if we want to send the input programmatically into the
    application. Mostly useful for unit testing.

    Usage::

        input = PosixPipeInput()
        input.send_text('inputdata')
    """
    _id = 0
    def __init__(self, text=''):
        self._r, self._w = os.pipe()

        class Stdin(object):
            def isatty(stdin):
                return True

            def fileno(stdin):
                return self._r

        super(PosixPipeInput, self).__init__(Stdin())
        self.send_text(text)

        # Identifier for every PipeInput for the hash.
        self.__class__._id += 1
        self._id = self.__class__._id

    @property
    def responds_to_cpr(self):
        return False

    def send_bytes(self, data):
        os.write(self._w, data)

    def send_text(self, data):
        " Send text to the input. "
        os.write(self._w, data.encode('utf-8'))

    def raw_mode(self):
        return DummyContext()

    def cooked_mode(self):
        return DummyContext()

    def close(self):
        " Close pipe fds. "
        os.close(self._r)
        os.close(self._w)

        # We should assign `None` to 'self._r` and 'self._w',
        # The event loop still needs to know the the fileno for this input in order
        # to properly remove it from the selectors.

    def typeahead_hash(self):
        """
        This needs to be unique for every `PipeInput`.
        """
        return 'pipe-input-%s' % (self._id, )
