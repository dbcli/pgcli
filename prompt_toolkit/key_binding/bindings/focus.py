from __future__ import unicode_literals

__all__ = (
    'focus_next',
    'focus_previous',
)


def focus_next(event):
    """
    Focus the next visible Window.
    (Often bound to the `Tab` key.)
    """
    windows = event.app.focussable_windows
    if len(windows) > 0:
        try:
            index = windows.index(event.app.layout.current_window)
        except ValueError:
            index = 0
        else:
            index = (index + 1) % len(windows)

        event.app.layout.focus(windows[index])


def focus_previous(event):
    """
    Focus the previous visible Window.
    (Often bound to the `BackTab` key.)
    """
    windows = event.app.focussable_windows
    if len(windows) > 0:
        try:
            index = windows.index(event.app.layout.current_window)
        except ValueError:
            index = 0
        else:
            index = (index - 1) % len(windows)

        event.app.layout.focus(windows[index])
