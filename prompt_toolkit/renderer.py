"""
Renders the command line on the console.
(Redraws parts of the input line that were changed.)
"""
from __future__ import unicode_literals

from pygments.style import Style
from pygments.token import Token
from prompt_toolkit.layout.screen import Point, Screen, WritePosition
from prompt_toolkit.layout.mouse_handlers import MouseHandlers
from prompt_toolkit.output import Output
from prompt_toolkit.utils import is_windows
from prompt_toolkit.filters import to_cli_filter

__all__ = (
    'Renderer',
    'print_tokens',
)


class _StyleForTokenCache(dict):
    """
    A cache structure that maps Pygments Tokens to their style objects.
    """
    def __init__(self, style):
        self.style = style

    def __missing__(self, token):
        try:
            result = self.style.style_for_token(token)
        except KeyError:
            result = None

        self[token] = result
        return result


def output_screen_diff(output, screen, current_pos, previous_screen=None, last_char=None,
                       is_done=False, style=None, width=0, previous_width=0):  # XXX: drop is_done
    """
    Render the diff between this screen and the previous screen.

    This takes two `Screen` instances. The one that represents the output like
    it was during the last rendering and one that represents the current
    output raster. Looking at these two `Screen` instances, this function will
    render the difference by calling the appropriate methods of the `Output`
    object that only paint the changes to the terminal.

    This is some performance-critical code which is heavily optimized.
    Don't change things without profiling first.

    :param current_pos: Current cursor position.
    :param last_char: `Char` instance that represents the output attributes of
            the last drawn character. (Color/attributes.)
    :param style: Pygments stylesheet.
    :param width: The width of the terminal.
    :param prevous_width: The width of the terminal during the last rendering.
    """
    #: Remember the last printed character.
    last_char = [last_char]  # nonlocal
    background_turned_on = [False]  # Nonlocal

    #: Variable for capturing the output.
    write = output.write

    # Create locals for the most used output methods.
    # (Save expensive attribute lookups.)
    _output_set_attributes = output.set_attributes
    _output_reset_attributes = output.reset_attributes
    _output_cursor_forward = output.cursor_forward
    _output_cursor_up = output.cursor_up
    _output_cursor_backward = output.cursor_backward

    def reset_attributes():
        " Wrapper around Output.reset_attributes. "
        _output_reset_attributes()
        last_char[0] = None  # Forget last char after resetting attributes.

    def move_cursor(new):
        " Move cursor to this `new` point. Returns the given Point. "
        current_x, current_y = current_pos.x, current_pos.y

        if new.y > current_y:
            # Use newlines instead of CURSOR_DOWN, because this meight add new lines.
            # CURSOR_DOWN will never create new lines at the bottom.
            # Also reset attributes, otherwise the newline could draw a
            # background color.
            reset_attributes()
            write('\r\n' * (new.y - current_y))
            current_x = 0
            _output_cursor_forward(new.x)
            return new
        elif new.y < current_y:
            _output_cursor_up(current_y - new.y)

        if current_x >= width - 1:
            write('\r')
            _output_cursor_forward(new.x)
        elif new.x < current_x or current_x >= width - 1:
            _output_cursor_backward(current_x - new.x)
        elif new.x > current_x:
            _output_cursor_forward(new.x - current_x)

        return new

    style_for_token = _StyleForTokenCache(style)

    def output_char(char):
        """
        Write the output of this character.
        """
        # If the last printed character has the same token, it also has the
        # same style, so we don't output it.
        if last_char[0] and last_char[0].token == char.token:
            write(char.char)
        else:
            style = style_for_token[char.token]

            if style:
                _output_set_attributes(style['color'], style['bgcolor'],
                                       bold=style.get('bold', False),
                                       underline=style.get('underline', False))

                # If we print something with a background color, remember that.
                background_turned_on[0] = bool(style['bgcolor'])
            else:
                # Reset previous style and output.
                reset_attributes()

            write(char.char)

        last_char[0] = char

    # Disable autowrap
    if not previous_screen:
        output.disable_autowrap()
        reset_attributes()

    # When the previous screen has a different size, redraw everything anyway.
    # Also when we are done. (We meight take up less rows, so clearing is important.)
    if is_done or not previous_screen or previous_width != width:  # XXX: also consider height??
        current_pos = move_cursor(Point(0, 0))
        reset_attributes()
        output.erase_down()

        previous_screen = Screen()

    # Get height of the screen.
    # (height changes as we loop over _buffer, so remember the current value.)
    current_height = screen.height

    # Loop over the rows.
    row_count = max(screen.height, previous_screen.height)
    c = 0  # Column counter.

    for y, r in enumerate(range(0, row_count)):
        new_row = screen._buffer[r]
        previous_row = previous_screen._buffer[r]

        new_max_line_len = max(new_row.keys()) if new_row else 0
        previous_max_line_len = max(previous_row.keys()) if previous_row else 0

        # Loop over the columns.
        c = 0
        while c < new_max_line_len + 1:
            new_char = new_row[c]
            old_char = previous_row[c]
            char_width = (new_char.width or 1)

            # When the old and new character at this position are different,
            # draw the output. (Because of the performance, we don't call
            # `Char.__ne__`, but inline the same expression.)
            if new_char.char != old_char.char or new_char.token != old_char.token:
                current_pos = move_cursor(Point(y=y, x=c))
                output_char(new_char)
                current_pos = current_pos._replace(x=current_pos.x + char_width)

            c += char_width

        # If the new line is shorter, trim it
        if previous_screen and new_max_line_len < previous_max_line_len:
            current_pos = move_cursor(Point(y=y, x=new_max_line_len+1))
            reset_attributes()
            output.erase_end_of_line()

    # Correctly reserve vertical space as required by the layout.
    # When this is a new screen (drawn for the first time), or for some reason
    # higher than the previous one. Move the cursor once to the bottom of the
    # output. That way, we're sure that the terminal scrolls up, even when the
    # lower lines of the canvas just contain whitespace.

    # The most obvious reason that we actually want this behaviour is the avoid
    # the artifact of the input scrolling when the completion menu is shown.
    # (If the scrolling is actually wanted, the layout can still be build in a
    # way to behave that way by setting a dynamic height.)
    if screen.height > previous_screen.height:
        current_pos = move_cursor(Point(y=screen.height - 1, x=0))

    # Move cursor:
    if is_done:
        current_pos = move_cursor(Point(y=current_height, x=0))
        output.erase_down()
    else:
        current_pos = move_cursor(screen.cursor_position)

    if is_done:
        reset_attributes()
        output.enable_autowrap()

    # If the last printed character has a background color, always reset.
    # (Many terminals give weird artifacs on resize events when there is an
    # active background color.)
    if background_turned_on[0]:
        reset_attributes()

    return current_pos, last_char[0]


