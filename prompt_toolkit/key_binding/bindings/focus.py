from __future__ import unicode_literals

__all__ = [
    'focus_next',
    'focus_previous',
]


def focus_next(event):
    """
    Focus the next visible Window.
    (Often bound to the `Tab` key.)
    """
    event.app.layout.focus_next()


def focus_previous(event):
    """
    Focus the previous visible Window.
    (Often bound to the `BackTab` key.)
    """
    event.app.layout.focus_previous()
