from __future__ import unicode_literals
from prompt_toolkit.keys import Keys
from ..key_bindings import KeyBindings

__all__ = [
    'load_cpr_bindings',
]


def load_cpr_bindings():
    key_bindings = KeyBindings()

    @key_bindings.add(Keys.CPRResponse, save_before=lambda e: False)
    def _(event):
        """
        Handle incoming Cursor-Position-Request response.
        """
        # The incoming data looks like u'\x1b[35;1R'
        # Parse row/col information.
        row, col = map(int, event.data[2:-1].split(';'))

        # Report absolute cursor position to the renderer.
        event.app.renderer.report_absolute_cursor_row(row)

    return key_bindings
