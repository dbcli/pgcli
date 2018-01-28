from __future__ import unicode_literals
from .enums import SearchDirection
from .filters import to_filter
import six

__all__ = [
    'SearchState',
]


class SearchState(object):
    """
    A search 'query'.
    """
    __slots__ = ('text', 'direction', 'ignore_case', 'incremental')

    def __init__(self, text='', direction=SearchDirection.FORWARD, ignore_case=False, incremental=True):
        assert isinstance(text, six.text_type)
        assert direction in (SearchDirection.FORWARD, SearchDirection.BACKWARD)
        assert isinstance(incremental, bool)

        ignore_case = to_filter(ignore_case)

        self.text = text
        self.direction = direction
        self.ignore_case = ignore_case
        self.incremental = incremental

    def __repr__(self):
        return '%s(%r, direction=%r, ignore_case=%r)' % (
            self.__class__.__name__, self.text, self.direction, self.ignore_case)

    def __invert__(self):
        """
        Create a new SearchState where backwards becomes forwards and the other
        way around.
        """
        if self.direction == SearchDirection.BACKWARD:
            direction = SearchDirection.FORWARD
        else:
            direction = SearchDirection.BACKWARD

        return SearchState(text=self.text, direction=direction, ignore_case=self.ignore_case)
