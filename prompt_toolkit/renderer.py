"""
Renders the command line on the console.
(Redraws parts of the input line that were changed.)
"""
from __future__ import unicode_literals

from prompt_toolkit.filters import to_app_filter
from prompt_toolkit.layout.formatted_text import to_formatted_text
from prompt_toolkit.layout.mouse_handlers import MouseHandlers
from prompt_toolkit.layout.screen import Point, Screen, WritePosition
from prompt_toolkit.output import Output
from prompt_toolkit.styles import BaseStyle
from prompt_toolkit.utils import is_windows

from six.moves import range

__all__ = (
    'Renderer',
    'print_formatted_text',
)


def _output_screen_diff(app, output, screen, current_pos, previous_screen=None, last_style=None,
                        is_done=False, attrs_for_style_string=None, size=None, previous_width=0):  # XXX: drop is_done
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
    :param last_style: The style string, used for drawing the last drawn
        character.  (Color/attributes.)
    :param attrs_for_style_string: :class:`._StyleStringToAttrsCache` instance.
    :param width: The width of the terminal.
    :param prevous_width: The width of the terminal during the last rendering.
    """
    width, height = size.columns, size.rows

    #: Remember the last printed character.
    last_style = [last_style]  # nonlocal

    #: Variable for capturing the output.
    write = output.write
    write_raw = output.write_raw

    # Create locals for the most used output methods.
    # (Save expensive attribute lookups.)
    _output_set_attributes = output.set_attributes
    _output_reset_attributes = output.reset_attributes
    _output_cursor_forward = output.cursor_forward
    _output_cursor_up = output.cursor_up
    _output_cursor_backward = output.cursor_backward

    # Hide cursor before rendering. (Avoid flickering.)
    output.hide_cursor()

    def reset_attributes():
        " Wrapper around Output.reset_attributes. "
        _output_reset_attributes()
        last_style[0] = None  # Forget last char after resetting attributes.

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

    def output_char(char):
        """
        Write the output of this character.
        """
        # If the last printed character has the same style, don't output the
        # style again.
        the_last_style = last_style[0]

        if the_last_style and the_last_style == char.style:
            write(char.char)
        else:
            _output_set_attributes(attrs_for_style_string[char.style])
            write(char.char)
            last_style[0] = char.style

    # Disable autowrap
    if not previous_screen:
        output.disable_autowrap()
        reset_attributes()

    # When the previous screen has a different size, redraw everything anyway.
    # Also when we are done. (We meight take up less rows, so clearing is important.)
    if is_done or not previous_screen or previous_width != width:  # XXX: also consider height??
        current_pos = move_cursor(Point(x=0, y=0))
        reset_attributes()
        output.erase_down()

        previous_screen = Screen()

    # Get height of the screen.
    # (height changes as we loop over data_buffer, so remember the current value.)
    # (Also make sure to clip the height to the size of the output.)
    current_height = min(screen.height, height)

    # Loop over the rows.
    row_count = min(max(screen.height, previous_screen.height), height)
    c = 0  # Column counter.

    for y in range(row_count):
        new_row = screen.data_buffer[y]
        previous_row = previous_screen.data_buffer[y]
        zero_width_escapes_row = screen.zero_width_escapes[y]

        new_max_line_len = min(width - 1, max(new_row.keys()) if new_row else 0)
        previous_max_line_len = min(width - 1, max(previous_row.keys()) if previous_row else 0)

        # Loop over the columns.
        c = 0
        while c < new_max_line_len + 1:
            new_char = new_row[c]
            old_char = previous_row[c]
            char_width = (new_char.width or 1)

            # When the old and new character at this position are different,
            # draw the output. (Because of the performance, we don't call
            # `Char.__ne__`, but inline the same expression.)
            if new_char.char != old_char.char or new_char.style != old_char.style:
                current_pos = move_cursor(Point(x=c, y=y))

                # Send injected escape sequences to output.
                if c in zero_width_escapes_row:
                    write_raw(zero_width_escapes_row[c])

                output_char(new_char)
                current_pos = Point(x=current_pos.x + char_width, y=current_pos.y)

            c += char_width

        # If the new line is shorter, trim it.
        if previous_screen and new_max_line_len < previous_max_line_len:
            current_pos = move_cursor(Point(x=new_max_line_len+1, y=y))
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
    if current_height > previous_screen.height:
        current_pos = move_cursor(Point(x=0, y=current_height - 1))

    # Move cursor:
    if is_done:
        current_pos = move_cursor(Point(x=0, y=current_height))
        output.erase_down()
    else:
        current_pos = move_cursor(
            screen.get_cursor_position(app.layout.current_window))

    if is_done:
        output.enable_autowrap()

    # Always reset the color attributes. This is important because a background
    # thread could print data to stdout and we want that to be displayed in the
    # default colors. (Also, if a background color has been set, many terminals
    # give weird artifacs on resize events.)
    reset_attributes()

    if screen.show_cursor or is_done:
        output.show_cursor()

    return current_pos, last_style[0]


class HeightIsUnknownError(Exception):
    " Information unavailable. Did not yet receive the CPR response. "


class _StyleStringToAttrsCache(dict):
    """
    A cache structure that maps style strings to :class:`.Attr`.
    (This is an important speed up.)
    """
    def __init__(self, get_attrs_for_style_str):
        self.get_attrs_for_style_str = get_attrs_for_style_str

    def __missing__(self, style_str):
        try:
            result = self.get_attrs_for_style_str(style_str)
        except KeyError:
            result = None

        self[style_str] = result
        return result


class Renderer(object):
    """
    Typical usage:

    ::

        output = Vt100_Output.from_pty(sys.stdout)
        r = Renderer(style, output)
        r.render(app, layout=...)
    """
    def __init__(self, style, output, full_screen=False, mouse_support=False):
        assert isinstance(style, BaseStyle)
        assert isinstance(output, Output)

        self.style = style
        self.output = output
        self.full_screen = full_screen
        self.mouse_support = to_app_filter(mouse_support)

        self._in_alternate_screen = False
        self._mouse_support_enabled = False
        self._bracketed_paste_enabled = False

        # Waiting for CPR flag. True when we send the request, but didn't got a
        # response.
        self.waiting_for_cpr = False

        # Cache for the style.
        self._attrs_for_style = None
        self._last_style_hash = None

        self.reset(_scroll=True)

    def reset(self, _scroll=False, leave_alternate_screen=True):
        # Reset position
        self._cursor_pos = Point(x=0, y=0)

        # Remember the last screen instance between renderers. This way,
        # we can create a `diff` between two screens and only output the
        # difference. It's also to remember the last height. (To show for
        # instance a toolbar at the bottom position.)
        self._last_screen = None
        self._last_size = None
        self._last_style = None

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
        if self._in_alternate_screen and leave_alternate_screen:
            self.output.quit_alternate_screen()
            self._in_alternate_screen = False

        # Disable mouse support.
        if self._mouse_support_enabled:
            self.output.disable_mouse_support()
            self._mouse_support_enabled = False

        # Disable bracketed paste.
        if self._bracketed_paste_enabled:
            self.output.disable_bracketed_paste()
            self._bracketed_paste_enabled = False

        # Flush output. `disable_mouse_support` needs to write to stdout.
        self.output.flush()

    @property
    def last_rendered_screen(self):
        """
        The `Screen` class that was generated during the last rendering.
        This can be `None`.
        """
        return self._last_screen

    @property
    def height_is_known(self):
        """
        True when the height from the cursor until the bottom of the terminal
        is known. (It's often nicer to draw bottom toolbars only if the height
        is known, in order to avoid flickering when the CPR response arrives.)
        """
        return self.full_screen or self._min_available_height > 0 or \
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
            if self.full_screen:
                self._min_available_height = self.output.get_size().rows
            else:
                # Asks for a cursor position report (CPR).
                self.waiting_for_cpr = True
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

        self.waiting_for_cpr = False

    def render(self, app, layout, is_done=False):
        """
        Render the current interface to the output.

        :param is_done: When True, put the cursor at the end of the interface. We
                won't print any changes to this part.
        """
        output = self.output
        output.start_rendering()

        # Enter alternate screen.
        if self.full_screen and not self._in_alternate_screen:
            self._in_alternate_screen = True
            output.enter_alternate_screen()

        # Enable bracketed paste.
        if not self._bracketed_paste_enabled:
            self.output.enable_bracketed_paste()
            self._bracketed_paste_enabled = True

        # Enable/disable mouse support.
        needs_mouse_support = self.mouse_support(app)

        if needs_mouse_support and not self._mouse_support_enabled:
            output.enable_mouse_support()
            self._mouse_support_enabled = True

        elif not needs_mouse_support and self._mouse_support_enabled:
            output.disable_mouse_support()
            self._mouse_support_enabled = False

        # Create screen and write layout to it.
        size = output.get_size()
        screen = Screen()
        screen.show_cursor = False  # Hide cursor by default, unless one of the
                                    # containers decides to display it.
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
        if self.style.invalidation_hash() != self._last_style_hash:
            self._last_screen = None
            self._attrs_for_style = None
        if self._attrs_for_style is None:
            self._attrs_for_style = _StyleStringToAttrsCache(self.style.get_attrs_for_style_str)
        self._last_style_hash = self.style.invalidation_hash()

        layout.container.write_to_screen(app, screen, mouse_handlers, WritePosition(
            xpos=0,
            ypos=0,
            width=size.columns,
            height=(size.rows if self.full_screen else height),
            extended_height=size.rows,
        ), parent_style='')

        # When grayed. Replace all styles in the new screen.
        if app.is_aborting or app.is_exiting:
            screen.replace_all_styles('class:aborted')

        # Process diff and write to output.
        self._cursor_pos, self._last_style = _output_screen_diff(
            app, output, screen, self._cursor_pos,
            self._last_screen, self._last_style, is_done,
            attrs_for_style_string=self._attrs_for_style,
            size=size,
            previous_width=(self._last_size.columns if self._last_size else 0))
        self._last_screen = screen
        self._last_size = size
        self.mouse_handlers = mouse_handlers

        # Write title if it changed.
        new_title = app.terminal_title

        if new_title != self._last_title:
            if new_title is None:
                self.output.clear_title()
            else:
                self.output.set_title(new_title)
            self._last_title = new_title

        output.flush()

        if is_done:
            self.reset()

        output.stop_rendering()

    def erase(self, leave_alternate_screen=True, erase_title=True):
        """
        Hide all output and put the cursor back at the first line. This is for
        instance used for running a system command (while hiding the CLI) and
        later resuming the same CLI.)

        :param leave_alternate_screen: When True, and when inside an alternate
            screen buffer, quit the alternate screen.
        :param erase_title: When True, clear the title from the title bar.
        """
        output = self.output

        output.cursor_backward(self._cursor_pos.x)
        output.cursor_up(self._cursor_pos.y)
        output.erase_down()
        output.reset_attributes()
        output.flush()

        # Erase title.
        if self._last_title and erase_title:
            output.clear_title()

        self.reset(leave_alternate_screen=leave_alternate_screen)

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


def print_formatted_text(output, formatted_text, style):
    """
    Print a list of (style_str, text) tuples in the given style to the output.
    """
    assert isinstance(output, Output)
    assert isinstance(style, BaseStyle)
    fragments = to_formatted_text(formatted_text)

    # Reset first.
    output.reset_attributes()
    output.enable_autowrap()

    # Print all (style_str, text) tuples.
    attrs_for_style_string = _StyleStringToAttrsCache(style.get_attrs_for_style_str)

    for style_str, text in fragments:
        attrs = attrs_for_style_string[style_str]

        if attrs:
            output.set_attributes(attrs)
        else:
            output.reset_attributes()

        output.write(text)

    # Reset again.
    output.reset_attributes()
    output.flush()


