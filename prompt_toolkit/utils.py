from __future__ import unicode_literals
import os
import signal
import sys

from wcwidth import wcwidth


__all__ = (
    'Callback',
    'DummyContext',
    'get_cwidth',
    'suspend_to_background_supported',
    'is_conemu_ansi',
    'is_windows',
)


class Callback(object):
    """
    Callbacks wrapper. Used for event propagation.

    There are two ways of using it. The first way is to create a callback
    instance from a callable and pass it to the code that's going to fire it.
    (This can also be used as a decorator.)
    ::

        c = Callback(function)
        c.fire()

    The second way is that the code who's going to fire the callback, already
    created an Callback instance. Then handlers can be attached using the
    ``+=`` operator::

        c = Callback()
        c += handler_function  # Add event handler.
        c.fire()  # Fire event.
    """
    def __init__(self, func=None):
        assert func is None or callable(func)
        self._handlers = [func] if func else []

    def fire(self, *args, **kwargs):
        """
        Trigger callback.
        """
        for handler in self._handlers:
            handler(*args, **kwargs)

    def __iadd__(self, handler):
        """
        Add another handler to this callback.
        """
        self._handlers.append(handler)
        return self

    def __isub__(self, handler):
        """
        Remove a handler from this callback.
        """
        self._handlers.remove(handler)
        return self

    def __or__(self, other):
        """
        Chain two callbacks, using the | operator.
        """
        assert isinstance(other, Callback)

        def call_both():
            self.fire()
            other.fire()

        return Callback(call_both)


class DummyContext(object):
    """
    (contextlib.nested is not available on Py3)
    """
    def __enter__(self):
        pass

    def __exit__(self, *a):
        pass


class _CharSizesCache(dict):
    """
    Cache for wcwidth sizes.
    """
    def __missing__(self, string):
        # Note: We use the `max(0, ...` because some non printable control
        #       characters, like e.g. Ctrl-underscore get a -1 wcwidth value.
        #       It can be possible that these characters end up in the input
        #       text.
        if len(string) == 1:
            result = max(0, wcwidth(string))
        else:
            result = sum(max(0, wcwidth(c)) for c in string)

        self[string] = result
        return result


_CHAR_SIZES_CACHE = _CharSizesCache()


def get_cwidth(string):
    """
    Return width of a string. Wrapper around ``wcwidth``.
    """
    return _CHAR_SIZES_CACHE[string]


def suspend_to_background_supported():
    """
    Returns `True` when the Python implementation supports
    suspend-to-background. This is typically `False' on Windows systems.
    """
    return hasattr(signal, 'SIGTSTP')


def is_windows():
    """
    True when we are using Windows.
    """
    return sys.platform.startswith('win')  # E.g. 'win32', not 'darwin' or 'linux2'


def is_conemu_ansi():
    """
    True when the ConEmu Windows console is used.
    """
    return is_windows() and os.environ.get('ConEmuANSI', 'OFF') == 'ON'
