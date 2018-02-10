"""
Utilities for manipulating formatted text.

When ``to_formatted_text`` has been called, we get a list of ``(style, text)``
tuples. This file contains functions for manipulating such a list.
"""
from __future__ import unicode_literals
from prompt_toolkit.utils import get_cwidth

__all__ = [
    'fragment_list_len',
    'fragment_list_width',
    'fragment_list_to_text',
    'split_lines',
]


def fragment_list_len(fragments):
    """
    Return the amount of characters in this text fragment list.

    :param fragments: List of ``(style_str, text)`` or
        ``(style_str, text, mouse_handler)`` tuples.
    """
    ZeroWidthEscape = '[ZeroWidthEscape]'
    return sum(len(item[1]) for item in fragments if ZeroWidthEscape not in item[0])


def fragment_list_width(fragments):
    """
    Return the character width of this text fragment list.
    (Take double width characters into account.)

    :param fragments: List of ``(style_str, text)`` or
        ``(style_str, text, mouse_handler)`` tuples.
    """
    ZeroWidthEscape = '[ZeroWidthEscape]'
    return sum(get_cwidth(c) for item in fragments for c in item[1] if ZeroWidthEscape not in item[0])


def fragment_list_to_text(fragments):
    """
    Concatenate all the text parts again.

    :param fragments: List of ``(style_str, text)`` or
        ``(style_str, text, mouse_handler)`` tuples.
    """
    ZeroWidthEscape = '[ZeroWidthEscape]'
    return ''.join(item[1] for item in fragments if ZeroWidthEscape not in item[0])


def split_lines(fragments):
    """
    Take a single list of (style_str, text) tuples and yield one such list for each
    line. Just like str.split, this will yield at least one item.

    :param fragments: List of (style_str, text) or (style_str, text, mouse_handler)
                      tuples.
    """
    line = []

    for item in fragments:
        # For (style_str, text) tuples.
        if len(item) == 2:
            style, string = item
            parts = string.split('\n')

            for part in parts[:-1]:
                if part:
                    line.append((style, part))
                yield line
                line = []

            line.append((style, parts[-1]))
                # Note that parts[-1] can be empty, and that's fine. It happens
                # in the case of [('[SetCursorPosition]', '')].

        # For (style_str, text, mouse_handler) tuples.
        #     I know, partly copy/paste, but understandable and more efficient
        #     than many tests.
        else:
            style, string, mouse_handler = item
            parts = string.split('\n')

            for part in parts[:-1]:
                if part:
                    line.append((style, part, mouse_handler))
                yield line
                line = []

            line.append((style, parts[-1], mouse_handler))

    # Always yield the last line, even when this is an empty line. This ensures
    # that when `fragments` ends with a newline character, an additional empty
    # line is yielded. (Otherwise, there's no way to differentiate between the
    # cases where `fragments` does and doesn't end with a newline.)
    yield line
