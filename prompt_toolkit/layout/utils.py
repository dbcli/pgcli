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

    :param tokenlist: List of (token, text) or (token, text, mouse_handler)
                      tuples.
    """
    return sum(len(item[1]) for item in tokenlist)


def token_list_width(tokenlist):
    """
    Return the character width of this token list.
    (Take double width characters into account.)

    :param tokenlist: List of (token, text) or (token, text, mouse_handler)
                      tuples.
    """
    return sum(get_cwidth(c) for item in tokenlist for c in item[1])


def token_list_to_text(tokenlist):
    """
    Concatenate all the text parts again.
    """
    return ''.join(item[1] for item in tokenlist)


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


def split_lines(tokenlist):
    """
    Take a single list of (Token, text) tuples and yield one such list for each
    line.

    :param tokenlist: List of (token, text) or (token, text, mouse_handler)
                      tuples.
    """
    line = []

    for item in tokenlist:
        # For (token, text) tuples.
        if len(item) == 2:
            token, string = item
            parts = string.split('\n')

            for part in parts[:-1]:
                if part:
                    line.append((token, part))
                yield line
                line = []

            line.append((token, parts[-1]))

        # For (token, text, mouse_handler) tuples.
        #     I know, partly copy/paste, but understandable and more efficient
        #     than many tests.
        else:
            token, string, mouse_handler = item
            parts = string.split('\n')

            for part in parts[:-1]:
                if part:
                    line.append((token, part, mouse_handler))
                yield line
                line = []

            line.append((token, parts[-1], mouse_handler))

    if line:
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


def find_window_for_buffer_name(cli, buffer_name):
    """
    Look for a :class:`~prompt_toolkit.layout.containers.Window` in the Layout
    that contains the :class:`~prompt_toolkit.layout.controls.BufferControl`
    for the given buffer and return it. If no such Window is found, return None.
    """
    from prompt_toolkit.interface import CommandLineInterface
    assert isinstance(cli, CommandLineInterface)

    from .containers import Window
    from .controls import BufferControl

    for l in cli.layout.walk(cli):
        if isinstance(l, Window) and isinstance(l.content, BufferControl):
            if l.content.buffer_name == buffer_name:
                return l
