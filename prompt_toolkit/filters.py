"""
Filters decide whether something is active or not, given the state of the
CommandLineInterface. This can be used to enable/disable key bindings, as well
as to hide/show parts of the layout.

When Filter.__call__ returns True for a centain key, this is considered active.

Filters can be chained using ``&`` and ``|`` operations, and inverted using the
``~`` operator::

    filter = HasFocus('default') & ~ HasSelection()
"""
from __future__ import unicode_literals
from abc import ABCMeta, abstractmethod
from six import with_metaclass

__all__ = (
    'HasFocus',
    'HasSelection',
    'IsMultiline',
    'NoFilter',
)


class Filter(with_metaclass(ABCMeta, object)):
    """
    Filter to activate/deactivate a key binding, depending on a condition.
    The return value of ``__call__`` will tell if the key binding should be active.
    """
    @abstractmethod
    def __call__(self, cli):
        return True

    def __and__(self, other):
        if other is None:
            return self
        else:
            assert isinstance(other, Filter), 'Expecting filter, got %r' % other
            return _AndList([self, other])

    def __or__(self, other):
        if other is None:
            return self
        else:
            assert isinstance(other, Filter), 'Expecting filter, got %r' % other
            return _OrList([self, other])

    def __invert__(self):
        return _Invert(self)


class _AndList(Filter):
    """ Result of &-operation between several filters. """
    def __init__(self, filters):
        self.filters = filters

    def __call__(self, cli):
        return all(f(cli) for f in self.filters)

    def __repr__(self):
        return '&'.join(repr(f) for f in self.filters)


class _OrList(Filter):
    """ Result of |-operation between several filters. """
    def __init__(self, filters):
        self.filters = filters

    def __call__(self, cli):
        return any(f(cli) for f in self.filters)

    def __repr__(self):
        return '|'.join(repr(f) for f in self.filters)


class _Invert(Filter):
    """ Negation of another filter. """
    def __init__(self, filter):
        self.filter = filter

    def __call__(self, cli):
        return not self.filter(cli)

    def __repr__(self):
        return '~%r' % self.filter


class HasFocus(Filter):
    """
    Enable when this buffer has the focus.
    """
    def __init__(self, buffer_name):
        self.buffer_name = buffer_name

    def __call__(self, cli):
        return cli.focus_stack.current == self.buffer_name


class HasSelection(Filter):
    """
    Enable when the current buffer has a selection.
    """
    def __call__(self, cli):
        return bool(cli.buffers[cli.focus_stack.current].selection_state)


class IsMultiline(Filter):
    """
    Enable in multiline mode.
    """
    def __call__(self, cli):
        return cli.buffers[cli.focus_stack.current].is_multiline


class NoFilter(Filter):
    """
    Always enable key binding.
    """
    def __call__(self, cli):
        return True
