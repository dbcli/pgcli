from __future__ import unicode_literals

from prompt_toolkit.utils import get_cwidth

__all__ = (
    'token_list_len',
    'token_list_width',
    'explode_tokens',
)


def token_list_len(tokenlist):
    """
    Return the amount of characters in this token list.

    :param tokenlist: List of (token, text) tuples.
    """
    return sum(len(v) for k, v in tokenlist)


def token_list_width(tokenlist):
    """
    Return the character width of this token list.
    (Take double width characters into account.)

    :param tokenlist: List of (token, text) tuples.
    """
    return sum(get_cwidth(c) for k, word in tokenlist for c in word)


def explode_tokens(tokenlist):
    """
    Turn a list of (token, text) tuples into another list where each string is
    exactly one character.

    :param tokenlist: List of (token, text) tuples.
    """
    result = []

    for token, string in tokenlist:
        for c in string:
            result.append((token, c))

    return result
