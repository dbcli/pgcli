from __future__ import unicode_literals
from abc import ABCMeta, abstractmethod
from six import with_metaclass
from .types import check_signatures_are_equal

import inspect

__all__ = (
    'Filter',
    'Never',
    'Always',
    'Condition',
)


class Filter(with_metaclass(ABCMeta, object)):
    """
    Filter to activate/deactivate a feature, depending on a condition.
    The return value of ``__call__`` will tell if the feature should be active.
    """
    @abstractmethod
    def __call__(self, *a, **kw):
        """
        The actual call to evaluate the filter.
        """
        return True

    def __and__(self, other):
        """
        Chaining of filters using the & operator.
        """
        if other is None or isinstance(other, Always):
            return self
        elif isinstance(other, Never):
            return other
        else:
            assert isinstance(other, Filter), 'Expecting filter, got %r' % other
            return _AndList([self, other])

    def __or__(self, other):
        """
        Chaining of filters using the | operator.
        """
        if other is None or isinstance(other, Never):
            return self
        elif isinstance(other, Always):
            return other
        else:
            assert isinstance(other, Filter), 'Expecting filter, got %r' % other
            return _OrList([self, other])

    def __invert__(self):
        """
        Inverting of filters using the ~ operator.
        """
        return _Invert(self)

    def __nonzero__(self):
        """
        By purpose, we don't allow bool(...) operations directly on a filter,
        because because the meaning is ambigue.

        Executing a filter has to be done always by calling it. Providing
        defaults for `None` values should be done through an `is None` check
        instead of for instance ``filter1 or Always()``.
        """
        raise TypeError

    def getargspec(self):
        """
        Return an Arguments object for this filter. This is used for type
        checking.
        """
        return inspect.getargspec(self.__call__)



class _AndList(Filter):
    """
    Result of &-operation between several filters.
    """
    def __init__(self, filters):
        all_filters = []

        for f in filters:
            if isinstance(f, _AndList):  # Turn nested _AndLists into one.
                all_filters.extend(f.filters)
            else:
                all_filters.append(f)

        # Make sure that all chained filters have the same signature.
        check_signatures_are_equal(all_filters)

        self.filters = all_filters

    def getargspec(self):
        return self.filters[0].getargspec()

    def __call__(self, *a, **kw):
        return all(f(*a, **kw) for f in self.filters)

    def __repr__(self):
        return '&'.join(repr(f) for f in self.filters)


class _OrList(Filter):
    """
    Result of |-operation between several filters.
    """
    def __init__(self, filters):
        all_filters = []

        for f in filters:
            if isinstance(f, _OrList):  # Turn nested _OrLists into one.
                all_filters.extend(f.filters)
            else:
                all_filters.append(f)

        # Make sure that all chained filters have the same signature.
        check_signatures_are_equal(all_filters)

        self.filters = all_filters

    def getargspec(self):
        return self.filters[0].getargspec()

    def __call__(self, *a, **kw):
        return any(f(*a, **kw) for f in self.filters)

    def __repr__(self):
        return '|'.join(repr(f) for f in self.filters)


class _Invert(Filter):
    """
    Negation of another filter.
    """
    def __init__(self, filter):
        self.filter = filter

    def __call__(self, *a, **kw):
        return not self.filter(*a, **kw)

    def __repr__(self):
        return '~%r' % self.filter

    def getargspec(self):
        return self.filter.getargspec()


class Always(Filter):
    """
    Always enable feature.
    """
    def __call__(self, *a, **kw):
        return True

    def __invert__(self):
        return Never()


class Never(Filter):
    """
    Never enable feature.
    """
    def __call__(self, *a, **kw):
        return False

    def __invert__(self):
        return Always()


class Condition(Filter):
    """
    Turn any callable (which takes a cli and returns a boolean) into a Filter.

    This can be used as a decorator::

        @Condition
        def feature_is_active(cli):  # `feature_is_active` becomes a Filter.
            return True

    :param func: Callable which takes a `CommandLineInterface` and returns a
                 boolean.
    """
    def __init__(self, func):
        assert callable(func)
        self.func = func

    def __call__(self, *a, **kw):
        return self.func(*a, **kw)

    def __repr__(self):
        return 'Condition(%r)' % self.func

    def getargspec(self):
        return inspect.getargspec(self.func)
