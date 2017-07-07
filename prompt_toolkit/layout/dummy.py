"""
Dummy layout. Used when somebody creates an `Application` without specifying a
`Layout`.
"""
from __future__ import unicode_literals
from prompt_toolkit.key_binding import KeyBindings
from .layout import Layout
from .controls import FormattedTextControl
from .containers import Window
from .formatted_text import HTML
from .dimension import D

__all__ = (
    'create_dummy_layout',
)


def create_dummy_layout():
    """
    Create a dummy layout for use in an 'Application' that doesn't have a
    layout specified. When ENTER is pressed, the application quits.
    """
    kb = KeyBindings()

    @kb.add('enter')
    def enter(event):
        event.app.set_return_value(None)

    control = FormattedTextControl(
        HTML('No layout specified. Press <reverse>ENTER</reverse> to quit.'),
        key_bindings=kb)
    window = Window(content=control, height=D(min=1))
    return Layout(container=window, focussed_window=window)
