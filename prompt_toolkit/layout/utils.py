from __future__ import unicode_literals
from pygments.token import Token

from prompt_toolkit.utils import get_cwidth

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
        result = explode_tokens(self._list)

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


def explode_tokens(tokens):
    """
    Turn a list of (token, text) tuples into another list where each string is
    exactly one character.

    :param tokens: List of (token, text) tuples.
    """
    result = []

    for token, string in tokens:
        for c in string:
            result.append((token, c))

    return result


def fit_tokens_in_size(tokens, width, height=1, default_token=Token):
    """
    Fit a list of (token, text) tuples in a width/height rectangle. Extend with
    `default_token` when there is space available, and trim when the input is
    too large.

    :param tokens: List of (token, text) tuples.
    :param width: Width of the rectangle.
    :param height: Height of the rectangle.
    :param default_token: Token to be used when extending.
    """
    result = [[]]  # List of lines
    line_index = 0
    line_width = 0

    for token, character in explode_tokens(tokens):
        if character == '\n':
            # Fill row.
            if width - line_width > 0:
                result[line_index] += [(default_token, ' ' * (width - line_width))]

            if len(result) == height:
                break

            line_index += 1
            line_width = 0
            result.append([])
        else:
            w = get_cwidth(character)
            line_width += w
            if line_width <= width:
                result[line_index].append((token, character))

    # Fill current row.
    if width - line_width > 0:
        result[line_index] += [(default_token, ' ' * (width - line_width))]

    # Fill lines.
    for _ in range(height - len(result)):
        result.append([(default_token, ' ' * width)])

    return result
