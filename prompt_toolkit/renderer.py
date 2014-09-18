"""
Renders the command line on the console.
(Redraws parts of the input line that were changed.)
"""
from __future__ import unicode_literals
import sys
import six
import errno

from .utils import get_size
from .libs.wcwidth import wcwidth
from collections import defaultdict, namedtuple

from pygments.formatters.terminal256 import Terminal256Formatter, EscapeSequence
from pygments.style import Style
from pygments.token import Token

# Global variable to keep the colour table in memory.
_tf = Terminal256Formatter()

__all__ = (
    'Point',
    'Renderer',
    'Screen',
)

Point = namedtuple('Point', 'y x')
Size = namedtuple('Size', 'rows columns')


#: If True: write the output of the renderer also to the following file. This
#: is very useful for debugging. (e.g.: to see that we don't write more bytes
#: than required.)
_DEBUG_RENDER_OUTPUT = False
_DEBUG_RENDER_OUTPUT_FILENAME = '/tmp/prompt-toolkit-render-output'

#: Cache for wcwidth sizes.
_CHAR_SIZES_CACHE = [wcwidth(six.unichr(i)) for i in range(0, 64000)]


def _get_width(c):
    """
    Return width of character. Wrapper around ``wcwidth``.
    """
    try:
        return _CHAR_SIZES_CACHE[ord(c)]
    except IndexError:
        return wcwidth(c)


class TerminalCodes:
    """
    Escape codes for a VT100 terminal.

    For more info, see: http://www.termsys.demon.co.uk/vtansi.htm
    """
    #: Erases the screen with the background colour and moves the cursor to home.
    ERASE_SCREEN = '\x1b[2J'

    #: Erases from the current cursor position to the end of the current line.
    ERASE_END_OF_LINE = '\x1b[K'

    #: Erases the screen from the current line down to the bottom of the screen.
    ERASE_DOWN = '\x1b[J'

    CARRIAGE_RETURN = '\r'
    NEWLINE = '\n'
    CRLF = '\r\n'

    HIDE_CURSOR = '\x1b[?25l'
    DISPLAY_CURSOR = '\x1b[?25h'

    RESET_ATTRIBUTES = '\x1b[0m'

    DISABLE_AUTOWRAP = '\x1b[?7l'
    ENABLE_AUTOWRAP = '\x1b[?7h'


    @staticmethod
    def CURSOR_GOTO(row=0, column=0):
        """ Move cursor position. """
        return '\x1b[%i;%iH' % (row, column)

    @staticmethod
    def CURSOR_UP(amount):
        if amount == 0:
            return ''
        elif amount == 1:
            return '\x1b[A'
        else:
            return '\x1b[%iA' % amount

    @staticmethod
    def CURSOR_DOWN(amount):
        if amount == 0:
            return ''
        elif amount == 1:
            return '\x1b[B' # XXX: would just `\n' also do?
        else:
            return '\x1b[%iB' % amount

    @staticmethod
    def CURSOR_FORWARD(amount):
        if amount == 0:
            return ''
        elif amount == 1:
            return '\x1b[C'
        else:
            return '\x1b[%iC' % amount

    @staticmethod
    def CURSOR_BACKWARD(amount):
        if amount == 0:
            return ''
        elif amount == 1:
            return '\b' # '\x1b[D'
        else:
            return '\x1b[%iD' % amount


class Char(object):
    __slots__ = ('char', 'token', 'z_index')

    # If we end up having one of these special control sequences in the input string,
    # we should display them as follows:
    # Usually this happens after a "quoted insert".
    display_mappings = {
        '\x00': '^@', # Control space
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
        '\x1b': '^[', # Escape
        '\x1c': '^\\',
        '\x1d': '^]',
        '\x1f': '^_',
        '\x7f': '^?', # Control backspace
    }

    def __init__(self, char=' ', token=Token, z_index=0):
        # If this character has to be displayed otherwise, take that one.
        char = self.display_mappings.get(char, char)

        self.char = char
        self.token = token
        self.z_index = z_index

    @property
    def width(self):
        # We use the `max(0, ...` because some non printable control
        # characters, like e.g. Ctrl-underscore get a -1 wcwidth value.
        # It can be possible that these characters end up in the input text.
        return max(0, sum([_get_width(c) for c in self.char]))


