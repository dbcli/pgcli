"""
Layout dimensions are used to give the minimum, maximum and preferred
dimensions for containers and controls.
"""
from __future__ import unicode_literals

__all__ = (
    'Dimension',
    'sum_layout_dimensions',
    'max_layout_dimensions',
    'to_dimension',
)


class Dimension(object):
    """
    Specified dimension (width/height) of a user control or window.

    The layout engine tries to honor the preferred size. If that is not
    possible, because the terminal is larger or smaller, it tries to keep in
    between min and max.

    :param min: Minimum size.
    :param max: Maximum size.
    :param weight: For a VSplit/HSplit, the actual size will be determined
                   by taking the proportion of weights from all the children.
                   E.g. When there are two children, one width a weight of 1,
                   and the other with a weight of 2. The second will always be
                   twice as big as the first, if the min/max values allow it.
    :param preferred: Preferred size.
    """
    def __init__(self, min=None, max=None, weight=1, preferred=None):
        assert isinstance(weight, int) and weight >= 0   # Cannot be a float.
        assert min is None or min >= 0
        assert max is None or max >= 0
        assert preferred is None or preferred >= 0

        self.min_specified = min is not None
        self.max_specified = max is not None
        self.preferred_specified = preferred is not None

        if min is None:
            min = 0  # Smallest possible value.
        if max is None:  # 0-values are allowed, so use "is None"
            max = 1000 ** 10  # Something huge.
        if preferred is None:
            preferred = min

        self.min = min
        self.max = max
        self.preferred = preferred
        self.weight = weight

        # Make sure that the 'preferred' size is always in the min..max range.
        if self.preferred < self.min:
            self.preferred = self.min

        if self.preferred > self.max:
            self.preferred = self.max

    @classmethod
    def exact(cls, amount):
        """
        Return a :class:`.Dimension` with an exact size. (min, max and
        preferred set to ``amount``).
        """
        return cls(min=amount, max=amount, preferred=amount)

    @classmethod
    def zero(cls):
        """
        Create a dimension that represents a zero size. (Used for 'invisible'
        controls.)
        """
        return cls.exact(amount=0)

    def is_zero(self):
        " True if this `Dimension` represents a zero size. "
        return self.preferred == 0 or self.max == 0

    def __repr__(self):
        return 'Dimension(min=%r, max=%r, preferred=%r, weight=%r)' % (
            self.min, self.max, self.preferred, self.weight)


def sum_layout_dimensions(dimensions):
    """
    Sum a list of :class:`.Dimension` instances.
    """
    min = sum(d.min for d in dimensions)
    max = sum(d.max for d in dimensions)
    preferred = sum(d.preferred for d in dimensions)

    return Dimension(min=min, max=max, preferred=preferred)


def max_layout_dimensions(dimensions):
    """
    Take the maximum of a list of :class:`.Dimension` instances.
    Used when we have a HSplit/VSplit, and we want to get the best width/height.)
    """
    if not len(dimensions):
        return Dimension.zero()

    # If all dimensions are size zero. Return zero.
    # (This is important for HSplit/VSplit, to report the right values to their
    # parent when all children are invisible.)
    if all(d.is_zero() for d in dimensions):
        return dimensions[0]

    # Ignore empty dimensions. (They should not reduce the size of others.)
    dimensions = [d for d in dimensions if not d.is_zero()]

    if dimensions:
        # The the maximum dimension.
        # But we can't go larger than the smallest 'max'.
        min_ = max(d.min for d in dimensions)
        max_ = min(d.max for d in dimensions)
        preferred = max(d.preferred for d in dimensions)

        return Dimension(min=min_, max=max_, preferred=preferred)
    else:
        return Dimension()


def to_dimension(value):
    """
    Turn the given object into a `Dimension` object.
    """
    if value is None:
        return Dimension()
    if isinstance(value, int):
        return Dimension.exact(value)
    if isinstance(value, Dimension):
        return value

    raise ValueError('Not an integer or Dimension object.')


# For backward-compatibility.
LayoutDimension = Dimension
