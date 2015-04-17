"""
Filters decide whether something is active or not, given the state of the
CommandLineInterface. This is used to enable/disable features, like key
bindings or parts of the layout.

When Filter.__call__ returns True for a centain key, this is considered active.

Filters can be chained using ``&`` and ``|`` operations, and inverted using the
``~`` operator::

    filter = HasFocus('default') & ~ HasSelection()
"""
from __future__ import unicode_literals
from abc import ABCMeta, abstractmethod
from six import with_metaclass

__all__ = (
    'Never',
    'Always',
    'Condition',
    'HasArg',
    'HasCompletions',
    'HasFocus',
    'HasSelection',
    'HasValidationError',
    'IsAborting',
    'IsDone',
    'IsMultiline',
    'IsReturning',
    'RendererHeightIsKnown',
)


class Filter(with_metaclass(ABCMeta, object)):
    """
    Filter to activate/deactivate a feature, depending on a condition.
    The return value of ``__call__`` will tell if the feature should be active.
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


class HasCompletions(Filter):
    """
    Enable when the current buffer has completions.
    """
    def __call__(self, cli):
        return cli.current_buffer.complete_state is not None


class IsMultiline(Filter):
    """
    Enable in multiline mode.
    """
    def __call__(self, cli):
        return cli.current_buffer.is_multiline(cli)


class HasValidationError(Filter):
    """
    Current buffer has validation error.
    """
    def __call__(self, cli):
        return cli.current_buffer.validation_error is not None


class HasArg(Filter):
    """
    Enable when the input processor has an 'arg'.
    """
    def __call__(self, cli):
        return cli.input_processor.arg is not None


class HasSearch(Filter):
    """
    Incremental search is active.
    """
    def __call__(self, cli):
        return cli.is_searching


class IsReturning(Filter):
    """
    When a return value has been set.
    """
    def __call__(self, cli):
        return cli.is_returning


class IsAborting(Filter):
    """
    True when aborting. (E.g. Control-C pressed.)
    """
    def __call__(self, cli):
        return cli.is_aborting


class IsExiting(Filter):
    """
    True when exiting. (E.g. Control-D pressed.)
    """
    def __call__(self, cli):
        return cli.is_exiting


class IsDone(Filter):
    """
    True when the CLI is returning, aborting or exiting.
    """
    def __call__(self, cli):
        return cli.is_done


class Condition(Filter):
    """
    Turn any callable (which takes a cli and returns a boolean) into a Filter.

    :param func: Callable which takes a `CommandLineInterface` and returns a
                 boolean.
    """
    def __init__(self, func):
        assert callable(func)
        self.func = func

    def __call__(self, cli):
        return self.func(cli)


class Always(Filter):
    """
    Always enable feature.
    """
    def __call__(self, cli):
        return True


class Never(Filter):
    """
    Never enable feature.
    """
    def __call__(self, cli):
        return False


class RendererHeightIsKnown(Filter):
    """
    Only True when the renderer knows it's real height.

    (On VT100 terminals, we have to wait for a CPR response, before we can be
    sure of the available height between the cursor position and the bottom of
    the terminal. And usually it's nicer to wait with drawing bottom toolbars
    until we receive the height, in order to avoid flickering -- first drawing
    somewhere in the middle, and then again at the bottom.)
    """
    def __call__(self, cli):
        return cli.renderer.height_is_known
