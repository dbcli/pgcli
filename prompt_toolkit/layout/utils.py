from __future__ import unicode_literals

from prompt_toolkit.utils import get_cwidth

__all__ = (
    'fragment_list_len',
    'fragment_list_width',
    'fragment_list_to_text',
    'explode_text_fragments',
    'split_lines',
)


def fragment_list_len(fragments):
    """
    Return the amount of characters in this text fragment list.

    :param fragments: List of ``(style_str, text)`` or
        ``(style_str, text, mouse_handler)`` tuples.
    """
    ZeroWidthEscape = '[ZeroWidthEscape]'
    return sum(len(item[1]) for item in fragments if item[0] != ZeroWidthEscape)


def fragment_list_width(fragments):
    """
    Return the character width of this text fragment list.
    (Take double width characters into account.)

    :param fragments: List of ``(style_str, text)`` or
        ``(style_str, text, mouse_handler)`` tuples.
    """
    ZeroWidthEscape = '[ZeroWidthEscape]'
    return sum(get_cwidth(c) for item in fragments for c in item[1] if item[0] != ZeroWidthEscape)


def fragment_list_to_text(fragments):
    """
    Concatenate all the text parts again.

    :param fragments: List of ``(style_str, text)`` or
        ``(style_str, text, mouse_handler)`` tuples.
    """
    ZeroWidthEscape = '[ZeroWidthEscape]'
    return ''.join(item[1] for item in fragments if item[0] != ZeroWidthEscape)


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


class _ExplodedList(list):
    """
    Wrapper around a list, that marks it as 'exploded'.

    As soon as items are added or the list is extended, the new items are
    automatically exploded as well.
    """
    def __init__(self, *a, **kw):
        super(_ExplodedList, self).__init__(*a, **kw)
        self.exploded = True

    def append(self, item):
        self.extend([item])

    def extend(self, lst):
        super(_ExplodedList, self).extend(explode_text_fragments(lst))

    def insert(self, index, item):
        raise NotImplementedError  # TODO

    # TODO: When creating a copy() or [:], return also an _ExplodedList.

    def __setitem__(self, index, value):
        """
        Ensure that when `(style_str, 'long string')` is set, the string will be
        exploded.
        """
        if not isinstance(index, slice):
            index = slice(index, index + 1)
        value = explode_text_fragments([value])
        super(_ExplodedList, self).__setitem__(index, value)


def explode_text_fragments(fragments):
    """
    Turn a list of (style_str, text) tuples into another list where each string is
    exactly one character.

    It should be fine to call this function several times. Calling this on a
    list that is already exploded, is a null operation.

    :param fragments: List of (style, text) tuples.
    """
    # When the fragments is already exploded, don't explode again.
    if getattr(fragments, 'exploded', False):
        return fragments

    result = []

    for style, string in fragments:
        for c in string:
            result.append((style, c))

    return _ExplodedList(result)
