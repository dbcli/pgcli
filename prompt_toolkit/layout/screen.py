from __future__ import unicode_literals

from prompt_toolkit.cache import FastDictCache
from prompt_toolkit.utils import get_cwidth

from collections import defaultdict, namedtuple

__all__ = (
    'Point',
    'Size',
    'Screen',
    'Char',
)


Point = namedtuple('Point', 'y x')
Size = namedtuple('Size', 'rows columns')


class Char(object):
    """
    Represent a single character in a :class:`.Screen`.

    This should be considered immutable.

    :param char: A single character (can be a double-width character).
    :param style: A style string. (Can contain classnames.)
    """
    __slots__ = ('char', 'style', 'width')

    # If we end up having one of these special control sequences in the input string,
    # we should display them as follows:
    # Usually this happens after a "quoted insert".
    display_mappings = {
        '\x00': '^@',  # Control space
        '\x01': '^A',
        '\x02': '^B',
        '\x03': '^C',
        '\x04': '^D',
        '\x05': '^E',
        '\x06': '^F',
        '\x07': '^G',
        '\x08': '^H',
        '\x09': '^I',
        '\x0a': '^J',
        '\x0b': '^K',
        '\x0c': '^L',
        '\x0d': '^M',
        '\x0e': '^N',
        '\x0f': '^O',
        '\x10': '^P',
        '\x11': '^Q',
        '\x12': '^R',
        '\x13': '^S',
        '\x14': '^T',
        '\x15': '^U',
        '\x16': '^V',
        '\x17': '^W',
        '\x18': '^X',
        '\x19': '^Y',
        '\x1a': '^Z',
        '\x1b': '^[',  # Escape
        '\x1c': '^\\',
        '\x1d': '^]',
        '\x1f': '^_',
        '\x7f': '^?',  # ASCII Delete (backspace).
    }

    def __init__(self, char=' ', style=''):
        # If this character has to be displayed otherwise, take that one.
        char = self.display_mappings.get(char, char)

        self.char = char
        self.style = style

        # Calculate width. (We always need this, so better to store it directly
        # as a member for performance.)
        self.width = get_cwidth(char)

    def __eq__(self, other):
        return self.char == other.char and self.style == other.style

    def __ne__(self, other):
        # Not equal: We don't do `not char.__eq__` here, because of the
        # performance of calling yet another function.
        return self.char != other.char or self.style != other.style

    def __repr__(self):
        return '%s(%r, %r)' % (self.__class__.__name__, self.char, self.style)


_CHAR_CACHE = FastDictCache(Char, size=1000 * 1000)
Transparent = '[transparent]'


class Screen(object):
    """
    Two dimentional buffer of :class:`.Char` instances.
    """
    def __init__(self, default_char=None, initial_width=0, initial_height=0):
        if default_char is None:
            default_char = _CHAR_CACHE[' ', Transparent]

        self.data_buffer = defaultdict(lambda: defaultdict(lambda: default_char))

        #: Escape sequences to be injected.
        self.zero_width_escapes = defaultdict(lambda: defaultdict(lambda: ''))

        #: Position of the cursor.
        self.cursor_positions = {}  # Map `Window` objects to `Point` objects.

        #: Visibility of the cursor.
        self.show_cursor = True

        #: (Optional) Where to position the menu. E.g. at the start of a completion.
        #: (We can't use the cursor position, because we don't want the
        #: completion menu to change its position when we browse through all the
        #: completions.)
        self.menu_positions = {}  # Map `Window` objects to `Point` objects.

        #: Currently used width/height of the screen. This will increase when
        #: data is written to the screen.
        self.width = initial_width or 0
        self.height = initial_height or 0

        # Windows that have been drawn. (Each `Window` class will add itself to
        # this list.)
        self.visible_windows = []

    def set_cursor_position(self, window, position):
        " Set the cursor position for a given window. "
        self.cursor_positions[window] = position

    def set_menu_position(self, window, position):
        " Set the cursor position for a given window. "
        self.menu_positions[window] = position

    def get_cursor_position(self, window):
        """
        Get the cursor position for a given window.
        Returns a `Point`.
        """
        try:
            return self.cursor_positions[window]
        except KeyError:
            return Point(0, 0)

    def get_menu_position(self, window):
        """
        Get the menu position for a given window.
        (This falls back to the cursor position if no menu position was set.)
        """
        try:
            return self.menu_positions[window]
        except KeyError:
            try:
                return self.cursor_positions[window]
            except KeyError:
                return Point(0, 0)

    def replace_all_styles(self, style_str):  # TODO: this is used for Aborted. shouldn't this be an append????
        """
        For all the characters in the screen.
        Set the style string to the given `style_str`.
        """
        b = self.data_buffer
        char_cache = _CHAR_CACHE

        prepend_style = style_str + ' '

        for y, row in b.items():
            for x, char in row.items():
                b[y][x] = char_cache[char.char, prepend_style + char.style]

    def fill_area(self, write_position, style='', after=False):
        """
        Fill the content of this area, using the given `style`.
        The style is prepended before whatever was here before.
        """
        if not style.strip():
            return

        xmin = write_position.xpos
        xmax = write_position.xpos + write_position.width
        char_cache = _CHAR_CACHE
        data_buffer = self.data_buffer

        if after:
            append_style = ' ' + style
            prepend_style = ''
        else:
            append_style = ''
            prepend_style = style + ' '

        for y in range(write_position.ypos, write_position.ypos + write_position.height):
            row = data_buffer[y]
            for x in range(xmin, xmax):
                cell = row[x]
                row[x] = char_cache[cell.char, prepend_style + cell.style + append_style]


class WritePosition(object):
    def __init__(self, xpos, ypos, width, height, extended_height=None):
        assert height >= 0
        assert extended_height is None or extended_height >= 0
        assert width >= 0
        # xpos and ypos can be negative. (A float can be partially visible.)

        self.xpos = xpos
        self.ypos = ypos
        self.width = width
        self.height = height
        self.extended_height = extended_height or height

    def __repr__(self):
        return '%s(x=%r, y=%r, width=%r, height=%r, extended_height=%r)' % (
            self.__class__.__name__,
            self.xpos, self.ypos, self.width, self.height, self.extended_height)
