# pylint: disable=function-redefined
from __future__ import unicode_literals

from prompt_toolkit.enums import DEFAULT_BUFFER
from prompt_toolkit.filters import has_selection, Condition, emacs_insert_mode, vi_insert_mode, in_paste_mode, is_multiline
from prompt_toolkit.key_binding.key_processor import KeyPress
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout.screen import Point
from prompt_toolkit.mouse_events import MouseEventType, MouseEvent
from prompt_toolkit.renderer import HeightIsUnknownError
from prompt_toolkit.utils import suspend_to_background_supported, is_windows

from .named_commands import get_by_name
from ..key_bindings import KeyBindings


__all__ = (
    'load_basic_bindings',
    'load_abort_and_exit_bindings',
    'load_basic_system_bindings',
    'load_auto_suggestion_bindings',
)

def if_no_repeat(event):
    """ Callable that returns True when the previous event was delivered to
    another handler. """
    return not event.is_repeat


def load_basic_bindings():
    key_bindings = KeyBindings()
    insert_mode = vi_insert_mode | emacs_insert_mode
    handle = key_bindings.add

    @handle('c-a')
    @handle('c-b')
    @handle('c-c')
    @handle('c-d')
    @handle('c-e')
    @handle('c-f')
    @handle('c-g')
    @handle('c-h')
    @handle('c-i')
    @handle('c-j')
    @handle('c-k')
    @handle('c-l')
    @handle('c-m')
    @handle('c-n')
    @handle('c-o')
    @handle('c-p')
    @handle('c-q')
    @handle('c-r')
    @handle('c-s')
    @handle('c-t')
    @handle('c-u')
    @handle('c-v')
    @handle('c-w')
    @handle('c-x')
    @handle('c-y')
    @handle('c-z')
    @handle('f1')
    @handle('f2')
    @handle('f3')
    @handle('f4')
    @handle('f5')
    @handle('f6')
    @handle('f7')
    @handle('f8')
    @handle('f9')
    @handle('f10')
    @handle('f11')
    @handle('f12')
    @handle('f13')
    @handle('f14')
    @handle('f15')
    @handle('f16')
    @handle('f17')
    @handle('f18')
    @handle('f19')
    @handle('f20')
    @handle('c-@')  # Also c-space.
    @handle('c-\\')
    @handle('c-]')
    @handle('c-^')
    @handle('c-_')
    @handle('backspace')
    @handle('up')
    @handle('down')
    @handle('right')
    @handle('left')
    @handle('s-up')
    @handle('s-down')
    @handle('s-right')
    @handle('s-left')
    @handle('home')
    @handle('end')
    @handle('delete')
    @handle('s-delete')
    @handle('c-delete')
    @handle('pageup')
    @handle('pagedown')
    @handle('s-tab')
    @handle('tab')
    @handle('c-left')
    @handle('c-right')
    @handle('c-up')
    @handle('c-down')
    @handle('insert')
    @handle(Keys.Ignore)
    def _(event):
        """
        First, for any of these keys, Don't do anything by default. Also don't
        catch them in the 'Any' handler which will insert them as data.

        If people want to insert these characters as a literal, they can always
        do by doing a quoted insert. (ControlQ in emacs mode, ControlV in Vi
        mode.)
        """
        pass

    # Readline-style bindings.
    handle('home')(get_by_name('beginning-of-line'))
    handle('end')(get_by_name('end-of-line'))
    handle('left')(get_by_name('backward-char'))
    handle('right')(get_by_name('forward-char'))
    handle('c-up')(get_by_name('previous-history'))
    handle('c-down')(get_by_name('next-history'))
    handle('c-l')(get_by_name('clear-screen'))

    handle('c-k', filter=insert_mode)(get_by_name('kill-line'))
    handle('c-u', filter=insert_mode)(get_by_name('unix-line-discard'))
    handle('backspace', filter=insert_mode, save_before=if_no_repeat)(
        get_by_name('backward-delete-char'))
    handle('delete', filter=insert_mode, save_before=if_no_repeat)(
        get_by_name('delete-char'))
    handle('c-delete', filter=insert_mode, save_before=if_no_repeat)(
        get_by_name('delete-char'))
    handle(Keys.Any, filter=insert_mode, save_before=if_no_repeat)(
        get_by_name('self-insert'))
    handle('c-t', filter=insert_mode)(get_by_name('transpose-chars'))
    handle('c-w', filter=insert_mode)(get_by_name('unix-word-rubout'))
    handle('c-i', filter=insert_mode)(get_by_name('menu-complete'))
    handle('s-tab', filter=insert_mode)(get_by_name('menu-complete-backward'))

    handle('pageup', filter= ~has_selection)(get_by_name('previous-history'))
    handle('pagedown', filter= ~has_selection)(get_by_name('next-history'))

    # CTRL keys.

    text_before_cursor = Condition(lambda app: app.current_buffer.text)
    handle('c-d', filter=text_before_cursor & insert_mode)(get_by_name('delete-char'))

    @handle('enter', filter=insert_mode & is_multiline)
    def _(event):
        " Newline (in case of multiline input. "
        event.current_buffer.newline(copy_margin=not in_paste_mode(event.app))

    @handle('c-j')
    def _(event):
        r"""
        By default, handle \n as if it were a \r (enter).
        (It appears that some terminals send \n instead of \r when pressing
        enter. - at least the Linux subsytem for Windows.)
        """
        event.key_processor.feed(
            KeyPress(Keys.ControlM, '\r'))

    # Delete the word before the cursor.

    @handle('up')
    def _(event):
        event.current_buffer.auto_up(count=event.arg)

    @handle('down')
    def _(event):
        event.current_buffer.auto_down(count=event.arg)

    @handle('delete', filter=has_selection)
    def _(event):
        data = event.current_buffer.cut_selection()
        event.app.clipboard.set_data(data)

    # Global bindings.

    @handle('c-z')
    def _(event):
        """
        By default, control-Z should literally insert Ctrl-Z.
        (Ansi Ctrl-Z, code 26 in MSDOS means End-Of-File.
        In a Python REPL for instance, it's possible to type
        Control-Z followed by enter to quit.)

        When the system bindings are loaded and suspend-to-background is
        supported, that will override this binding.
        """
        event.current_buffer.insert_text(event.data)

    @handle(Keys.CPRResponse, save_before=lambda e: False)
    def _(event):
        """
        Handle incoming Cursor-Position-Request response.
        """
        # The incoming data looks like u'\x1b[35;1R'
        # Parse row/col information.
        row, col = map(int, event.data[2:-1].split(';'))

        # Report absolute cursor position to the renderer.
        event.app.renderer.report_absolute_cursor_row(row)

    @handle(Keys.BracketedPaste)
    def _(event):
        " Pasting from clipboard. "
        data = event.data

        # Be sure to use \n as line ending.
        # Some terminals (Like iTerm2) seem to paste \r\n line endings in a
        # bracketed paste. See: https://github.com/ipython/ipython/issues/9737
        data = data.replace('\r\n', '\n')
        data = data.replace('\r', '\n')

        event.current_buffer.insert_text(data)

    @handle(Keys.Any, filter=Condition(lambda app: app.quoted_insert), eager=True)
    def _(event):
        """
        Handle quoted insert.
        """
        event.current_buffer.insert_text(event.data, overwrite=False)
        event.app.quoted_insert = False

    return key_bindings


