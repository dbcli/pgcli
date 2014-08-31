"""
Renders the command line on the console.
(Redraws parts of the input line that were changed.)
"""
from __future__ import unicode_literals
import sys
import six

from .utils import get_size
from .libs.wcwidth import wcwidth
from collections import defaultdict

from pygments.formatters.terminal256 import Terminal256Formatter, EscapeSequence
from pygments.style import Style
from pygments.token import Token

# Global variable to keep the colour table in memory.
_tf = Terminal256Formatter()

__all__ = (
    'Renderer',
)

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

    @staticmethod
    def CURSOR_GOTO(row=0, column=0):
        """ Move cursor position. """
        return '\x1b[%i;%iH' % (row, column)

    @staticmethod
    def CURSOR_UP(amount):
        if amount == 1:
            return '\x1b[A'
        else:
            return '\x1b[%iA' % amount

    @staticmethod
    def CURSOR_DOWN(amount):
        if amount == 1:
            return '\x1b[B'
        else:
            return '\x1b[%iB' % amount

    @staticmethod
    def CURSOR_FORWARD(amount):
        if amount == 1:
            return '\x1b[C'
        else:
            return '\x1b[%iC' % amount

    @staticmethod
    def CURSOR_BACKWARD(amount):
        if amount == 1:
            return '\x1b[D'
        else:
            return '\x1b[%iD' % amount


class Char(object):
    __slots__ = ('char', 'style', 'z_index')

    def __init__(self, char=' ', style=None, z_index=0):
        self.char = char
        self.style = style # TODO: maybe we should still use `token` instead of
                           #       `style` and use the actual style in the last step of the renderer.
        self.z_index = z_index

    def output(self):
        """ Return the output to write this character to the terminal. """
        style = self.style

        if style:
            e = EscapeSequence(
                    fg=(_tf._color_index(style['color']) if style['color'] else None),
                    bg=(_tf._color_index(style['bgcolor']) if style['bgcolor'] else None),
                    bold=style.get('bold', False),
                    underline=style.get('underline', False))

            return ''.join([
                    e.color_string(),
                    self.char,
                    e.reset_string()
                ])
        else:
            return self.char

    @property
    def width(self):
        # We use the `max(0, ...` because some non printable control
        # characters, like e.g. Ctrl-underscore get a -1 wcwidth value.
        # It can be possible that these characters end up in the input text.
        return max(0, wcwidth(self.char))


class Screen(object):
    """
    Two dimentional buffer for the output.

    :param style: Pygments style.
    :param grayed: True when all tokes should be replaced by `Token.Aborted`
    """
    def __init__(self, style, columns, grayed=False):
        self._buffer = defaultdict(lambda: defaultdict(Char))
        self._cursor_mappings = { } # Map `source_string_index` of input data to (row, col) screen output.
        self._x = 0
        self._y = 0
        self._max_y = 0

        self.columns = columns
        self._style = style
        self._grayed = grayed
        self._left_margin_func = None

        self._cursor_x = 0
        self._cursor_y = 0

    @property
    def current_height(self):
        return max(self._buffer.keys())

    def get_cursor_position(self):
        return self._cursor_y, self._cursor_x

    def set_left_margin(self, func):
        """
        Set a function that returns a list of (token,text) tuples to be
        inserted after every newline.
        """
        self._left_margin_func = func

    def write_char(self, char, token, string_index=None,
                    set_cursor_position=False, z_index=False):
        """
        Write char to current cursor position and move cursor.
        """
        assert len(char) == 1

        char_width = wcwidth(char)

        # In case of a double width character, if there is no more place left
        # at this line, go first to the following line.
        if self._x + char_width > self.columns:
            self._y += 1
            self._x = 0

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

            if self._left_margin_func:
                self._left_margin_func(self._y)
                #self.write_highlighted(self._left_margin_func())

        # Insertion of a 'visible' character.
        else:
            self.write_at_pos(self._y, self._x, char, token, z_index=z_index)

            # Move cursor position
            if self._x + char_width >= self.columns:
                self._y += 1
                self._x = 0
            else:
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
        if y < self.columns:
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

    def output(self):
        """
        Return (string, last_y, last_x) tuple.
        """
        result = []

        # Disable autowrap
        result.append('\x1b[?7l')

        rows = max(self._buffer.keys()) + 1
        c = 0

        for y, r in enumerate(range(0, rows)):
            line_data = self._buffer[r]
            if line_data:
                cols = max(line_data.keys()) + 1

                c = 0
                while c < cols:
                    result.append(line_data[c].output())
                    c += (line_data[c].width or 1)

            if y != rows - 1:
                result.append(TerminalCodes.CRLF)

        # Enable autowrap again.
        result.append('\x1b[?7h')

        return ''.join(result), y, min(c, self.columns - 1)


class Renderer(object):
    screen_cls = Screen

    def __init__(self, prompt_factory=None, stdout=None, style=None):
        self.prompt_factory = prompt_factory
        self._stdout = (stdout or sys.stdout)
        self._style = style or Style

        self.reset()

    def reset(self):
        # Reset position
        self._cursor_line = 0

        # Remember height of the screen between renderers. This way,
        # a toolbar can remain at the 'bottom' position.
        self._last_screen_height = 0

    def get_cols(self):
        rows, cols = get_size(self._stdout.fileno())
        return cols

    def _render_to_str(self, render_context):
        output = []
        write = output.append

        # Move the cursor to the first line that was printed before
        # and erase everything below it.
        if self._cursor_line:
            write(TerminalCodes.CURSOR_UP(self._cursor_line))

        write(TerminalCodes.CARRIAGE_RETURN)
        write(TerminalCodes.ERASE_DOWN)

        # Generate the output of the new screen.
        screen = self.screen_cls(style=self._style, columns=self.get_cols(),
                grayed=render_context.abort)

        prompt = self.prompt_factory(render_context)
        prompt.write_to_screen(screen, self._last_screen_height)

        o, last_y, last_x = screen.output()
        write(o)

        # Move cursor to correct position.
        if render_context.accept or render_context.abort:
            self._cursor_line = 0
            write(TerminalCodes.CRLF)
        else:
            cursor_y, cursor_x = screen.get_cursor_position()

            # Up
            if last_y - cursor_y:
                write(TerminalCodes.CURSOR_UP(last_y - cursor_y))

            # Horizontal
                    # Note the '+1' is required to make sure that we first
                    # really are back at the left margin. In some terminals
                    # like gnome-terminal, it looks like if we disabled line
                    # wrap but still write until the rigth margin, the cursor
                    # could end up just past the right margin.
            write(TerminalCodes.CURSOR_BACKWARD(last_x + 1))
            write(TerminalCodes.CURSOR_FORWARD(cursor_x))

            self._cursor_line = cursor_y

        self._last_screen_height = max(self._last_screen_height, screen.current_height)

        return ''.join(output)

    def render(self, render_context):
        out = self._render_to_str(render_context)
        self._stdout.write(out)
        self._stdout.flush()

    def render_completions(self, completions):
        self._stdout.write(TerminalCodes.CRLF)
        for line in self._in_columns([ c.display for c in completions ]):
            self._stdout.write('%s\r\n' % line)

        # Reset position
        self._cursor_line = 0

        return
        if many: # TODO: Implement paging
            'Display all %i possibilities? (y on n)'

    def clear(self):
        """
        Clear screen and go to 0,0
        """
        self._stdout.write(TerminalCodes.ERASE_SCREEN)
        self._stdout.write(TerminalCodes.CURSOR_GOTO(0, 0))

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
        term_width = self.get_cols() - margin_left
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
