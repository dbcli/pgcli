from __future__ import unicode_literals
import array
import fcntl
import signal
import six
import termios
import tty


def get_size(fileno):
    # Thanks to fabric (fabfile.org), and
    # http://sqizit.bartletts.id.au/2011/02/14/pseudo-terminals-in-python/
    """
    Get the size of this pseudo terminal.

    :param fileno: stdout.fileno()
    :returns: A (rows, cols) tuple.
    """
#    assert stdout.isatty()

    # Buffer for the C call
    buf = array.array(u'h' if six.PY3 else b'h', [0, 0, 0, 0])

    # Do TIOCGWINSZ (Get)
    fcntl.ioctl(fileno, termios.TIOCGWINSZ, buf, True)
#    fcntl.ioctl(0, termios.TIOCGWINSZ, buf, True)

    # Return rows, cols
    return buf[0], buf[1]


class raw_mode(object):
    """
    ::

        with raw_mode(stdin):
            ''' the pseudo-terminal stdin is now used in raw mode '''
    """
    def __init__(self, fileno):
        self.fileno = fileno
        self.attrs_before = termios.tcgetattr(fileno)

    def __enter__(self):
        # NOTE: On os X systems, using pty.setraw() fails. Therefor we are using this:
        newattr = termios.tcgetattr(self.fileno)
        newattr[tty.LFLAG] = self._patch(newattr[tty.LFLAG])
        termios.tcsetattr(self.fileno, termios.TCSANOW, newattr)

    def _patch(self, attrs):
        return attrs & ~(termios.ECHO | termios.ICANON | termios.IEXTEN | termios.ISIG)

    def __exit__(self, *a, **kw):
        termios.tcsetattr(self.fileno, termios.TCSANOW, self.attrs_before)


class cooked_mode(raw_mode):
    """
    (The opposide of ``raw_mode``::

        with cooked_mode(stdin):
            ''' the pseudo-terminal stdin is now used in cooked mode. '''
    """
    def _patch(self, attrs):
        return attrs | (termios.ECHO | termios.ICANON | termios.IEXTEN | termios.ISIG)


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


class EventHook(object):
    """
    Event hook::

        e = EventHook()
        e += handler_function  # Add event handler.
        e.fire()  # Fire event.

    Thanks to Michael Foord:
    http://www.voidspace.org.uk/python/weblog/arch_d7_2007_02_03.shtml#e616
    """
    def __init__(self):
        self.__handlers = []

    def __iadd__(self, handler):
        self.__handlers.append(handler)
        return self

    def __isub__(self, handler):
        self.__handlers.remove(handler)
        return self

    def fire(self, *args, **keywargs):
        for handler in self.__handlers:
            handler(*args, **keywargs)
