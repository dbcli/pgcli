from __future__ import unicode_literals
from abc import ABCMeta, abstractmethod
from six import with_metaclass

from prompt_toolkit.utils import test_callable_args

__all__ = [
    'Filter',
    'Never',
    'Always',
    'Condition',
]


class Filter(with_metaclass(ABCMeta, object)):
    """
    Base class for any filter to activate/deactivate a feature, depending on a
    condition.

    The return value of ``__call__`` will tell if the feature should be active.
    """
    @abstractmethod
    def __call__(self):
        """
        The actual call to evaluate the filter.
        """
        return True

    def __and__(self, other):
        """
        Chaining of filters using the & operator.
        """
        return _and_cache[self, other]

    def __or__(self, other):
        """
        Chaining of filters using the | operator.
        """
        return _or_cache[self, other]

    def __invert__(self):
        """
        Inverting of filters using the ~ operator.
        """
        return _invert_cache[self]

    def __bool__(self):
        """
        By purpose, we don't allow bool(...) operations directly on a filter,
        because the meaning is ambiguous.

        Executing a filter has to be done always by calling it. Providing
        defaults for `None` values should be done through an `is None` check
        instead of for instance ``filter1 or Always()``.
        """
        raise ValueError('The truth value of a Filter is ambiguous. '
                         'Instead, call it as a function.')

    __nonzero__ = __bool__  # For Python 2.


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
        a, b = filters
        assert isinstance(b, Filter), 'Expecting filter, got %r' % b

        if isinstance(b, Always) or isinstance(a, Never):
            return a
        elif isinstance(b, Never) or isinstance(a, Always):
            return b

        result = _AndList(filters)
        self[filters] = result
        return result


class _OrCache(dict):
    """ Cache for Or operation between filters. """
    def __missing__(self, filters):
        a, b = filters
        assert isinstance(b, Filter), 'Expecting filter, got %r' % b

        if isinstance(b, Always) or isinstance(a, Never):
            return b
        elif isinstance(b, Never) or isinstance(a, Always):
            return a

        result = _OrList(filters)
        self[filters] = result
        return result


class _InvertCache(dict):
    """ Cache for inversion operator. """
    def __missing__(self, filter):
        result = _Invert(filter)
        self[filter] = result
        return result


_and_cache = _AndCache()
_or_cache = _OrCache()
_invert_cache = _InvertCache()


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

    def __call__(self):
        return all(f() for f in self.filters)

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

    def __call__(self):
        return any(f() for f in self.filters)

    def __repr__(self):
        return '|'.join(repr(f) for f in self.filters)


class _Invert(Filter):
    """
    Negation of another filter.
    """
    def __init__(self, filter):
        self.filter = filter

    def __call__(self):
        return not self.filter()

    def __repr__(self):
        return '~%r' % self.filter


class Always(Filter):
    """
    Always enable feature.
    """
    def __call__(self):
        return True

    def __invert__(self):
        return Never()


class Never(Filter):
    """
    Never enable feature.
    """
    def __call__(self):
        return False

    def __invert__(self):
        return Always()


class Condition(Filter):
    """
    Turn any callable into a Filter. The callable is supposed to not take any
    arguments.

    This can be used as a decorator::

        @Condition
        def feature_is_active():  # `feature_is_active` becomes a Filter.
            return True

    :param func: Callable which takes no inputs and returns a boolean.
    """
    def __init__(self, func):
        assert callable(func)
        assert test_callable_args(func, [])
        self.func = func

    def __call__(self):
        return self.func()

    def __repr__(self):
        return 'Condition(%r)' % self.func
