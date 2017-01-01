from __future__ import unicode_literals
from .base import Always, Never
from .types import SimpleFilter, AppFilter

__all__ = (
    'to_app_filter',
    'to_simple_filter',
    'to_cli_filter',
)

_always = Always()
_never = Never()


def to_simple_filter(bool_or_filter):
    """
    Accept both booleans and CLIFilters as input and
    turn it into a SimpleFilter.
    """
    if not isinstance(bool_or_filter, (bool, SimpleFilter)):
        raise TypeError('Expecting a bool or a SimpleFilter instance. Got %r' % bool_or_filter)

    return {
        True: _always,
        False: _never,
    }.get(bool_or_filter, bool_or_filter)


def to_app_filter(bool_or_filter):
    """
    Accept both booleans and CLIFilters as input and
    turn it into a AppFilter.
    """
    if not isinstance(bool_or_filter, (bool, AppFilter)):
        raise TypeError('Expecting a bool or a AppFilter instance. Got %r' % bool_or_filter)

    return {
        True: _always,
        False: _never,
    }.get(bool_or_filter, bool_or_filter)


# For backwards-compatibility. Keep the old name.
to_cli_filter = to_app_filter
