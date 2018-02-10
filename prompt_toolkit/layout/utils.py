from __future__ import unicode_literals

__all__ = [
    'explode_text_fragments',
]


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
