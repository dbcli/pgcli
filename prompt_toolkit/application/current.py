from __future__ import unicode_literals

__all__ = (
    'get_app',
    'set_app',
    'NoRunningApplicationError',
)


_current_app = None


def get_app():
    """
    Set the current active (running) Application.
    An `Application` is active during the `Application.run_async` call.

    We assume that there can only be one :class:`.Application` active at the
    same time. There is only one terminal window, with only one stdin and
    stdout. This makes the code significantly easier than passing around the
    `Application` everywhere.

    (For applications like pymux where we can have more than one `Application`,
    we'll use a work-around to handle that.)
    """
    if _current_app is None:
        raise NoRunningApplicationError
    return _current_app


def set_app(app):
    """
    Set the current active Application, and return the previous `Application`
    or `None`.
    """
    from .application import Application
    assert app is None or isinstance(app, Application)
    global _current_app
    previous = _current_app
    _current_app = app
    return previous


class NoRunningApplicationError(Exception):
    " There is no active application right now. "
