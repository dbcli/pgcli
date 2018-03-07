"""
Output for vt100 terminals.

A lot of thanks, regarding outputting of colors, goes to the Pygments project:
(We don't rely on Pygments anymore, because many things are very custom, and
everything has been highly optimized.)
http://pygments.org/
"""
from __future__ import unicode_literals

from prompt_toolkit.layout.screen import Size
from prompt_toolkit.output import Output
from prompt_toolkit.styles.base import ANSI_COLOR_NAMES

from .color_depth import ColorDepth

from six.moves import range
import array
import errno
import six

__all__ = [
    'Vt100_Output',
]


FG_ANSI_COLORS = {
    'ansidefault': 39,

    # Low intensity.
    'ansiblack':   30,
    'ansired':     31,
    'ansigreen':   32,
    'ansiyellow':  33,
    'ansiblue':    34,
    'ansimagenta': 35,
    'ansicyan':    36,
    'ansigray':    37,

    # High intensity.
    'ansibrightblack':   90,
    'ansibrightred':     91,
    'ansibrightgreen':   92,
    'ansibrightyellow':  93,
    'ansibrightblue':    94,
    'ansibrightmagenta': 95,
    'ansibrightcyan':    96,
    'ansiwhite':         97,
}

BG_ANSI_COLORS = {
    'ansidefault':     49,

    # Low intensity.
    'ansiblack':   40,
    'ansired':     41,
    'ansigreen':   42,
    'ansiyellow':  43,
    'ansiblue':    44,
    'ansimagenta': 45,
    'ansicyan':    46,
    'ansigray':    47,

    # High intensity.
    'ansibrightblack':   100,
    'ansibrightred':     101,
    'ansibrightgreen':   102,
    'ansibrightyellow':  103,
    'ansibrightblue':    104,
    'ansibrightmagenta': 105,
    'ansibrightcyan':    106,
    'ansiwhite':         107,
}


ANSI_COLORS_TO_RGB = {
    'ansidefault':     (0x00, 0x00, 0x00),  # Don't use, 'default' doesn't really have a value.
    'ansiblack':       (0x00, 0x00, 0x00),
    'ansigray':        (0xe5, 0xe5, 0xe5),
    'ansibrightblack': (0x7f, 0x7f, 0x7f),
    'ansiwhite':       (0xff, 0xff, 0xff),

    # Low intensity.
    'ansired':     (0xcd, 0x00, 0x00),
    'ansigreen':   (0x00, 0xcd, 0x00),
    'ansiyellow':  (0xcd, 0xcd, 0x00),
    'ansiblue':    (0x00, 0x00, 0xcd),
    'ansimagenta': (0xcd, 0x00, 0xcd),
    'ansicyan':    (0x00, 0xcd, 0xcd),

    # High intensity.
    'ansibrightred':     (0xff, 0x00, 0x00),
    'ansibrightgreen':   (0x00, 0xff, 0x00),
    'ansibrightyellow':  (0xff, 0xff, 0x00),
    'ansibrightblue':    (0x00, 0x00, 0xff),
    'ansibrightmagenta': (0xff, 0x00, 0xff),
    'ansibrightcyan':    (0x00, 0xff, 0xff),
}


assert set(FG_ANSI_COLORS) == set(ANSI_COLOR_NAMES)
assert set(BG_ANSI_COLORS) == set(ANSI_COLOR_NAMES)
assert set(ANSI_COLORS_TO_RGB) == set(ANSI_COLOR_NAMES)


def _get_closest_ansi_color(r, g, b, exclude=()):
    """
    Find closest ANSI color. Return it by name.

    :param r: Red (Between 0 and 255.)
    :param g: Green (Between 0 and 255.)
    :param b: Blue (Between 0 and 255.)
    :param exclude: A tuple of color names to exclude. (E.g. ``('ansired', )``.)
    """
    assert isinstance(exclude, tuple)

    # When we have a bit of saturation, avoid the gray-like colors, otherwise,
    # too often the distance to the gray color is less.
    saturation = abs(r - g) + abs(g - b) + abs(b - r)  # Between 0..510

    if saturation > 30:
        exclude += ('ansilightgray', 'ansidarkgray', 'ansiwhite', 'ansiblack')

    # Take the closest color.
    # (Thanks to Pygments for this part.)
    distance = 257 * 257 * 3  # "infinity" (>distance from #000000 to #ffffff)
    match = 'ansidefault'

    for name, (r2, g2, b2) in ANSI_COLORS_TO_RGB.items():
        if name != 'ansidefault' and name not in exclude:
            d = (r - r2) ** 2 + (g - g2) ** 2 + (b - b2) ** 2

            if d < distance:
                match = name
                distance = d

    return match


