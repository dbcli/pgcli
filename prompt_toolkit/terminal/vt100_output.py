from __future__ import unicode_literals
from pygments.formatters.terminal256 import Terminal256Formatter

from prompt_toolkit.filters import to_simple_filter
from prompt_toolkit.layout.screen import Size
from prompt_toolkit.renderer import Output
from prompt_toolkit.styles import ANSI_COLOR_NAMES

import array
import errno
import six

__all__ = (
    'Vt100_Output',
)


# Global variable to keep the colour table in memory.
_tf = Terminal256Formatter()

#: If True: write the output of the renderer also to the following file. This
#: is very useful for debugging. (e.g.: to see that we don't write more bytes
#: than required.)
_DEBUG_RENDER_OUTPUT = False
_DEBUG_RENDER_OUTPUT_FILENAME = '/tmp/prompt-toolkit-render-output'

FG_ANSI_COLORS = {
    'black':   30,
    'default': 39,
    'white':   97,

    # Low intensity.
    'red':     31,
    'green':   32,
    'yellow':  33,
    'blue':    34,
    'magenta': 35,
    'cyan':    36,
    'gray':    37,


    # High intensity.
    'dark-gray':      90,  # Bright black.
    'bright-red':     91,
    'bright-green':   92,
    'bright-yellow':  93,
    'bright-blue':    94,
    'bright-magenta': 95,
    'bright-cyan':    96,
}

BG_ANSI_COLORS = {
    'black':   40,
    'default': 49,
    'white':   107,

    # Low intensity.
    'red':     41,
    'green':   42,
    'yellow':  43,
    'blue':    44,
    'magenta': 45,
    'cyan':    46,
    'gray':    47,

    # High intensity.
    'dark-gray':      100,  # bright black.
    'bright-red':     101,
    'bright-green':   102,
    'bright-yellow':  103,
    'bright-blue':    104,
    'bright-magenta': 105,
    'bright-cyan':    106,
}

assert set(FG_ANSI_COLORS) == set(ANSI_COLOR_NAMES)
assert set(BG_ANSI_COLORS) == set(ANSI_COLOR_NAMES)


class _EscapeCodeCache(dict):
    """
    Cache for VT100 escape codes. It maps
    (fgcolor, bgcolor, bold, underline, reverse) tuples to VT100 escape sequences.

    :param true_color: When True, use 24bit colors instead of 256 colors.
    """
    def __init__(self, true_color=False):
        assert isinstance(true_color, bool)
        self.true_color = true_color

    def __missing__(self, attrs):
        fgcolor, bgcolor, bold, underline, italic, blink, reverse = attrs

        parts = []

        if fgcolor:
            parts.extend(self._color_to_code(fgcolor))
        if bgcolor:
            parts.extend(self._color_to_code(bgcolor, True))
        if bold:
            parts.append('1')
        if italic:
            parts.append('3')
        if blink:
            parts.append('5')
        if underline:
            parts.append('4')
        if reverse:
            parts.append('7')

        if parts:
            result = '\x1b[0;' + ';'.join(parts) + 'm'
        else:
            result = '\x1b[0m'

        self[attrs] = result
        return result

    def _color_to_code(self, color, bg=False):
       table = BG_ANSI_COLORS if bg else FG_ANSI_COLORS

       # 16 ANSI colors.
       if color in table:
           result = (table[color], )

       # True colors.
       elif self.true_color:
            try:
                rgb = int(color, 16)
            except ValueError:
                result = []

            r = (rgb >> 16) & 0xff
            g = (rgb >> 8) & 0xff
            b = rgb & 0xff

            result = (48 if bg else 38, 2, r, g, b)

       # 256 RGB colors.
       else:
           result = (48 if bg else 38, 5, _tf._color_index(color))

       return map(six.text_type, result)


_ESCAPE_CODE_CACHE = _EscapeCodeCache(true_color=False)
_ESCAPE_CODE_CACHE_TRUE_COLOR = _EscapeCodeCache(true_color=True)


def _get_size(fileno):
    # Thanks to fabric (fabfile.org), and
    # http://sqizit.bartletts.id.au/2011/02/14/pseudo-terminals-in-python/
    """
    Get the size of this pseudo terminal.

    :param fileno: stdout.fileno()
    :returns: A (rows, cols) tuple.
    """
    # Inline imports, because these modules are not available on Windows.
    # (This file is used by ConEmuOutput, which is used on Windows.)
    import fcntl
    import termios

    # Buffer for the C call
    buf = array.array(b'h' if six.PY2 else u'h', [0, 0, 0, 0])

    # Do TIOCGWINSZ (Get)
    fcntl.ioctl(fileno, termios.TIOCGWINSZ, buf, True)

    # Return rows, cols
    return buf[0], buf[1]


