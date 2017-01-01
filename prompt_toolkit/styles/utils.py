from __future__ import unicode_literals
from .base import Attrs

__all__ = (
    'split_token_in_parts',
    'merge_attrs',
)


def split_token_in_parts(token):
    """
    Take a Token, and turn it in a list of tokens, by splitting
    it on ':' (taking that as a separator.)

    (This returns a `tuple` of tuples, usable for hashing.)
    """
    result = []
    current = []
    for part in token + (':', ):
        if part == ':':
            if current:
                result.append(tuple(current))
                current = []
        else:
            current.append(part)

    # Remove empty items, duplicates and return sorted as a tuple.
    return tuple(sorted(set(filter(None, result))))


def merge_attrs(list_of_attrs):
    """
    Take a list of :class:`.Attrs` instances and merge them into one.
    Every `Attr` in the list can override the styling of the previous one. So,
    the last one has highest priority.
    """
    def _or(*values):
        " Take first not-None value, starting at the end. "
        for v in values[::-1]:
            if v is not None:
                return v

    return Attrs(
        color=_or('', *[a.color for a in list_of_attrs]),
        bgcolor=_or('', *[a.bgcolor for a in list_of_attrs]),
        bold=_or(False, *[a.bold for a in list_of_attrs]),
        underline=_or(False, *[a.underline for a in list_of_attrs]),
        italic=_or(False, *[a.italic for a in list_of_attrs]),
        blink=_or(False, *[a.blink for a in list_of_attrs]),
        reverse=_or(False, *[a.reverse for a in list_of_attrs]))