def load_mouse_bindings():
    """
    Key bindings, required for mouse support.
    (Mouse events enter through the key binding system.)
    """
    key_bindings = KeyBindings()

    @key_bindings.add(Keys.Vt100MouseEvent)
    def _(event):
        """
        Handling of incoming mouse event.
        """
        # TypicaL:   "eSC[MaB*"
        # Urxvt:     "Esc[96;14;13M"
        # Xterm SGR: "Esc[<64;85;12M"

        # Parse incoming packet.
        if event.data[2] == 'M':
            # Typical.
            mouse_event, x, y = map(ord, event.data[3:])
            mouse_event = {
                32: MouseEventType.MOUSE_DOWN,
                35: MouseEventType.MOUSE_UP,
                96: MouseEventType.SCROLL_UP,
                97: MouseEventType.SCROLL_DOWN,
            }.get(mouse_event)

            # Handle situations where `PosixStdinReader` used surrogateescapes.
            if x >= 0xdc00: x-= 0xdc00
            if y >= 0xdc00: y-= 0xdc00

            x -= 32
            y -= 32
        else:
            # Urxvt and Xterm SGR.
            # When the '<' is not present, we are not using the Xterm SGR mode,
            # but Urxvt instead.
            data = event.data[2:]
            if data[:1] == '<':
                sgr = True
                data = data[1:]
            else:
                sgr = False

            # Extract coordinates.
            mouse_event, x, y = map(int, data[:-1].split(';'))
            m = data[-1]

            # Parse event type.
            if sgr:
                mouse_event = {
                    (0, 'M'): MouseEventType.MOUSE_DOWN,
                    (0, 'm'): MouseEventType.MOUSE_UP,
                    (64, 'M'): MouseEventType.SCROLL_UP,
                    (65, 'M'): MouseEventType.SCROLL_DOWN,
                }.get((mouse_event, m))
            else:
                mouse_event = {
                    32: MouseEventType.MOUSE_DOWN,
                    35: MouseEventType.MOUSE_UP,
                    96: MouseEventType.SCROLL_UP,
                    97: MouseEventType.SCROLL_DOWN,
                    }.get(mouse_event)

        x -= 1
        y -= 1

        # Only handle mouse events when we know the window height.
        if event.app.renderer.height_is_known and mouse_event is not None:
            # Take region above the layout into account. The reported
            # coordinates are absolute to the visible part of the terminal.
            try:
                y -= event.app.renderer.rows_above_layout
            except HeightIsUnknownError:
                return

            # Call the mouse handler from the renderer.
            handler = event.app.renderer.mouse_handlers.mouse_handlers[x,y]
            handler(event.app, MouseEvent(position=Point(x=x, y=y),
                                          event_type=mouse_event))

    @key_bindings.add(Keys.ScrollUp)
    def _(event):
        " Scroll up event without cursor position. "
        # We don't receive a cursor position, so we don't know which window to
        # scroll. Just send an 'up' key press instead.
        event.key_processor.feed(KeyPress(Keys.Up))

    @key_bindings.add(Keys.ScrollDown)
    def _(event):
        " Scroll down event without cursor position. "
        event.key_processor.feed(KeyPress(Keys.Down))

    @key_bindings.add(Keys.WindowsMouseEvent)
    def _(event):
        """
        Handling of mouse events for Windows.
        """
        assert is_windows()  # This key binding should only exist for Windows.

        # Parse data.
        event_type, x, y = event.data.split(';')
        x = int(x)
        y = int(y)

        # Make coordinates absolute to the visible part of the terminal.
        screen_buffer_info = event.app.renderer.output.get_win32_screen_buffer_info()
        rows_above_cursor = screen_buffer_info.dwCursorPosition.Y - event.app.renderer._cursor_pos.y
        y -= rows_above_cursor

        # Call the mouse event handler.
        handler = event.app.renderer.mouse_handlers.mouse_handlers[x,y]
        handler(event.app, MouseEvent(position=Point(x=x, y=y),
                                      event_type=event_type))

    return key_bindings


