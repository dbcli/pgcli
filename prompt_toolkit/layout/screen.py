from __future__ import unicode_literals

from prompt_toolkit.utils import get_cwidth
from collections import defaultdict, namedtuple
from pygments.token import Token
import six

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
    Represent a single character in a `Screen.`

    This should be considered immutable.
    """
    __slots__ = ('char', 'token', 'width')

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
        '\x7f': '^?',  # Control backspace
    }

    def __init__(self, char=' ', token=Token):
        # If this character has to be displayed otherwise, take that one.
        char = self.display_mappings.get(char, char)

        self.char = char
        self.token = token

        # Calculate width. (We always need this, so better to store it directly
        # as a member for performance.)
        self.width = get_cwidth(char)

    def __eq__(self, other):
        return self.char == other.char and self.token == other.token

    def __ne__(self, other):
        # Not equal: We don't do `not char.__eq__` here, because of the
        # performance of calling yet another function.
        return self.char != other.char or self.token != other.token

    def __repr__(self):
        return '%s(%r, %r)' % (self.__class__.__name__, self.char, self.token)


class CharCache(dict):
    """
    Cache of Char instances.
    Mapping of (character, Token) tuples to Char instances.

    (Char instances should be considered immutable.)
    """
    def __missing__(self, key):
        c = Char(*key)
        self[key] = c
        return c


_CHAR_CACHE = CharCache()
Transparent = Token.Transparent


class Screen(object):
    """
    Two dimentional buffer for the output.
    """
    def __init__(self, default_char=None, initial_width=0, initial_height=0):
        if default_char is None:
            default_char = Char(token=Transparent)

        self._buffer = defaultdict(lambda: defaultdict(lambda: default_char))

        #: Position of the cursor.
        self.cursor_position = Point(y=0, x=0)

        #: (Optional) Where to position the menu. E.g. at the start of a completion.
        #: (We can't use the cursor position, because we don't want the
        #: completion menu to change its position when we browse through all the
        #: completions.)
        self.menu_position = None

        #: Currently used width/height of the screen. This will increase when
        #: data is written to the screen.
        self.width = initial_width or 0
        self.height = initial_height or 0

        #: Mapping of buffer lines to input lines.
        self.screen_line_to_input_line = {}

    def write_data(self, data, width=None):
        """
        Write data at :class:`WritePosition`.
        When one of the tokens in the token list is Token.SetCursorPosition,
        this will set the cursor position.

        :param data: List of Token tuples to write to the buffer.
        :param width: Width of the line wrap. (Don't wrap when `width` is None.)
        """
        if width is None:
            width = 10 ** 100  # A very big number.
        buffer = self._buffer
        screen_line_to_input_line = self.screen_line_to_input_line

        x = 0
        y = 0
        max_allowed_x = x + width
        index = 0
        line_number = 0
        requires_line_feed = True
        indexes_to_pos = {}  # Map input positions to (x, y) coordinates.
        set_cursor_position = Token.SetCursorPosition
        max_x = 0

        for token, text in data:
            if token == set_cursor_position:
                self.cursor_position = Point(y=y, x=x)

            for char in text:
                # Line feed.
                if requires_line_feed:
                    screen_line_to_input_line[y] = line_number
                    requires_line_feed = False

                char_obj = _CHAR_CACHE[char, token]
                char_width = char_obj.width

                # In case there is no more place left at this line, go first to the
                # following line. (Also in case of double-width characters.)
                if x + char_width > max_allowed_x and char != '\n':
                    max_x = max(max_x, x)
                    y += 1
                    x = 0

                # Keep mapping of index to position.
                indexes_to_pos[index] = (x, y)

                # Insertion of newline
                if char == '\n':
                    max_x = max(max_x, x)
                    y += 1
                    x = 0
                    requires_line_feed = True
                    line_number += 1

                # Insertion of a 'visible' character.
                else:
                    buffer_y = buffer[y]
                    buffer_y[x] = char_obj

                    # When we have a double width character, store this byte in the
                    # second cell. So that if this character gets deleted afterwarsd,
                    # the ``output_screen_diff`` will notice that this byte is also
                    # gone and redraw both cells.
                    if char_width > 1:
                        buffer_y[x+1] = Char(six.unichr(0))

                    # Move position
                    x += char_width

                index += 1

        self.height = max(self.height, y + 1)
        self.width = max(self.width, max_x, x)

        return indexes_to_pos

    def replace_all_tokens(self, token):
        """
        For all the characters in the screen. Set the token to the given `token`.
        """
        b = self._buffer

        for y, row in b.items():
            for x, char in row.items():
                b[y][x] = _CHAR_CACHE[char.char, token]


class WritePosition(object):
    def __init__(self, xpos, ypos, width, height, extended_height=None):
        assert height >= 0
        assert extended_height is None or extended_height >= 0
        assert width >= 0
        assert xpos >= 0
        assert ypos >= 0

        self.xpos = xpos
        self.ypos = ypos
        self.width = width
        self.height = height
        self.extended_height = extended_height or height

    def __repr__(self):
        return '%s(%r, %r, %r %r, %r)' % (
            self.__class__.__name__,
            self.xpos, self.ypos, self.width, self.height, self.extended_height)