class Vt100_Output(Output):
    """
    :param get_size: A callable which returns the `Size` of the output terminal.
    :param stdout: Any object with has a `write` and `flush` method.
    :param true_color: Use 24bit color instead of 256 colors. (Can be a :class:`SimpleFilter`.)
    """
    def __init__(self, stdout, get_size, true_color=False):
        self._buffer = []
        self.stdout = stdout
        self.get_size = get_size
        self.true_color = to_simple_filter(true_color)

    @classmethod
    def from_pty(cls, stdout, true_color=False):
        """
        Create an Output class from a pseudo terminal.
        (This will take the dimensions by reading the pseudo
        terminal attributes.)
        """
        def get_size():
            rows, columns = _get_size(stdout.fileno())
            return Size(rows=rows, columns=columns)

        return cls(stdout, get_size, true_color=true_color)

    def write_raw(self, data):
        """
        Write raw data to output.
        """
        self._buffer.append(data)

    def write(self, data):
        """
        Write text to output.
        (Removes vt100 escape codes. -- used for safely writing text.)
        """
        self._buffer.append(data.replace('\x1b', '?'))

    def set_title(self, title):
        """
        Set terminal title.
        """
        self.write_raw('\x1b]2;%s\x07' % title.replace('\x1b', '').replace('\x07', ''))

    def clear_title(self):
        self.set_title('')

    def erase_screen(self):
        """
        Erases the screen with the background colour and moves the cursor to
        home.
        """
        self.write_raw('\x1b[2J')

    def enter_alternate_screen(self):
        self.write_raw('\x1b[?1049h\x1b[H')

    def quit_alternate_screen(self):
        self.write_raw('\x1b[?1049l')

    def enable_mouse_support(self):
        self.write_raw('\x1b[?1000h')

        # Enable urxvt Mouse mode. (For terminals that understand this.)
        self.write_raw('\x1b[?1015h')

        # Also enable Xterm SGR mouse mode. (For terminals that understand this.)
        self.write_raw('\x1b[?1006h')

        # Note: E.g. lxterminal understands 1000h, but not the urxvt or sgr
        #       extensions.

    def disable_mouse_support(self):
        self.write_raw('\x1b[?1000l')
        self.write_raw('\x1b[?1015l')
        self.write_raw('\x1b[?1006l')

    def erase_end_of_line(self):
        """
        Erases from the current cursor position to the end of the current line.
        """
        self.write_raw('\x1b[K')

    def erase_down(self):
        """
        Erases the screen from the current line down to the bottom of the
        screen.
        """
        self.write_raw('\x1b[J')

    def reset_attributes(self):
        self.write_raw('\x1b[0m')

    def set_attributes(self, attrs):
        """
        Create new style and output.

        :param attrs: `Attrs` instance.
        """
        if self.true_color():
            self.write_raw(_ESCAPE_CODE_CACHE_TRUE_COLOR[attrs])
        else:
            self.write_raw(_ESCAPE_CODE_CACHE[attrs])

    def disable_autowrap(self):
        self.write_raw('\x1b[?7l')

    def enable_autowrap(self):
        self.write_raw('\x1b[?7h')

    def enable_bracketed_paste(self):
        self.write_raw('\x1b[?2004h')

    def disable_bracketed_paste(self):
        self.write_raw('\x1b[?2004l')

    def cursor_goto(self, row=0, column=0):
        """ Move cursor position. """
        self.write_raw('\x1b[%i;%iH' % (row, column))

    def cursor_up(self, amount):
        if amount == 0:
            self.write_raw('')
        elif amount == 1:
            self.write_raw('\x1b[A')
        else:
            self.write_raw('\x1b[%iA' % amount)

    def cursor_down(self, amount):
        if amount == 0:
            self.write_raw('')
        elif amount == 1:
            # Note: Not the same as '\n', '\n' can cause the window content to
            #       scroll.
            self.write_raw('\x1b[B')
        else:
            self.write_raw('\x1b[%iB' % amount)

    def cursor_forward(self, amount):
        if amount == 0:
            self.write_raw('')
        elif amount == 1:
            self.write_raw('\x1b[C')
        else:
            self.write_raw('\x1b[%iC' % amount)

    def cursor_backward(self, amount):
        if amount == 0:
            self.write_raw('')
        elif amount == 1:
            self.write_raw('\b')  # '\x1b[D'
        else:
            self.write_raw('\x1b[%iD' % amount)

    def hide_cursor(self):
        self.write_raw('\x1b[?25l')

    def show_cursor(self):
        self.write_raw('\x1b[?12l\x1b[?25h')  # Stop blinking cursor and show.

    def flush(self):
        """
        Write to output stream and flush.
        """
        if not self._buffer:
            return

        data = ''.join(self._buffer)

        try:
            # (We try to encode ourself, because that way we can replace
            # characters that don't exist in the character set, avoiding
            # UnicodeEncodeError crashes. E.g. u'\xb7' does not appear in 'ascii'.)
            # My Arch Linux installation of july 2015 reported 'ANSI_X3.4-1968'
            # for sys.stdout.encoding in xterm.
            if hasattr(self.stdout, 'encoding'):
                out = self.stdout if six.PY2 else self.stdout.buffer
                out.write(data.encode(self.stdout.encoding or 'utf-8', 'replace'))
            else:
                self.stdout.write(data)

            self.stdout.flush()
        except IOError as e:
            if e.args and e.args[0] == errno.EINTR:
                # Interrupted system call. Can happpen in case of a window
                # resize signal. (Just ignore. The resize handler will render
                # again anyway.)
                pass
            elif e.args and e.args[0] == 0:
                # This can happen when there is a lot of output and the user
                # sends a KeyboardInterrupt by pressing Control-C. E.g. in
                # a Python REPL when we execute "while True: print('test')".
                # (The `ptpython` REPL uses this `Output` class instead of
                # `stdout` directly -- in order to be network transparent.)
                # So, just ignore.
                pass
            else:
                raise

        self._buffer = []

    def ask_for_cpr(self):
        """
        Asks for a cursor position report (CPR).
        """
        self.write_raw('\x1b[6n')
        self.flush()

    def bell(self):
        " Sound bell. "
        self.write_raw('\a')
        self.flush()
