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
    'Renderer',
)

_Point = namedtuple('Point', 'y x')
_Size = namedtuple('Size', 'rows columns')


#: If True: write the output of the renderer also to the following file. This
#: is very useful for debugging. (e.g.: to see that we don't write more bytes
#: than required.)
_DEBUG_RENDER_OUTPUT = False
_DEBUG_RENDER_OUTPUT_FILENAME = '/tmp/prompt-toolkit-render-output'


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
    __slots__ = ('char', 'style', 'z_index')

    def __init__(self, char=' ', style=None, z_index=0):
        self.char = char
        self.style = style # TODO: maybe we should still use `token` instead of
                           #       `style` and use the actual style in the last step of the renderer.
        self.z_index = z_index

    def output(self, last_char=None):
        """ Return the output to write this character to the terminal. """
        style = self.style

        # If the last printed charact has the same styling, we don't have to
        # output the style.
        if last_char and last_char.style == self.style:
            return self.char

        if style:
            e = EscapeSequence(
                    fg=(_tf._color_index(style['color']) if style['color'] else None),
                    bg=(_tf._color_index(style['bgcolor']) if style['bgcolor'] else None),
                    bold=style.get('bold', False),
                    underline=style.get('underline', False))

            return ''.join([
                    TerminalCodes.RESET_ATTRIBUTES,
                    e.color_string(),
                    self.char,
                ])
        else:
            return ''.join([
                TerminalCodes.RESET_ATTRIBUTES,
                self.char
                ])

    @property
    def width(self):
        # We use the `max(0, ...` because some non printable control
        # characters, like e.g. Ctrl-underscore get a -1 wcwidth value.
        # It can be possible that these characters end up in the input text.
        return max(0, wcwidth(self.char))

    @property
    def _background(self):
        if self.style:
            return self.style.get('bgcolor', None)

    def __eq__(self, other):
        """
        Test whether two `Char` instances are equal.
        """
        # Spaces are always equal, whathever their styling.
        if self.char == other.char and self.char == ' ' and self._background == other._background:
            return True

        # We ignore z-index, that does not matter if things get painted.
        return self.char == other.char and self.style == other.style


