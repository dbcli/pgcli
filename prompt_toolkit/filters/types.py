from __future__ import unicode_literals
from six import with_metaclass
import inspect

__all__ = (
    'CLIFilter',
    'SimpleFilter',
    'test_callable_args',
)


class _FilterTypeMeta(type):
    def __instancecheck__(cls, instance):
        if not hasattr(instance, 'test_args'):
            return False

        return instance.test_args(*cls.arguments_list)


class _FilterType(with_metaclass(_FilterTypeMeta)):
    def __new__(cls):
        raise NotImplementedError('This class should not be initiated.')


class CLIFilter(_FilterType):
    """
    Abstract base class for filters that accept a
    :class:`~prompt_toolkit.interface.CommandLineInterface` argument. It cannot
    be instantiated, it's only to be used for instance assertions, e.g.::

        isinstance(my_filter, CliFilter)
    """
    arguments_list = ['cli']


class SimpleFilter(_FilterType):
    """
    Abstract base class for filters that don't accept any arguments.
    """
    arguments_list = []


def test_callable_args(func, args):
    """
    Return True when this function can be called with the given arguments.
    """
    signature = getattr(inspect, 'signature', None)

    if signature is not None:
        # For Python 3, use inspect.signature.
        sig = signature(func)
        try:
            sig.bind(*args)
        except TypeError:
            return False
        else:
            return True
    else:
        # For older Python versions, fall back to using getargspec.
        spec = inspect.getargspec(func)

        # Drop the 'self'
        def drop_self(spec):
            args, varargs, varkw, defaults = spec
            if args[0:1] == ['self']:
                args = args[1:]
            return inspect.ArgSpec(args, varargs, varkw, defaults)

        spec = drop_self(spec)

        # When taking *args, always return True.
        if spec.varargs is not None:
            return True

        # Test whether the given amount of args is between the min and max
        # accepted argument counts.
        return len(spec.args) - len(spec.defaults or []) <= len(args) <= len(spec.args)
