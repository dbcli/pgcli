from __future__ import unicode_literals
from prompt_toolkit.eventloop.context import TaskLocal, TaskLocalNotSetError
from contextlib import contextmanager

__all__ = [
    'get_app',
    'set_app',
    'NoRunningApplicationError',
]


_current_app = TaskLocal()


def get_app(raise_exception=False, return_none=False):
    """
    Get the current active (running) Application.
    An :class:`.Application` is active during the
    :meth:`.Application.run_async` call.

    We assume that there can only be one :class:`.Application` active at the
    same time. There is only one terminal window, with only one stdin and
    stdout. This makes the code significantly easier than passing around the
    :class:`.Application` everywhere.

    If no :class:`.Application` is running, then return by default a
    :class:`.DummyApplication`. For practical reasons, we prefer to not raise
    an exception. This way, we don't have to check all over the place whether
    an actual `Application` was returned.

    (For applications like pymux where we can have more than one `Application`,
    we'll use a work-around to handle that.)

    :param raise_exception: When `True`, raise
        :class:`.NoRunningApplicationError` instead of returning a
        :class:`.DummyApplication` if no application is running.
    :param return_none: When `True`, return `None`
        instead of returning a :class:`.DummyApplication` if no application is
        running.
    """
    try:
        value = _current_app.get()
    except TaskLocalNotSetError:
        if raise_exception:
            raise NoRunningApplicationError
        elif return_none:
            return None
        else:
            from .dummy import DummyApplication
            return DummyApplication()
    else:
        return value


@contextmanager
def set_app(app):
    """
    Context manager that sets the given :class:`.Application` active.

    (Usually, not needed to call outside of prompt_toolkit.)
    """
    from .application import Application
    assert app is None or isinstance(app, Application)

    previous = get_app(return_none=True)
    _current_app.set(app)

    try:
        yield
    finally:
        if previous:
            _current_app.set(previous)
        else:
            _current_app.delete()


class NoRunningApplicationError(Exception):
    " There is no active application right now. "
