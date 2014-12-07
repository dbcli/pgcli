"""
Renders the command line on the console.
(Redraws parts of the input line that were changed.)
"""
from __future__ import unicode_literals
import sys
import six
import errno

from collections import defaultdict, namedtuple

from pygments.style import Style
from pygments.token import Token

from .utils import get_cwidth

if sys.platform == 'win32':
    from .terminal.win32_output import Win32Output as Output
else:
    from .terminal.vt100_output import Vt100_Output as Output


__all__ = (
    'Point',
    'Renderer',
    'Screen',
)


Point = namedtuple('Point', 'y x')
Size = namedtuple('Size', 'rows columns')


class Char(object):
    __slots__ = ('char', 'token', 'z_index')

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

    def __init__(self, char=' ', token=Token, z_index=0):
        # If this character has to be displayed otherwise, take that one.
        char = self.display_mappings.get(char, char)

        self.char = char
        self.token = token
        self.z_index = z_index

    def get_width(self):
        # We use the `max(0, ...` because some non printable control
        # characters, like e.g. Ctrl-underscore get a -1 wcwidth value.
        # It can be possible that these characters end up in the input text.
        char = self.char
        if len(char) == 1:
            return max(0, get_cwidth(char))
        else:
            return max(0, sum(get_cwidth(c) for c in char))

    def __repr__(self):
        return 'Char(%r, %r, %r)' % (self.char, self.token, self.z_index)


