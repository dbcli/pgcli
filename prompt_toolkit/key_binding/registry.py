from __future__ import unicode_literals
from ..filters import NoFilter, Filter
from ..utils import EventHook

__all__ = (
    'Registry',
)


class _Binding(object):
    def __init__(self, keys, callable, filter=None):
        self.keys = keys
        self._callable = callable
        self.filter = filter

    def call(self, event):
        return self._callable(event)

    def __repr__(self):
        return '_Binding(keys=%r, callable=%r)' % (self.keys, self._callable)



class Registry(object):
    """
    Key binding registry.

    ::

        r = Registry()

        @r.add_binding(Keys.ControlX, Keys.ControlC, filter=INSERT)
        def handler(event):
            # Handle ControlX-ControlC key sequence.
            pass
    """
    def __init__(self):
        self.key_bindings = []
        self.onHandlerCalled = EventHook()

    def add_binding(self, *keys, **kwargs):
        """
        Decorator for annotating key bindings.
        """
        filter = kwargs.pop('filter', None) or NoFilter()
        assert not kwargs
        assert keys
        assert isinstance(filter, Filter), 'Expected Filter instance, got %r' % filter

        def decorator(func):
            self.key_bindings.append(_Binding(keys, func, filter=filter))
            return func
        return decorator
