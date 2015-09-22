from __future__ import unicode_literals

from prompt_toolkit.utils import get_cwidth

__all__ = (
    'token_list_len',
    'token_list_width',
    'token_list_to_text',
    'explode_tokens',
    'find_window_for_buffer_name',
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


def token_list_to_text(tokenlist):
    """
    Concatenate all the text parts again.
    """
    return ''.join(v for k, v in tokenlist)


def iter_token_lines(tokenlist):
    """
    Iterator that yields tokenlists for each line.
    """
    line = []
    for token, c in explode_tokens(tokenlist):
        line.append((token, c))

        if c == '\n':
            yield line
            line = []

    yield line


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


def find_window_for_buffer_name(layout, buffer_name):
    """
    Look for a Window in the Layout that contains the BufferControl for the
    given buffer and return it. If no such Window is found, return None.
    """
    from .containers import Window
    from .controls import BufferControl

    for l in layout.walk():
        if isinstance(l, Window) and isinstance(l.content, BufferControl):
            if l.content.buffer_name == buffer_name:
                return l
