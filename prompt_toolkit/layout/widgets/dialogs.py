"""
Collection of reusable components for building full screen applications.
"""
from __future__ import unicode_literals
import six
from prompt_toolkit.eventloop import EventLoop
from .base import Box, Shadow, Frame
from ..containers import VSplit, HSplit
from ..dimension import Dimension as D

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
    :param loop: The `EventLoop` to be used.
    """
    def __init__(self, body, title='', buttons=None, loop=None):
        assert loop is None or isinstance(loop, EventLoop)
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

        self.container = Box(
            body=Shadow(
                body=Frame(
                    title=title,
                    body=frame_body,
                    style='class:dialog.body')),
            style='class:dialog')

    def __pt_container__(self):
        return self.container
