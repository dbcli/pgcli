from __future__ import unicode_literals
from inspect import ArgSpec
from six import with_metaclass

__all__ = (
    'CLIFilter',
    'SimpleFilter',
    'check_signatures_are_equal',
)

class _FilterTypeMeta(type):
    def __instancecheck__(cls, instance):
        if not hasattr(instance, 'getargspec'):
            return False

        arguments = _drop_self(instance.getargspec())
        return arguments.args == cls.arguments_list or arguments.varargs is not None


class _FilterType(with_metaclass(_FilterTypeMeta)):
    def __new__(cls):
        raise NotImplementedError('This class should not be initiated.')


class CLIFilter(_FilterType):
    """
    Abstract base class for filters that accept a `CommandLineInterface`
    argument. It cannot be instantiated, it's only to be used for instance
    assertions, e.g.::

        isinstance(my_filter, CliFilter)
    """
    arguments_list = ['cli']


class SimpleFilter(_FilterType):
    """
    Abstract base class for filters that don't accept any arguments.
    """
    arguments_list = []


def _drop_self(spec):
    """
    Take an argspec and return a new one without the 'self'.
    """
    args, varargs, varkw, defaults = spec
    if args[0:1] == ['self']:
        args = args[1:]
    return ArgSpec(args, varargs, varkw, defaults)


def check_signatures_are_equal(lst):
    """
    Check whether all filters in this list have the same signature.
    Raises `TypeError` if not.
    """
    spec = _drop_self(lst[0].getargspec())

    for f in lst[1:]:
        if _drop_self(f.getargspec()) != spec:
            raise TypeError('Trying to chain filters with different signature: %r and %r' %
                            (lst[0], f))
