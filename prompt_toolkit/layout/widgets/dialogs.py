"""
Collection of reusable components for building full screen applications.
"""
from __future__ import unicode_literals
from .base import Box, Shadow, Frame
from ..containers import VSplit, HSplit
from ..dimension import Dimension as D
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.key_binding.key_bindings import KeyBindings
from prompt_toolkit.filters import has_completions
import six

__all__ = (
    'Dialog',
)


class Dialog(object):
    """
    Simple dialog window. This is the base for input dialogs, message dialogs
    and confirmation dialogs.

    :param body: Child container object.
    :param title: Text to be displayed in the heading of the dialog.
    :param buttons: A list of `Button` widgets, displayed at the bottom.
    """
    def __init__(self, body, title='', buttons=None, modal=True, width=None, with_background=False):
        assert isinstance(title, six.text_type)
        assert buttons is None or isinstance(buttons, list)

        buttons = buttons or []

        if buttons:
            frame_body = HSplit([
                # Add optional padding around the body.
                Box(body=body, padding=D(preferred=1, max=1), padding_bottom=0),
                # The buttons.
                Box(body=VSplit(buttons, padding=1),
                    height=D(min=1, max=3, preferred=3))
            ])
        else:
            frame_body = body

        # Key bindings.
        kb = KeyBindings()
        kb.add('tab', filter=~has_completions)(focus_next)
        kb.add('s-tab', filter=~has_completions)(focus_previous)

        frame = Shadow(body=Frame(
            title=title,
            body=frame_body,
            style='class:dialog.body',
            width=(None if with_background is None else width),
            key_bindings=kb,
            modal=modal,
        ))

        if with_background:
            self.container = Box(
                body=frame,
                style='class:dialog',
                width=width)
        else:
            self.container = frame

    def __pt_container__(self):
        return self.container
