from __future__ import unicode_literals
import array
import fcntl
import signal
import termios
import tty
import six


def get_size(fileno):
    # Thanks to fabric (fabfile.org), and
    # http://sqizit.bartletts.id.au/2011/02/14/pseudo-terminals-in-python/
    """
    Get the size of this pseudo terminal.

    :param fileno: stdout.fileno()
    :returns: A (rows, cols) tuple.
    """
    #assert stdout.isatty()

    # Buffer for the C call
    buf = array.array(u'h' if six.PY3 else b'h', [0, 0, 0, 0 ])

    # Do TIOCGWINSZ (Get)
    fcntl.ioctl(fileno, termios.TIOCGWINSZ, buf, True)
#    fcntl.ioctl(0, termios.TIOCGWINSZ, buf, True)

    # Return rows, cols
    return buf[0], buf[1]



class raw_mode(object):
    """
    with raw_mode(stdin):
        ''' the pseudo-terminal stdin is now used in raw mode '''
    """
    def __init__(self, fileno):
        self.fileno = fileno
        self.attrs_before = termios.tcgetattr(fileno)

    def __enter__(self):
        # NOTE: On os X systems, using pty.setraw() fails. Therefor we are using this:
        newattr = termios.tcgetattr(self.fileno)
        newattr[tty.LFLAG] = newattr[tty.LFLAG] & ~(
                        termios.ECHO | termios.ICANON | termios.IEXTEN | termios.ISIG)
        termios.tcsetattr(self.fileno, termios.TCSANOW, newattr)

    def __exit__(self, *a, **kw):
        termios.tcsetattr(self.fileno, termios.TCSANOW, self.attrs_before)


class call_on_sigwinch(object):
    """
    Context manager which Installs a SIGWINCH callback.
    (This signal occurs when the terminal size changes.)
    """
    def __init__(self, callback):
        self.callback = callback

    def __enter__(self):
        self.previous_callback = signal.signal(signal.SIGWINCH, lambda *a:self.callback())

    def __exit__(self, *a, **kw):
        signal.signal(signal.SIGWINCH, self.previous_callback)