class HeightIsUnknownError(Exception):
    " Information unavailable. Did not yet receive the CPR response. "


class Renderer(object):
    """
    Typical usage:

    ::

        output = Vt100_Output.from_pty(sys.stdout)
        r = Renderer(output)
        r.render(cli, layout=..., style=...)
    """
    def __init__(self, output, use_alternate_screen=False, mouse_support=False):
        assert isinstance(output, Output)

        self.output = output
        self.use_alternate_screen = use_alternate_screen
        self.mouse_support = to_cli_filter(mouse_support)

        self._in_alternate_screen = False
        self._mouse_support_enabled = False

        self.reset(_scroll=True)

    def reset(self, _scroll=False):
        # Reset position
        self._cursor_pos = Point(x=0, y=0)

        # Remember the last screen instance between renderers. This way,
        # we can create a `diff` between two screens and only output the
        # difference. It's also to remember the last height. (To show for
        # instance a toolbar at the bottom position.)
        self._last_screen = None
        self._last_size = None
        self._last_char = None
        self._last_style = None  # When the style changes, we have to do a full
                                 # redraw as well.

        # Default MouseHandlers. (Just empty.)
        self.mouse_handlers = MouseHandlers()

        # Remember the last title. Only set the title when it changes.
        self._last_title = None

        #: Space from the top of the layout, until the bottom of the terminal.
        #: We don't know this until a `report_absolute_cursor_row` call.
        self._min_available_height = 0

        # In case of Windown, also make sure to scroll to the current cursor
        # position. (Only when rendering the first time.)
        if is_windows() and _scroll:
            self.output.scroll_buffer_to_prompt()

        # Quit alternate screen.
        if self._in_alternate_screen:
            self.output.quit_alternate_screen()
            self.output.flush()
            self._in_alternate_screen = False

        # Disable mouse support.
        if self._mouse_support_enabled:
            self.output.disable_mouse_support()
            self._mouse_support_enabled = False

        # Flush output. `disable_mouse_support` needs to write to stdout.
        self.output.flush()

    @property
    def height_is_known(self):
        """
        True when the height from the cursor until the bottom of the terminal
        is known. (It's often nicer to draw bottom toolbars only if the height
        is known, in order to avoid flickering when the CPR response arrives.)
        """
        return self.use_alternate_screen or self._min_available_height > 0 or \
            is_windows()  # On Windows, we don't have to wait for a CPR.

    @property
    def rows_above_layout(self):
        """
        Return the number of rows visible in the terminal above the layout.
        """
        if self._in_alternate_screen:
            return 0
        elif self._min_available_height > 0:
            total_rows = self.output.get_size().rows
            last_screen_height = self._last_screen.height if self._last_screen else 0
            return total_rows - max(self._min_available_height, last_screen_height)
        else:
            raise HeightIsUnknownError('Rows above layout is unknown.')

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
        if is_windows():
            self._min_available_height = self.output.get_rows_below_cursor_position()
        else:
            if self.use_alternate_screen:
                self._min_available_height = self.output.get_size().rows
            else:
                # Asks for a cursor position report (CPR).
                self.output.ask_for_cpr()

    def report_absolute_cursor_row(self, row):
        """
        To be called when we know the absolute cursor position.
        (As an answer of a "Cursor Position Request" response.)
        """
        # Calculate the amount of rows from the cursor position until the
        # bottom of the terminal.
        total_rows = self.output.get_size().rows
        rows_below_cursor = total_rows - row + 1

        # Set the
        self._min_available_height = rows_below_cursor

    def render(self, cli, layout, style=None, is_done=False):
        """
        Render the current interface to the output.

        :param is_done: When True, put the cursor at the end of the interface. We
                won't print any changes to this part.
        """
        style = style or Style
        output = self.output

        # Enter alternate screen.
        if self.use_alternate_screen and not self._in_alternate_screen:
            self._in_alternate_screen = True
            output.enter_alternate_screen()

        # Enable/disable mouse support.
        needs_mouse_support = self.mouse_support(cli)

        if needs_mouse_support and not self._mouse_support_enabled:
            output.enable_mouse_support()
            self._mouse_support_enabled = True

        elif not needs_mouse_support and self._mouse_support_enabled:
            output.disable_mouse_support()
            self._mouse_support_enabled = False

        # Create screen and write layout to it.
        size = output.get_size()
        screen = Screen()
        mouse_handlers = MouseHandlers()

        if is_done:
            height = 0  # When we are done, we don't necessary want to fill up until the bottom.
        else:
            height = self._last_screen.height if self._last_screen else 0
            height = max(self._min_available_height, height)

        # When te size changes, don't consider the previous screen.
        if self._last_size != size:
            self._last_screen = None

        # When we render using another style, do a full repaint. (Forget about
        # the previous rendered screen.)
        # (But note that we still use _last_screen to calculate the height.)
        if style != self._last_style:
            self._last_screen = None
        self._last_style = style

        layout.write_to_screen(cli, screen, mouse_handlers, WritePosition(
            xpos=0,
            ypos=0,
            width=size.columns,
            height=(size.rows if self.use_alternate_screen else height),
            extended_height=size.rows,
        ))

        # When grayed. Replace all tokens in the new screen.
        if cli.is_aborting or cli.is_exiting:
            screen.replace_all_tokens(Token.Aborted)

        # Process diff and write to output.
        self._cursor_pos, self._last_char = output_screen_diff(
            output, screen, self._cursor_pos,
            self._last_screen, self._last_char, is_done,
            style=style,
            width=size.columns,
            previous_width=(self._last_size.columns if self._last_size else 0),
            )
        self._last_screen = screen
        self._last_size = size
        self.mouse_handlers = mouse_handlers

        # Write title if it changed.
        new_title = cli.terminal_title

        if new_title != self._last_title:
            if new_title is None:
                self.output.clear_title()
            else:
                self.output.set_title(new_title)
            self._last_title = new_title

        output.flush()

    def erase(self):
        """
        Hide all output and put the cursor back at the first line. This is for
        instance used for running a system command (while hiding the CLI) and
        later resuming the same CLI.)
        """
        output = self.output

        output.cursor_backward(self._cursor_pos.x)
        output.cursor_up(self._cursor_pos.y)
        output.erase_down()
        output.reset_attributes()
        output.flush()

        # Erase title.
        if self._last_title:
            output.clear_title()

        self.reset()

    def clear(self):
        """
        Clear screen and go to 0,0
        """
        # Erase current output first.
        self.erase()

        # Send "Erase Screen" command and go to (0, 0).
        output = self.output

        output.erase_screen()
        output.cursor_goto(0, 0)
        output.flush()

        self.request_absolute_cursor_position()


def print_tokens(output, tokens, style):
    """
    Print a list of (Token, text) tuples in the given style to the output.
    """
    assert isinstance(output, Output)
    assert style

    # Reset first.
    output.reset_attributes()
    output.enable_autowrap()

    # Print all (token, text) tuples.
    style_for_token = _StyleForTokenCache(style)

    for token, text in tokens:
        style = style_for_token[token]

        if style:
            output.set_attributes(style['color'], style['bgcolor'],
                                  bold=style.get('bold', False),
                                  underline=style.get('underline', False))
        else:
            output.reset_attributes()

        output.write(text)

    # Reset again.
    output.reset_attributes()
    output.flush()
