from __future__ import unicode_literals

__all__ = (
    'TokenList',
)


class TokenList(object):
    """
    Wrapper around (Token, text) tuples.
    Implements logical slice and len operations.
    """
    def __init__(self, iterator=None):
        if iterator is not None:
            self._list = list(iterator)
        else:
            self._list = []

    def __len__(self):
        return sum(len(v) for k, v in self._list)

    def __getitem__(self, val):
        result = []

        for token, string in self._list:
            for c in string:
                result.append((token, c))

        if isinstance(val, slice):
            return TokenList(result[val])
        else:
            return result[val]

    def __iter__(self):
        return iter(self._list)

    def append(self, val):
        self._list.append(val)

    def __add__(self, other):
        return TokenList(self._list + list(other))

    @property
    def text(self):
        return ''.join(p[1] for p in self._list)

    def __repr__(self):
        return 'TokenList(%r)' % self._list
