from __future__ import unicode_literals
from abc import ABCMeta, abstractmethod
from six import with_metaclass

from .types import test_callable_args


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
        if isinstance(other, Always) or isinstance(self, Never):
            return self
        elif isinstance(other, Never) or isinstance(self, Always):
            return other
        else:
            assert isinstance(other, Filter), 'Expecting filter, got %r' % other
            return _and(self, other)

    def __or__(self, other):
        """
        Chaining of filters using the | operator.
        """
        if isinstance(other, Always) or isinstance(self, Never):
            return other
        elif isinstance(other, Never) or isinstance(self, Always):
            return self
        else:
            assert isinstance(other, Filter), 'Expecting filter, got %r' % other
            return _or(self, other)

    def __invert__(self):
        """
        Inverting of filters using the ~ operator.
        """
        return _Invert(self)

    def __bool__(self):
        """
        By purpose, we don't allow bool(...) operations directly on a filter,
        because because the meaning is ambigue.

        Executing a filter has to be done always by calling it. Providing
        defaults for `None` values should be done through an `is None` check
        instead of for instance ``filter1 or Always()``.
        """
        raise TypeError

    __nonzero__ = __bool__  # For Python 2.

    def test_args(self, *args):
        """
        Test whether this filter can be called with the following argument list.
        """
        return test_callable_args(self.__call__, args)


class _AndCache(dict):
    """
    Cache for And operation between filters.
    (Filter classes are stateless, so we can reuse them.)

    Note: This could be a memory leak if we keep creating filters at runtime.
          If that is True, the filters should be weakreffed (not the tuple of
          filters), and tuples should be removed when one of these filters is
          removed. In practise however, there is a finite amount of filters.
    """
    def __missing__(self, filters):
        result = _AndList(filters)
        self[filters] = result
        return result


class _OrCache(dict):
    """ Cache for Or operation between filters. """
    def __missing__(self, filters):
        result = _OrList(filters)
        self[filters] = result
        return result


_and_cache = _AndCache()
_or_cache = _OrCache()


def _and(filter1, filter2):
    """
    And operation between two filters.
    """
    return _and_cache[filter1, filter2]


def _or(filter1, filter2):
    """
    Or operation between two filters.
    """
    return _or_cache[filter1, filter2]


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

        self.filters = all_filters

    def test_args(self, *args):
        return all(f.test_args(*args) for f in self.filters)

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

        self.filters = all_filters

    def test_args(self, *args):
        return all(f.test_args(*args) for f in self.filters)

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

    def test_args(self, *args):
        return self.filter.test_args(*args)


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

    :param func: Callable which takes either a
        :class:`~prompt_toolkit.interface.CommandLineInterface` or nothing and
        returns a boolean. (Depending on what it takes, this will become a
        :class:`.Filter` or :class:`~prompt_toolkit.filters.CLIFilter`.)
    """
    def __init__(self, func):
        assert callable(func)
        self.func = func

    def __call__(self, *a, **kw):
        return self.func(*a, **kw)

    def __repr__(self):
        return 'Condition(%r)' % self.func

    def test_args(self, *a):
        return test_callable_args(self.func, a)
