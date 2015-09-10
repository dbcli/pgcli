"""
Layout dimensions are used to give the minimum, maximum and preferred
dimensions for containers and controls.
"""
from __future__ import unicode_literals

__all__ = (
    'LayoutDimension',
    'sum_layout_dimensions',
    'max_layout_dimensions',
)


class LayoutDimension(object):
    def __init__(self, min=None, max=None, preferred=None):
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

        # Make sure that the 'preferred' size is always in the min..max range.
        if self.preferred < self.min:
            self.preferred = self.min

        if self.preferred > self.max:
            self.preferred = self.max

    @classmethod
    def exact(cls, amount):
        return cls(min=amount, max=amount, preferred=amount)

    def __repr__(self):
        return 'LayoutDimension(min=%r, max=%r, preferred=%r)' % (self.min, self.max, self.preferred)

    def __add__(self, other):
        return sum_layout_dimensions([self, other])


def sum_layout_dimensions(dimensions):
    """
    Sum a list of `LayoutDimension` instances.
    """
    min = sum([d.min for d in dimensions if d.min is not None])
    max = sum([d.max for d in dimensions if d.max is not None])
    preferred = sum([d.preferred for d in dimensions])

    return LayoutDimension(min=min, max=max, preferred=preferred)


def max_layout_dimensions(dimensions):
    """
    Take the maximum of a list of `LayoutDimension` instances.
    """
    min_ = max([d.min for d in dimensions if d.min is not None])
    max_ = max([d.max for d in dimensions if d.max is not None])
    preferred = max([d.preferred for d in dimensions])

    return LayoutDimension(min=min_, max=max_, preferred=preferred)
