from __future__ import unicode_literals
from six import with_metaclass
import inspect
from prompt_toolkit.utils import test_callable_args

__all__ = (
    'CLIFilter',
    'SimpleFilter',
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
