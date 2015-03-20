from __future__ import unicode_literals

try:
    from wcwidth import wcwidth
except ImportError:
    from .libs.wcwidth import wcwidth


__all__ = (
    'EventHook',
    'DummyContext',
)


class EventHook(object):
    """
    Event hook::

        e = EventHook()
        e += handler_function  # Add event handler.
        e.fire()  # Fire event.

    Thanks to Michael Foord:
    http://www.voidspace.org.uk/python/weblog/arch_d7_2007_02_03.shtml#e616
    """
    def __init__(self):
        self.__handlers = []

    def __iadd__(self, handler):
        self.__handlers.append(handler)
        return self

    def __isub__(self, handler):
        self.__handlers.remove(handler)
        return self

    def fire(self, *args, **keywargs):
        for handler in self.__handlers:
            handler(*args, **keywargs)


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