def load_abort_and_exit_bindings():
    """
    Basic bindings for abort (Ctrl-C) and exit (Ctrl-D).
    """
    key_bindings = KeyBindings()
    handle = key_bindings.add

    @handle('c-c')
    def _(event):
        " Abort when Control-C has been pressed. "
        event.app.abort()

    @Condition
    def ctrl_d_condition(app):
        """ Ctrl-D binding is only active when the default buffer is selected
        and empty. """
        return (app.current_buffer.name == DEFAULT_BUFFER and
                not app.current_buffer.text)

    handle('c-d', filter=ctrl_d_condition)(get_by_name('end-of-file'))

    return key_bindings


def load_basic_system_bindings():
    """
    Basic system bindings (For both Emacs and Vi mode.)
    """
    key_bindings = KeyBindings()

    suspend_supported = Condition(
        lambda app: suspend_to_background_supported())

    @key_bindings.add('c-z', filter=suspend_supported)
    def _(event):
        """
        Suspend process to background.
        """
        event.app.suspend_to_background()

    return key_bindings


def load_auto_suggestion_bindings():
    """
    Key bindings for accepting auto suggestion text.
    """
    key_bindings = KeyBindings()
    handle = key_bindings.add

    suggestion_available = Condition(
        lambda app:
            app.current_buffer.suggestion is not None and
            app.current_buffer.document.is_cursor_at_the_end)

    @handle('c-f', filter=suggestion_available)
    @handle('c-e', filter=suggestion_available)
    @handle('right', filter=suggestion_available)
    def _(event):
        " Accept suggestion. "
        b = event.current_buffer
        suggestion = b.suggestion

        if suggestion:
            b.insert_text(suggestion.text)

    return key_bindings
