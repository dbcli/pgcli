from __future__ import unicode_literals
from prompt_toolkit.key_binding.key_processor import KeyPress
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout.screen import Point
from prompt_toolkit.mouse_events import MouseEventType, MouseEvent
from prompt_toolkit.renderer import HeightIsUnknownError
from prompt_toolkit.utils import is_windows

from ..key_bindings import KeyBindings

__all__ = [
    'load_mouse_bindings',
]


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
            if x >= 0xdc00: x -= 0xdc00
            if y >= 0xdc00: y -= 0xdc00

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
            handler = event.app.renderer.mouse_handlers.mouse_handlers[x, y]
            handler(MouseEvent(position=Point(x=x, y=y),
                               event_type=mouse_event))

    @key_bindings.add(Keys.ScrollUp)
    def _(event):
        " Scroll up event without cursor position. "
        # We don't receive a cursor position, so we don't know which window to
        # scroll. Just send an 'up' key press instead.
        event.key_processor.feed(KeyPress(Keys.Up), first=True)

    @key_bindings.add(Keys.ScrollDown)
    def _(event):
        " Scroll down event without cursor position. "
        event.key_processor.feed(KeyPress(Keys.Down), first=True)

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
        handler = event.app.renderer.mouse_handlers.mouse_handlers[x, y]
        handler(MouseEvent(position=Point(x=x, y=y), event_type=event_type))

    return key_bindings