class _16ColorCache(dict):
    """
    Cache which maps (r, g, b) tuples to 16 ansi colors.

    :param bg: Cache for background colors, instead of foreground.
    """
    def __init__(self, bg=False):
        assert isinstance(bg, bool)
        self.bg = bg

    def get_code(self, value, exclude=()):
        """
        Return a (ansi_code, ansi_name) tuple. (E.g. ``(44, 'ansiblue')``.) for
        a given (r,g,b) value.
        """
        key = (value, exclude)
        if key not in self:
            self[key] = self._get(value, exclude)
        return self[key]

    def _get(self, value, exclude=()):
        r, g, b = value
        match = _get_closest_ansi_color(r, g, b, exclude=exclude)

        # Turn color name into code.
        if self.bg:
            code = BG_ANSI_COLORS[match]
        else:
            code = FG_ANSI_COLORS[match]

        self[value] = code
        return code, match


class _256ColorCache(dict):
    """
    Cache which maps (r, g, b) tuples to 256 colors.
    """
    def __init__(self):
        # Build color table.
        colors = []

        # colors 0..15: 16 basic colors
        colors.append((0x00, 0x00, 0x00))  # 0
        colors.append((0xcd, 0x00, 0x00))  # 1
        colors.append((0x00, 0xcd, 0x00))  # 2
        colors.append((0xcd, 0xcd, 0x00))  # 3
        colors.append((0x00, 0x00, 0xee))  # 4
        colors.append((0xcd, 0x00, 0xcd))  # 5
        colors.append((0x00, 0xcd, 0xcd))  # 6
        colors.append((0xe5, 0xe5, 0xe5))  # 7
        colors.append((0x7f, 0x7f, 0x7f))  # 8
        colors.append((0xff, 0x00, 0x00))  # 9
        colors.append((0x00, 0xff, 0x00))  # 10
        colors.append((0xff, 0xff, 0x00))  # 11
        colors.append((0x5c, 0x5c, 0xff))  # 12
        colors.append((0xff, 0x00, 0xff))  # 13
        colors.append((0x00, 0xff, 0xff))  # 14
        colors.append((0xff, 0xff, 0xff))  # 15

        # colors 16..232: the 6x6x6 color cube
        valuerange = (0x00, 0x5f, 0x87, 0xaf, 0xd7, 0xff)

        for i in range(217):
            r = valuerange[(i // 36) % 6]
            g = valuerange[(i // 6) % 6]
            b = valuerange[i % 6]
            colors.append((r, g, b))

        # colors 233..253: grayscale
        for i in range(1, 22):
            v = 8 + i * 10
            colors.append((v, v, v))

        self.colors = colors

    def __missing__(self, value):
        r, g, b = value

        # Find closest color.
        # (Thanks to Pygments for this!)
        distance = 257 * 257 * 3  # "infinity" (>distance from #000000 to #ffffff)
        match = 0

        for i, (r2, g2, b2) in enumerate(self.colors):
            d = (r - r2) ** 2 + (g - g2) ** 2 + (b - b2) ** 2

            if d < distance:
                match = i
                distance = d

        # Turn color name into code.
        self[value] = match
        return match


_16_fg_colors = _16ColorCache(bg=False)
_16_bg_colors = _16ColorCache(bg=True)
_256_colors = _256ColorCache()


class _EscapeCodeCache(dict):
    """
    Cache for VT100 escape codes. It maps
    (fgcolor, bgcolor, bold, underline, reverse) tuples to VT100 escape sequences.

    :param true_color: When True, use 24bit colors instead of 256 colors.
    """
    def __init__(self, color_depth):
        assert color_depth in ColorDepth._ALL
        self.color_depth = color_depth

    def __missing__(self, attrs):
        fgcolor, bgcolor, bold, underline, italic, blink, reverse, hidden = attrs
        parts = []

        parts.extend(self._colors_to_code(fgcolor, bgcolor))

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
        if hidden:
            parts.append('8')

        if parts:
            result = '\x1b[0;' + ';'.join(parts) + 'm'
        else:
            result = '\x1b[0m'

        self[attrs] = result
        return result

    def _color_name_to_rgb(self, color):
        " Turn 'ffffff', into (0xff, 0xff, 0xff). "
        try:
            rgb = int(color, 16)
        except ValueError:
            raise
        else:
            r = (rgb >> 16) & 0xff
            g = (rgb >> 8) & 0xff
            b = rgb & 0xff
            return r, g, b

    def _colors_to_code(self, fg_color, bg_color):
        " Return a tuple with the vt100 values  that represent this color. "
        # When requesting ANSI colors only, and both fg/bg color were converted
        # to ANSI, ensure that the foreground and background color are not the
        # same. (Unless they were explicitly defined to be the same color.)
        fg_ansi = [()]

        def get(color, bg):
            table = BG_ANSI_COLORS if bg else FG_ANSI_COLORS

            if not color or self.color_depth == ColorDepth.DEPTH_1_BIT:
                return ()

            # 16 ANSI colors. (Given by name.)
            elif color in table:
                return (table[color], )

            # RGB colors. (Defined as 'ffffff'.)
            else:
                try:
                    rgb = self._color_name_to_rgb(color)
                except ValueError:
                    return ()

                # When only 16 colors are supported, use that.
                if self.color_depth == ColorDepth.DEPTH_4_BIT:
                    if bg:  # Background.
                        if fg_color != bg_color:
                            exclude = (fg_ansi[0], )
                        else:
                            exclude = ()
                        code, name = _16_bg_colors.get_code(rgb, exclude=exclude)
                        return (code, )
                    else:  # Foreground.
                        code, name = _16_fg_colors.get_code(rgb)
                        fg_ansi[0] = name
                        return (code, )

                # True colors. (Only when this feature is enabled.)
                elif self.color_depth == ColorDepth.DEPTH_24_BIT:
                    r, g, b = rgb
                    return (48 if bg else 38, 2, r, g, b)

                # 256 RGB colors.
                else:
                    return (48 if bg else 38, 5, _256_colors[rgb])

        result = []
        result.extend(get(fg_color, False))
        result.extend(get(bg_color, True))

        return map(six.text_type, result)


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
    # Note: We should not pass 'True' as a fourth parameter to 'ioctl'. (True
    #       is the default.) This causes segmentation faults on some systems.
    #       See: https://github.com/jonathanslenders/python-prompt-toolkit/pull/364
    fcntl.ioctl(fileno, termios.TIOCGWINSZ, buf)

    # Return rows, cols
    return buf[0], buf[1]


class Vt100_Output(Output):
    """
    :param get_size: A callable which returns the `Size` of the output terminal.
    :param stdout: Any object with has a `write` and `flush` method + an 'encoding' property.
    :param term: The terminal environment variable. (xterm, xterm-256color, linux, ...)
    :param write_binary: Encode the output before writing it. If `True` (the
        default), the `stdout` object is supposed to expose an `encoding` attribute.
    """
    def __init__(self, stdout, get_size, term=None, write_binary=True):
        assert callable(get_size)
        assert term is None or isinstance(term, six.text_type)
        assert all(hasattr(stdout, a) for a in ('write', 'flush'))

        if write_binary:
            assert hasattr(stdout, 'encoding')

        self._buffer = []
        self.stdout = stdout
        self.write_binary = write_binary
        self.get_size = get_size
        self.term = term or 'xterm'

        # Cache for escape codes.
        self._escape_code_caches = {
            ColorDepth.DEPTH_1_BIT: _EscapeCodeCache(ColorDepth.DEPTH_1_BIT),
            ColorDepth.DEPTH_4_BIT: _EscapeCodeCache(ColorDepth.DEPTH_4_BIT),
            ColorDepth.DEPTH_8_BIT: _EscapeCodeCache(ColorDepth.DEPTH_8_BIT),
            ColorDepth.DEPTH_24_BIT: _EscapeCodeCache(ColorDepth.DEPTH_24_BIT),
        }

    @classmethod
    def from_pty(cls, stdout, term=None):
        """
        Create an Output class from a pseudo terminal.
        (This will take the dimensions by reading the pseudo
        terminal attributes.)
        """
        assert stdout.isatty()

        def get_size():
            rows, columns = _get_size(stdout.fileno())
            return Size(rows=rows, columns=columns)

        return cls(stdout, get_size, term=term)

    def fileno(self):
        " Return file descriptor. "
        return self.stdout.fileno()

    def encoding(self):
        " Return encoding used for stdout. "
        return self.stdout.encoding

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
        if self.term not in ('linux', 'eterm-color'):  # Not supported by the Linux console.
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

    def set_attributes(self, attrs, color_depth):
        """
        Create new style and output.

        :param attrs: `Attrs` instance.
        """
        # Get current depth.
        escape_code_cache = self._escape_code_caches[color_depth]

        # Write escape character.
        self.write_raw(escape_code_cache[attrs])

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
            pass
        elif amount == 1:
            self.write_raw('\x1b[A')
        else:
            self.write_raw('\x1b[%iA' % amount)

    def cursor_down(self, amount):
        if amount == 0:
            pass
        elif amount == 1:
            # Note: Not the same as '\n', '\n' can cause the window content to
            #       scroll.
            self.write_raw('\x1b[B')
        else:
            self.write_raw('\x1b[%iB' % amount)

    def cursor_forward(self, amount):
        if amount == 0:
            pass
        elif amount == 1:
            self.write_raw('\x1b[C')
        else:
            self.write_raw('\x1b[%iC' % amount)

    def cursor_backward(self, amount):
        if amount == 0:
            pass
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
            if self.write_binary:
                if hasattr(self.stdout, 'buffer'):
                    out = self.stdout.buffer  # Py3.
                else:
                    out = self.stdout
                out.write(data.encode(self.stdout.encoding or 'utf-8', 'replace'))
            else:
                self.stdout.write(data)

            self.stdout.flush()
        except IOError as e:
            if e.args and e.args[0] == errno.EINTR:
                # Interrupted system call. Can happen in case of a window
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
