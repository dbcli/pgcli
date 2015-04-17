from .enums import IncrementalSearchDirection

__all__ = (
    'SearchState',
)


class SearchState(object):
    def __init__(self, text='', direction=IncrementalSearchDirection.FORWARD):
         self.text = text
         self.direction = direction

    def __repr__(self):
        return '%s(%r, direction=%r)' % (
            self.__class__.__name__, self.text, self.direction)

    def __invert__(self):
        """
        Create a new SearchState where backwards becomes forwards and the other
        way around.
        """
        if self.direction == IncrementalSearchDirection.BACKWARD:
            direction = IncrementalSearchDirection.FORWARD
        else:
            direction = IncrementalSearchDirection.BACKWARD

        return SearchState(text=self.text, direction=direction)
