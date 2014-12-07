"""
Push/pop stack of buffer names. The top buffer of the stack is the one that
currently has the focus.
"""
from __future__ import unicode_literals
from six import string_types

__all__ = (
    'FocusStack',
)


class FocusStack(object):
    def __init__(self, initial='default'):
        self._initial = initial

    def reset(self):
        self._stack = [self._initial]

    def pop(self):
        if len(self._stack) > 1:
            self._stack.pop()
        else:
            raise Exception('Cannot pop last item from the focus stack.')

    def push(self, buffer_name):
        assert isinstance(buffer_name, string_types)
        self._stack.append(buffer_name)

    @property
    def current(self):
        return self._stack[-1]

    @property
    def previous(self):
        return self._stack[-2]
