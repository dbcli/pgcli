from __future__ import unicode_literals
from .base import Always, Never
from .types import SimpleFilter, CLIFilter

__all__ = (
    'to_cli_filter',
    'to_simple_filter',
)


def to_simple_filter(bool_or_filter):
    """
    Accept both booleans and CLIFilters as input and
    turn it into a SimpleFilter.
    """
    assert isinstance(bool_or_filter, (bool, SimpleFilter)), \
        TypeError('Expecting a bool or a SimpleFilter instance. Got %r' % bool_or_filter)

    return {
        True: Always(),
        False: Never()
    }.get(bool_or_filter, bool_or_filter)


def to_cli_filter(bool_or_filter):
    """
    Accept both booleans and CLIFilters as input and
    turn it into a CLIFilter.
    """
    assert isinstance(bool_or_filter, (bool, CLIFilter)), \
        TypeError('Expecting a bool or a CLIFilter instance. Got %r' % bool_or_filter)

    return {
        True: Always(),
        False: Never()
    }.get(bool_or_filter, bool_or_filter)
