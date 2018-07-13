from __future__ import unicode_literals

from ..eventloop import get_event_loop
from .base import Input
from .posix_utils import PosixStdinReader
from .vt100_parser import Vt100Parser
import io
import os
import sys
import termios
import tty
import contextlib

__all__ = [
    'Vt100Input',
    'raw_mode',
    'cooked_mode',
]


class Vt100Input(Input):
    """
    Vt100 input for Posix systems.
    (This uses a posix file descriptor that can be registered in the event loop.)
    """
    def __init__(self, stdin):
        # The input object should be a TTY.
        assert stdin.isatty()

        # Test whether the given input object has a file descriptor.
        # (Idle reports stdin to be a TTY, but fileno() is not implemented.)
        try:
            # This should not raise, but can return 0.
            stdin.fileno()
        except io.UnsupportedOperation:
            if 'idlelib.run' in sys.modules:
                raise io.UnsupportedOperation(
                    'Stdin is not a terminal. Running from Idle is not supported.')
            else:
                raise io.UnsupportedOperation('Stdin is not a terminal.')

        self.stdin = stdin

        # Create a backup of the fileno(). We want this to work even if the
        # underlying file is closed, so that `typeahead_hash()` keeps working.
        self._fileno = stdin.fileno()

        self._buffer = []  # Buffer to collect the Key objects.
        self.stdin_reader = PosixStdinReader(self._fileno)
        self.vt100_parser = Vt100Parser(
            lambda key: self._buffer.append(key))

    @property
    def responds_to_cpr(self):
        return True

    def attach(self, input_ready_callback):
        """
        Return a context manager that makes this input active in the current
        event loop.
        """
        assert callable(input_ready_callback)
        return _attached_input(self, input_ready_callback)

    def detach(self):
        """
        Return a context manager that makes sure that this input is not active
        in the current event loop.
        """
        return _detached_input(self)

    def read_keys(self):
        " Read list of KeyPress. "
        # Read text from stdin.
        data = self.stdin_reader.read()

        # Pass it through our vt100 parser.
        self.vt100_parser.feed(data)

        # Return result.
        result = self._buffer
        self._buffer = []
        return result

    def flush_keys(self):
        """
        Flush pending keys and return them.
        (Used for flushing the 'escape' key.)
        """
        # Flush all pending keys. (This is most important to flush the vt100
        # 'Escape' key early when nothing else follows.)
        self.vt100_parser.flush()

        # Return result.
        result = self._buffer
        self._buffer = []
        return result

    @property
    def closed(self):
        return self.stdin_reader.closed

    def raw_mode(self):
        return raw_mode(self.stdin.fileno())

    def cooked_mode(self):
        return cooked_mode(self.stdin.fileno())

    def fileno(self):
        return self.stdin.fileno()

    def typeahead_hash(self):
        return 'fd-%s' % (self._fileno, )


_current_callbacks = {}  # (loop, fd) -> current callback


@contextlib.contextmanager
def _attached_input(input, callback):
    """
    Context manager that makes this input active in the current event loop.

    :param input: :class:`~prompt_toolkit.input.Input` object.
    :param callback: Called when the input is ready to read.
    """
    loop = get_event_loop()
    fd = input.fileno()
    previous = _current_callbacks.get((loop, fd))

    loop.add_reader(fd, callback)
    _current_callbacks[loop, fd] = callback

    try:
        yield
    finally:
        loop.remove_reader(fd)

        if previous:
            loop.add_reader(fd, previous)
            _current_callbacks[loop, fd] = previous
        else:
            del _current_callbacks[loop, fd]


@contextlib.contextmanager
def _detached_input(input):
    loop = get_event_loop()
    fd = input.fileno()
    previous = _current_callbacks.get((loop, fd))

    if previous:
        loop.remove_reader(fd)
        _current_callbacks[loop, fd] = None

    try:
        yield
    finally:
        if previous:
            loop.add_reader(fd, previous)
            _current_callbacks[loop, fd] = previous