class Screen(object):
    """
    Two dimentional buffer for the output.

    :param style: Pygments style.
    :param grayed: True when all tokes should be replaced by `Token.Aborted`
    """
    def __init__(self, size):
        self._buffer = defaultdict(lambda: defaultdict(Char))
        self._cursor_mappings = {}  # Map `source_string_index` of input data to (row, col) screen output.
        self._x = 0
        self._y = 0

        self.size = size

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

    def write_char(self, char, token, string_index=None,
                   set_cursor_position=False, z_index=False):
        """
        Write char to current cursor position and move cursor.
        """
        assert len(char) == 1

        char_obj = Char(char, token, z_index)
        char_width = char_obj.get_width()

        # In case there is no more place left at this line, go first to the
        # following line. (Also in case of double-width characters.)
        if self._x + char_width > self.size.columns:
            self._y += 1
            self._x = 0

        insert_pos = self._y, self._x  # XXX: make a Point of this?

        if string_index is not None:
            self._cursor_mappings[string_index] = insert_pos

        if set_cursor_position:
            self.cursor_position = Point(y=self._y, x=self._x)

        # Insertion of newline
        if char == '\n':
            self._y += 1
            self._x = 0
            self._line_number += 1

        # Insertion of a 'visible' character.
        else:
            if char_obj.z_index >= self._buffer[self._y][self._x].z_index:
                self._buffer[self._y][self._x] = char_obj

            # When we have a double width character, store this byte in the
            # second cell. So that if this character gets deleted afterwarsd,
            # the ``output_screen_diff`` will notice that this byte is also
            # gone and redraw both cells.
            if char_width > 1:
                self._buffer[self._y][self._x+1] = Char(six.unichr(0))

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

        :param data: Enumerable of (Token, text) tuples.
        """
        for token, text in data:
            for c in text:
                char_obj = Char(c, token, z_index)
                self.write_at_pos(y, x, char_obj)
                x += char_obj.get_width()

    def write_highlighted(self, data):
        """
        Write (Token, text) tuples to the screen.
        """
        for token, text in data:
            for c in text:
                self.write_char(c, token=token)


def output_screen_diff(output, screen, current_pos, previous_screen=None, last_char=None, accept_or_abort=False, style=None, grayed=False):
    """
    Create diff of this screen with the previous screen.
    """
    #: Remember the last printed character.
    last_char = [last_char]  # nonlocal
    background_turned_on = [False]  # Nonlocal

    #: Variable for capturing the output.
    write = output.write

    def move_cursor(new):
        current_x, current_y = current_pos.x, current_pos.y

        if new.y > current_y:
            # Use newlines instead of CURSOR_DOWN, because this meight add new lines.
            # CURSOR_DOWN will never create new lines at the bottom.
            # Also reset attributes, otherwise the newline could draw a
            # background color.
            output.reset_attributes()
            write('\r\n' * (new.y - current_y))
            current_x = 0
            output.cursor_forward(new.x)
            last_char[0] = None  # Forget last char after resetting attributes.
            return new
        elif new.y < current_y:
            output.cursor_up(current_y - new.y)

        if current_x >= screen.size.columns - 1:
            write('\r')
            output.cursor_forward(new.x)
        elif new.x < current_x or current_x >= screen.size.columns - 1:
            output.cursor_backward(current_x - new.x)
        elif new.x > current_x:
            output.cursor_forward(new.x - current_x)

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
                output.set_attributes(style['color'], style['bgcolor'],
                                      bold=style.get('bold', False),
                                      underline=style.get('underline', False))

                # If we print something with a background color, remember that.
                background_turned_on[0] = bool(style['bgcolor'])
            else:
                # Reset previous style and output.
                output.reset_attributes()

            write(char.char)

        last_char[0] = char


    # Disable autowrap
    if not previous_screen:
        output.disable_autowrap()
        output.reset_attributes()

    # When the previous screen has a different size, redraw everything anyway.
    if not previous_screen or previous_screen.size != screen.size:
        current_pos = move_cursor(Point(0, 0))
        output.reset_attributes()
        output.erase_down()

        previous_screen = Screen(screen.size)

    # Get height of the screen.
    # (current_height changes as we loop over _buffer, so remember the current value.)
    current_height = screen.current_height

    # Loop over the rows.
    row_count = max(screen.current_height, previous_screen.current_height)
    c = 0  # Column counter.

    for y, r in enumerate(range(0, row_count)):
        new_row = screen._buffer[r]
        previous_row = previous_screen._buffer[r]

        new_max_line_len = max(new_row.keys()) if new_row else 0
        previous_max_line_len = max(previous_row.keys()) if previous_row else 0

        # Loop over the columns.
        c = 0
        while c < new_max_line_len + 1:
            char_width = (new_row[c].get_width() or 1)

            if not chars_are_equal(new_row[c], previous_row[c]):
                current_pos = move_cursor(Point(y=y, x=c))
                output_char(new_row[c])
                current_pos = current_pos._replace(x=current_pos.x + char_width)

            c += char_width

        # If the new line is shorter, trim it
        if previous_screen and new_max_line_len < previous_max_line_len:
            current_pos = move_cursor(Point(y=y, x=new_max_line_len+1))
            output.reset_attributes()
            output.erase_end_of_line()
            last_char[0] = None  # Forget last char after resetting attributes.

    # Move cursor:
    if accept_or_abort:
        current_pos = move_cursor(Point(y=current_height, x=0))
        output.erase_down()
    else:
        current_pos = move_cursor(screen.get_cursor_position())

    if accept_or_abort:
        output.reset_attributes()
        output.enable_autowrap()

    # If the last printed character has a background color, always reset.
    # (Many terminals give weird artifacs on resize events when there is an
    # active background color.)
    if background_turned_on[0]:
        output.reset_attributes()
        last_char[0] = None

    return current_pos, last_char[0]


class Renderer(object):
    """
    Typical usage:

    ::

        r = Renderer(layout)
        r.render(Render_context(...))
    """
    def __init__(self, layout=None, stdout=None, style=None):
        self.layout = layout
        self.stdout = stdout or sys.stdout
        self._style = style or Style
        self._last_screen = None

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

        #: Space from the top of the layout, until the bottom of the terminal.
        #: We don't know this until a `report_absolute_cursor_row` call.
        self._min_available_height = 0

        # In case of Windown, also make sure to scroll to the current cursor
        # position.
        if sys.platform == 'win32':
            Output(self.stdout).scroll_buffer_to_prompt()

    def _write_and_flush(self, data):
        """
        Write to output stream and flush.
        """
        try:
            self.stdout.write(data)
            self.stdout.flush()
        except IOError as e:
            if e.args and e.args[0] == errno.EINTR:
                # Interrupted system call. Can happpen in case of a window
                # resize signal. (Just ignore. The resize handler will render
                # again anyway.)
                pass
            else:
                raise

    def request_absolute_cursor_position(self):
        """
        Get current cursor position.
        For vt100: Do CPR request. (answer will arrive later.)
        For win32: Do API call. (Answer comes immediately.)
        """
        # Only do this request when the cursor is at the top row. (after a
        # clear or reset). We will rely on that in `report_absolute_cursor_row`.
        assert self._cursor_pos.y == 0

        # For Win32, we have an API call to get the number of rows below the
        # cursor.
        if sys.platform == 'win32':
            self._min_available_height = Output(self.stdout).get_rows_below_cursor_position()
        else:
            # Asks for a cursor position report (CPR).
            self._write_and_flush('\x1b[6n')

    def report_absolute_cursor_row(self, row):
        """
        To be called when we know the absolute cursor position.
        (As an answer of a "Cursor Position Request" response.)
        """
        # Calculate the amount of rows from the cursor position until the
        # bottom of the terminal.
        total_rows = Output(self.stdout).get_size().rows
        rows_below_cursor = total_rows - row + 1

        # Set the
        self._min_available_height = rows_below_cursor

    def render(self, cli):
        """
        Render the current interface to the output.
        """
        output = Output(self.stdout)

        # Create screen and write layout to it.
        screen = Screen(size=output.get_size())

        height = self._last_screen.current_height if self._last_screen else 0
        height = max(self._min_available_height, height)
        self.layout.write_to_screen(cli, screen, height)

        accept_or_abort = cli.is_exiting or cli.is_aborting or cli.is_returning

        # Process diff and write to output.
        output_buffer = []
        self._cursor_pos, self._last_char = output_screen_diff(
            output, screen, self._cursor_pos,
            self._last_screen, self._last_char, accept_or_abort,
            style=self._style, grayed=cli.is_aborting,
            )
        self._last_screen = screen

        output.flush()

    def erase(self):
        """
        Hide all output and put the cursor back at the first line. This is for
        instance used for running a system command (while hiding the CLI) and
        later resuming the same CLI.)
        """
        output = Output(self.stdout)

        output.cursor_backward(self._cursor_pos.x)
        output.cursor_up(self._cursor_pos.y)
        output.erase_down()
        output.reset_attributes()
        output.flush()

        self.reset()

    def clear(self):
        """
        Clear screen and go to 0,0
        """
        # Erase current output first.
        self.erase()

        # Send "Erase Screen" command and go to (0, 0).
        output = Output(self.stdout)

        output.erase_screen()
        output.cursor_goto(0, 0)
        output.flush()

        self.request_absolute_cursor_position()