class Screen(object):
    """
    Two dimentional buffer for the output.

    :param style: Pygments style.
    :param grayed: True when all tokes should be replaced by `Token.Aborted`
    """
    def __init__(self, style, size, grayed=False):
        self._buffer = defaultdict(lambda: defaultdict(Char))
        self._cursor_mappings = { } # Map `source_string_index` of input data to (row, col) screen output.
        self._x = 0
        self._y = 0
        self._max_y = 0

        self.size = size
        self._style = style
        self._grayed = grayed
        self._left_margin_func = lambda linenr, is_new_line: None

        self._cursor_x = 0
        self._cursor_y = 0
        self._line_number = 1

    @property
    def current_height(self):
        if not self._buffer:
            return 1
        else:
            return max(self._buffer.keys()) + 1

    def get_cursor_position(self):
        return self._cursor_y, self._cursor_x

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

        char_width = wcwidth(char)

        # In case there is no more place left at this line, go first to the
        # following line. (Also in case of double-width characters.)
        if self._x + char_width > self.size.columns:
            self._y += 1
            self._x = 0
            self._left_margin_func(self._line_number, False)

        insert_pos = self._y, self._x

        if string_index is not None:
            self._cursor_mappings[string_index] = insert_pos

        if set_cursor_position:
            self._cursor_x = self._x
            self._cursor_y = self._y

        # If grayed, replace token
        if self._grayed:
            token = Token.Aborted

        # Insertion of newline
        if char == '\n':
            self._y += 1
            self._x = 0
            self._line_number += 1
            self._left_margin_func(self._line_number, True)

        # Insertion of a 'visible' character.
        else:
            self.write_at_pos(self._y, self._x, char, token, z_index=z_index)

            # Move cursor position
            self._x += char_width

        return insert_pos

    def write_at_pos(self, y, x, char, token, z_index=0):
        """
        Write character at position (y, x).
        (Truncate when character is outside margin.)
        """
        # Get style
        try:
            style = self._style.style_for_token(token)
        except KeyError:
            style = None

        # Add char to buffer
        if y < self.size.columns:
            if z_index >= self._buffer[y][x].z_index:
                self._buffer[y][x] = Char(char=char, style=style, z_index=z_index)

    def write_highlighted_at_pos(self, y, x, data, z_index=0):
        """
        Write (Token, text) tuples at position (y, x).
        (Truncate when character is outside margin.)
        """
        for token, text in data:
            for c in text:
                self.write_at_pos(y, x, c, token, z_index=z_index)
                x += wcwidth(c)

    def write_highlighted(self, data):
        """
        Write (Token, text) tuples to the screen.
        """
        for token, text in data:
            for c in text:
                self.write_char(c, token=token)

    def output(self, current_pos, previous_screen=None, last_char=None, accept_or_abort=False):
        """
        Create diff of this screen with the previous screen.
        """
        last_char = [last_char] # nonlocal
        result = []
        write = result.append

        def move_cursor(new):
            if current_pos.x >= self.size.columns - 1:
                write(TerminalCodes.CARRIAGE_RETURN)
                write(TerminalCodes.CURSOR_FORWARD(new.x))
            elif new.x < current_pos.x or current_pos.x >= self.size.columns - 1:
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

        # Disable autowrap
        if not previous_screen:
            write(TerminalCodes.DISABLE_AUTOWRAP)
            write(TerminalCodes.RESET_ATTRIBUTES)

        # Get height of the screen.
        # (current_height changes as we loop over _buffer, so remember the current value.)
        current_height = self.current_height

        if previous_screen:
            row_count = max(self.current_height, previous_screen.current_height)
        else:
            row_count = self.current_height

        # When the previous screen has a different width, redraw everything anyway.
        if previous_screen and previous_screen.size != self.size:
            current_pos = move_cursor(_Point(0, 0))
            write(TerminalCodes.RESET_ATTRIBUTES)
            write(TerminalCodes.ERASE_DOWN)
            previous_screen = None

        # Loop over the rows.
        c = 0

        for y, r in enumerate(range(0, row_count)):
            new_row = self._buffer[r]
            if previous_screen:
                previous_row = previous_screen._buffer[r]

            if new_row:
                new_max_line_len = max(new_row.keys())
            else:
                new_max_line_len = 0

            if previous_screen:
                if previous_row:
                    previous_max_line_len = max(previous_row.keys())
                else:
                    previous_max_line_len = 0

            # Loop over the columns.
            c = 0
            while c < new_max_line_len + 1:
                char_width = (new_row[c].width or 1)

                if not previous_screen or not (new_row[c] == previous_row[c]):
                    current_pos = move_cursor(_Point(y=y, x=c))
                    write(new_row[c].output(last_char[0]))
                    last_char[0] = new_row[c]
                    current_pos = current_pos._replace(x=current_pos.x + char_width)

                c += char_width

            # If the new line is shorter, trim it
            if previous_screen and new_max_line_len < previous_max_line_len:
                current_pos = move_cursor(_Point(y=y, x=new_max_line_len+1))
                write(TerminalCodes.RESET_ATTRIBUTES)
                write(TerminalCodes.ERASE_END_OF_LINE)
                last_char[0] = None # Forget last char after resetting attributes.

        # Move cursor:
        if accept_or_abort:
            current_pos = move_cursor(_Point(y=current_height, x=0))
            write(TerminalCodes.CRLF)
            write(TerminalCodes.ERASE_DOWN)
        else:
            cursor_y, cursor_x = self.get_cursor_position()
            current_pos = move_cursor(_Point(y=cursor_y, x=cursor_x))

        if accept_or_abort:
            write(TerminalCodes.RESET_ATTRIBUTES)
            write(TerminalCodes.ENABLE_AUTOWRAP)

        # If the last printed character has a background color, always reset.
        # (Many terminals give weird artifacs on resize events when there is an
        # active background color.)
        if last_char[0] and last_char[0]._background:
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
        self._cursor_pos = _Point(x=0, y=0)

        # Remember the last screen instance between renderers. This way,
        # we can create a `diff` between two screens and only output the
        # difference. It's also to remember the last height. (To show for
        # instance a toolbar at the bottom position.)
        self._last_screen = None
        self._last_char = None

    def get_size(self):
        rows, columns = get_size(self._stdout.fileno())
        return _Size(rows=rows, columns=columns)

    def render_to_str(self, abort=False, accept=False):
        # Generate the output of the new screen.
        screen = self.screen_cls(style=self._style, size=self.get_size(), grayed=abort)

        self.prompt.write_to_screen(screen, self._last_screen.current_height if self._last_screen else 0,
                abort=abort, accept=accept)

        output, self._cursor_pos, self._last_char = screen.output(self._cursor_pos,
                self._last_screen, self._last_char, accept or abort)
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