class raw_mode(object):
    """
    ::

        with raw_mode(stdin):
            ''' the pseudo-terminal stdin is now used in raw mode '''

    We ignore errors when executing `tcgetattr` fails.
    """
    # There are several reasons for ignoring errors:
    # 1. To avoid the "Inappropriate ioctl for device" crash if somebody would
    #    execute this code (In a Python REPL, for instance):
    #
    #         import os; f = open(os.devnull); os.dup2(f.fileno(), 0)
    #
    #    The result is that the eventloop will stop correctly, because it has
    #    to logic to quit when stdin is closed. However, we should not fail at
    #    this point. See:
    #      https://github.com/jonathanslenders/python-prompt-toolkit/pull/393
    #      https://github.com/jonathanslenders/python-prompt-toolkit/issues/392

    # 2. Related, when stdin is an SSH pipe, and no full terminal was allocated.
    #    See: https://github.com/jonathanslenders/python-prompt-toolkit/pull/165
    def __init__(self, fileno):
        self.fileno = fileno
        try:
            self.attrs_before = termios.tcgetattr(fileno)
        except termios.error:
            # Ignore attribute errors.
            self.attrs_before = None

    def __enter__(self):
        # NOTE: On os X systems, using pty.setraw() fails. Therefor we are using this:
        try:
            newattr = termios.tcgetattr(self.fileno)
        except termios.error:
            pass
        else:
            newattr[tty.LFLAG] = self._patch_lflag(newattr[tty.LFLAG])
            newattr[tty.IFLAG] = self._patch_iflag(newattr[tty.IFLAG])

            # VMIN defines the number of characters read at a time in
            # non-canonical mode. It seems to default to 1 on Linux, but on
            # Solaris and derived operating systems it defaults to 4. (This is
            # because the VMIN slot is the same as the VEOF slot, which
            # defaults to ASCII EOT = Ctrl-D = 4.)
            newattr[tty.CC][termios.VMIN] = 1

            termios.tcsetattr(self.fileno, termios.TCSANOW, newattr)

            # Put the terminal in cursor mode. (Instead of application mode.)
            os.write(self.fileno, b'\x1b[?1l')

    @classmethod
    def _patch_lflag(cls, attrs):
        return attrs & ~(termios.ECHO | termios.ICANON | termios.IEXTEN | termios.ISIG)

    @classmethod
    def _patch_iflag(cls, attrs):
        return attrs & ~(
            # Disable XON/XOFF flow control on output and input.
            # (Don't capture Ctrl-S and Ctrl-Q.)
            # Like executing: "stty -ixon."
            termios.IXON | termios.IXOFF |

            # Don't translate carriage return into newline on input.
            termios.ICRNL | termios.INLCR | termios.IGNCR
        )

    def __exit__(self, *a, **kw):
        if self.attrs_before is not None:
            try:
                termios.tcsetattr(self.fileno, termios.TCSANOW, self.attrs_before)
            except termios.error:
                pass

            # # Put the terminal in application mode.
            # self._stdout.write('\x1b[?1h')


class cooked_mode(raw_mode):
    """
    The opposite of ``raw_mode``, used when we need cooked mode inside a
    `raw_mode` block.  Used in `Application.run_in_terminal`.::

        with cooked_mode(stdin):
            ''' the pseudo-terminal stdin is now used in cooked mode. '''
    """
    @classmethod
    def _patch_lflag(cls, attrs):
        return attrs | (termios.ECHO | termios.ICANON | termios.IEXTEN | termios.ISIG)

    @classmethod
    def _patch_iflag(cls, attrs):
        # Turn the ICRNL flag back on. (Without this, calling `input()` in
        # run_in_terminal doesn't work and displays ^M instead. Ptpython
        # evaluates commands using `run_in_terminal`, so it's important that
        # they translate ^M back into ^J.)
        return attrs | termios.ICRNL