class Screen(object):
    """
    Two dimentional buffer for the output.

    :param style: Pygments style.
    :param grayed: True when all tokes should be replaced by `Token.Aborted`
    """
    def __init__(self, size):
        self._buffer = defaultdict(lambda: defaultdict(Char))
        self._cursor_mappings = { } # Map `source_string_index` of input data to (row, col) screen output.
        self._x = 0
        self._y = 0

        self.size = size
        self._left_margin_func = lambda linenr, is_new_line: None

        self.cursor_position = Point(y=0, x=0)
        self._line_number = 1

    @property
    def current_height(self):
        if not self._buffer:
            return 1
        else:
            return max(self._buffer.keys()) + 1

    def get_cursor_position(self):
        return self.cursor_position

    def set_left_margin(self, func):
        """
        Set a function that returns a list of (token,text) tuples to be
        inserted after every newline.
        """
        self._left_margin_func = func or (lambda linenr, is_new_line: None)

    def write_char(self, char, token, string_index=None,
                    set_cursor_position=False, z_index=False):
        """
        Write char to current cursor position and move cursor.
        """
        assert len(char) == 1

        char_obj  = Char(char, token, z_index)
        char_width = char_obj.width

        # In case there is no more place left at this line, go first to the
        # following line. (Also in case of double-width characters.)
        if self._x + char_width > self.size.columns:
            self._y += 1
            self._x = 0
            self._left_margin_func(self._line_number, False)

        insert_pos = self._y, self._x # XXX: make a Point of this?

        if string_index is not None:
            self._cursor_mappings[string_index] = insert_pos

        if set_cursor_position:
            self.cursor_position = Point(y=self._y, x=self._x)

        # Insertion of newline
        if char == '\n':
            self._y += 1
            self._x = 0
            self._line_number += 1
            self._left_margin_func(self._line_number, True)

        # Insertion of a 'visible' character.
        else:
            if char_obj.z_index >= self._buffer[self._y][self._x].z_index:
                self._buffer[self._y][self._x] = char_obj

            # Move position
            self._x += char_width

        return insert_pos

    def write_at_pos(self, y, x, char_obj):
        """
        Write character at position (y, x).
        (Truncate when character is outside margin.)

        :param char_obj: :class:`.Char` instance.
        """
        # Add char to buffer
        if x < self.size.columns:
            if char_obj.z_index >= self._buffer[y][x].z_index:
                self._buffer[y][x] = char_obj

    def write_highlighted_at_pos(self, y, x, data, z_index=0):
        """
        Write (Token, text) tuples at position (y, x).
        (Truncate when character is outside margin.)
        """
        for token, text in data:
            for c in text:
                char_obj = Char(c, token, z_index=z_index)
                self.write_at_pos(y, x, char_obj)
                x += char_obj.width

    def write_highlighted(self, data):
        """
        Write (Token, text) tuples to the screen.
        """
        for token, text in data:
            for c in text:
                self.write_char(c, token=token)


