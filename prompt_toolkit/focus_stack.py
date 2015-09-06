"""
Push/pop stack of buffer names. The top buffer of the stack is the one that
currently has the focus.

Note that the stack can contain `None` values. This means that none of the
buffers has the focus.
"""
from __future__ import unicode_literals
from six import string_types

from prompt_toolkit.enums import DEFAULT_BUFFER

__all__ = (
    'FocusStack',
)


class FocusStack(object):
    def __init__(self, initial=DEFAULT_BUFFER):
        self._initial = initial
        self.reset()

    def __repr__(self):
        return '%s(initial=%r, _stack=%r)' % (
            self.__class__.__name__, self._initial, self._stack)

    def reset(self):
        self._stack = [self._initial]

    def __contains__(self, value):
        return value in self._stack

    def pop(self):
        if len(self._stack) > 1:
            self._stack.pop()
        else:
            raise IndexError('Cannot pop last item from the focus stack.')

    def replace(self, buffer_name):
        assert buffer_name == None or isinstance(buffer_name, string_types)

        self._stack.pop()
        self._stack.append(buffer_name)

    def push(self, buffer_name):
        assert buffer_name == None or isinstance(buffer_name, string_types)

        self._stack.append(buffer_name)

    @property
    def current(self):
        return self._stack[-1]

    @property
    def previous(self):
        """
        Return the name of the previous focussed buffer, or return None.
        """
        if len(self._stack) > 1:
            return self._stack[-2]
