from __future__ import unicode_literals
from .enums import SearchDirection
from .filters import to_filter
import six

__all__ = [
    'SearchState',
]


class SearchState(object):
    """
    A search 'query', associated with a search field (like a SearchToolbar).

    Every searchable `BufferControl` points to a `search_buffer_control`
    (another `BufferControls`) which represents the search field. The
    `SearchState` attached to that search field is used for storing the current
    search query.

    It is possible to have one searchfield for multiple `BufferControls`. In
    that case, they'll share the same `SearchState`.
    If there are multiple `BufferControls` that display the same `Buffer`, then
    they can have a different `SearchState` each (if they have a different
    search control).
    """
    __slots__ = ('text', 'direction', 'ignore_case')

    def __init__(self, text='', direction=SearchDirection.FORWARD, ignore_case=False):
        assert isinstance(text, six.text_type)
        assert direction in (SearchDirection.FORWARD, SearchDirection.BACKWARD)

        ignore_case = to_filter(ignore_case)

        self.text = text
        self.direction = direction
        self.ignore_case = ignore_case

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