def output_screen_diff(screen, current_pos, previous_screen=None, last_char=None, accept_or_abort=False, style=None, grayed=False):
    """
    Create diff of this screen with the previous screen.
    """
    #: Remember the last printed character.
    last_char = [last_char] # nonlocal
    background_turned_on = [False] # Nonlocal

    #: Variable for capturing the output.
    result = []
    write = result.append

    def move_cursor(new):
        if current_pos.x >= screen.size.columns - 1:
            write(TerminalCodes.CARRIAGE_RETURN)
            write(TerminalCodes.CURSOR_FORWARD(new.x))
        elif new.x < current_pos.x or current_pos.x >= screen.size.columns - 1:
            write(TerminalCodes.CURSOR_BACKWARD(current_pos.x - new.x))
        elif new.x > current_pos.x:
            write(TerminalCodes.CURSOR_FORWARD(new.x - current_pos.x))

        if new.y > current_pos.y:
            # Use newlines instead of CURSOR_DOWN, because this meight add new lines.
            # CURSOR_DOWN will never create new lines at the bottom.
            # Also reset attributes, otherwise the newline could draw a
            # background color.
            write(TerminalCodes.RESET_ATTRIBUTES)
            write(TerminalCodes.NEWLINE * (new.y - current_pos.y))
            write(TerminalCodes.CURSOR_FORWARD(new.x))
            last_char[0] = None # Forget last char after resetting attributes.
        elif new.y < current_pos.y:
            write(TerminalCodes.CURSOR_UP(current_pos.y - new.y))

        return new

    def get_style_for_token(token, replace_if_grayed=True):
        """
        Get style
        """
        # If grayed, replace token
        if grayed and replace_if_grayed:
            token = Token.Aborted

        try:
            return style.style_for_token(token)
        except KeyError:
            return None

    def chars_are_equal(new_char, old_char):
        """
        Test whether two `Char` instances are equal if printed.
        """
        new_token = Token.Aborted if grayed else new_char.token

        # We ignore z-index, that does not matter if things get painted.
        return new_char.char == old_char.char and new_token == old_char.token

    def output_char(char):
        """
        Write the output of this charact.r
        """
        # If the last printed character has the same token, it also has the
        # same style, so we don't output it.
        if last_char[0] and last_char[0].token == char.token:
            write(char.char)
        else:
            style = get_style_for_token(char.token)

            if style:
                # Create new style and output.
                fg = _tf._color_index(style['color']) if style['color'] else None
                bg = _tf._color_index(style['bgcolor']) if style['bgcolor'] else None

                e = EscapeSequence(fg=fg, bg=bg,
                        bold=style.get('bold', False),
                        underline=style.get('underline', False))

                write(TerminalCodes.RESET_ATTRIBUTES)
                write(e.color_string())
                write(char.char)

                # If we printed something with a background color, remember that.
                background_turned_on[0] = bool(bg)
            else:
                # Reset previous style and output.
                write(TerminalCodes.RESET_ATTRIBUTES)
                write(char.char)

        last_char[0] = char

    # Disable autowrap
    if not previous_screen:
        write(TerminalCodes.DISABLE_AUTOWRAP)
        write(TerminalCodes.RESET_ATTRIBUTES)

    # When the previous screen has a different size, redraw everything anyway.
    if not previous_screen or previous_screen.size != screen.size:
        current_pos = move_cursor(Point(0, 0))
        write(TerminalCodes.RESET_ATTRIBUTES)
        write(TerminalCodes.ERASE_DOWN)

        previous_screen = Screen(screen.size)

    # Get height of the screen.
    # (current_height changes as we loop over _buffer, so remember the current value.)
    current_height = screen.current_height

    # Loop over the rows.
    row_count = max(screen.current_height, previous_screen.current_height)
    c = 0 # Column counter.

    for y, r in enumerate(range(0, row_count)):
        new_row = screen._buffer[r]
        previous_row = previous_screen._buffer[r]

        new_max_line_len = max(new_row.keys()) if new_row else 0
        previous_max_line_len = max(previous_row.keys()) if previous_row else 0

        # Loop over the columns.
        c = 0
        while c < new_max_line_len + 1:
            char_width = (new_row[c].width or 1)

            if not chars_are_equal(new_row[c], previous_row[c]):
                current_pos = move_cursor(Point(y=y, x=c))
                output_char(new_row[c])
                current_pos = current_pos._replace(x=current_pos.x + char_width)

            c += char_width

        # If the new line is shorter, trim it
        if previous_screen and new_max_line_len < previous_max_line_len:
            current_pos = move_cursor(Point(y=y, x=new_max_line_len+1))
            write(TerminalCodes.RESET_ATTRIBUTES)
            write(TerminalCodes.ERASE_END_OF_LINE)
            last_char[0] = None # Forget last char after resetting attributes.

    # Move cursor:
    if accept_or_abort:
        current_pos = move_cursor(Point(y=current_height, x=0))
        write(TerminalCodes.ERASE_DOWN)
    else:
        current_pos = move_cursor(screen.get_cursor_position())

    if accept_or_abort:
        write(TerminalCodes.RESET_ATTRIBUTES)
        write(TerminalCodes.ENABLE_AUTOWRAP)

    # If the last printed character has a background color, always reset.
    # (Many terminals give weird artifacs on resize events when there is an
    # active background color.)
    if background_turned_on[0]:
        write(TerminalCodes.RESET_ATTRIBUTES)
        last_char[0] = None

    return ''.join(result), current_pos, last_char[0]


class Renderer(object):
    """

    Typical usage:

    ::

        r = Renderer(Prompt)
        r.render(Render_context(...))
    """
    screen_cls = Screen

    def __init__(self, prompt=None, stdout=None, style=None):
        self.prompt = prompt
        self._stdout = (stdout or sys.stdout)
        self._style = style or Style
        self._last_screen = None

        if _DEBUG_RENDER_OUTPUT:
            self.LOG = open(_DEBUG_RENDER_OUTPUT_FILENAME, 'ab')

        self.reset()

    def reset(self):
        # Reset position
        self._cursor_pos = Point(x=0, y=0)

        # Remember the last screen instance between renderers. This way,
        # we can create a `diff` between two screens and only output the
        # difference. It's also to remember the last height. (To show for
        # instance a toolbar at the bottom position.)
        self._last_screen = None
        self._last_char = None

    def get_size(self):
        rows, columns = get_size(self._stdout.fileno())
        return Size(rows=rows, columns=columns)

    def render_to_str(self, abort=False, accept=False):
        """
        Generate the output of the new screen. Return as string.
        """
        screen = self.screen_cls(size=self.get_size())

        self.prompt.write_to_screen(screen, self._last_screen.current_height if self._last_screen else 0,
                abort=abort, accept=accept)

        output, self._cursor_pos, self._last_char = output_screen_diff(screen, self._cursor_pos,
                self._last_screen, self._last_char, accept or abort,
                style=self._style, grayed=abort)
        self._last_screen = screen

        return output

    def render(self, abort=False, accept=False):
        # Render to string first.
        output = self.render_to_str(abort=abort, accept=accept)

        # Write output to log file.
        if _DEBUG_RENDER_OUTPUT and output:
            self.LOG.write(repr(output).encode('utf-8'))
            self.LOG.write(b'\n')
            self.LOG.flush()

        # Write to output stream.
        try:
            self._stdout.write(output)
            self._stdout.flush()
        except IOError as e:
            if e.args and e.args[0] == errno.EINTR:
                # Interrupted system call. Can happpen in case of a window
                # resize signal. (Just ignore. The resize handler will render
                # again anyway.)
                pass
            else:
                raise

    def clear(self):
        """
        Clear screen and go to 0,0
        """
        self._stdout.write(TerminalCodes.ERASE_SCREEN)
        self._stdout.write(TerminalCodes.CURSOR_GOTO(0, 0))

        self.reset()

    def _in_columns(self, item_iterator, margin_left=0): # XXX: copy of deployer.console.in_columns
        """
        :param item_iterator: An iterable, which yields either ``basestring``
                              instances, or (colored_item, length) tuples.
        """
        # Helper functions for extracting items from the iterator
        def get_length(item):
            return len(item) if isinstance(item, six.string_types) else item[1]

        def get_text(item):
            return item if isinstance(item, six.string_types) else item[0]

        # First, fetch all items
        all_items = list(item_iterator)

        if not all_items:
            return

        # Calculate the longest.
        max_length = max(map(get_length, all_items)) + 1

        # World per line?
        term_width = self.get_size().columns - margin_left
        words_per_line = int(max(term_width / max_length, 1))

        # Iterate through items.
        margin = ' ' * margin_left
        line = [ margin ]
        for i, j in enumerate(all_items):
            # Print command and spaces
            line.append(get_text(j))

            # When we reached the max items on this line, yield line.
            if (i+1) % words_per_line == 0:
                yield ''.join(line)
                line = [ margin ]
            else:
                # Pad with whitespace
                line.append(' ' * (max_length - get_length(j)))

        yield ''.join(line)
