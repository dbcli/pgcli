from __future__ import unicode_literals

from prompt_toolkit.utils import take_using_weights

import itertools


def test_using_weights():
    def take(generator, count):
        return list(itertools.islice(generator, 0, count))

    # Check distribution.
    data = take(take_using_weights(['A', 'B', 'C'], [5, 10, 20]), 35)
    assert data.count('A') == 5
    assert data.count('B') == 10
    assert data.count('C') == 20

    assert data == [
        'A', 'B', 'C', 'C', 'B', 'C', 'C', 'A', 'B', 'C', 'C', 'B', 'C',
        'C', 'A', 'B', 'C', 'C', 'B', 'C', 'C', 'A', 'B', 'C', 'C',
        'B', 'C', 'C', 'A', 'B', 'C', 'C', 'B', 'C', 'C']

    # Another order.
    data = take(take_using_weights(['A', 'B', 'C'], [20, 10, 5]), 35)
    assert data.count('A') == 20
    assert data.count('B') == 10
    assert data.count('C') == 5

    # Bigger numbers.
    data = take(take_using_weights(['A', 'B', 'C'], [20, 10, 5]), 70)
    assert data.count('A') == 40
    assert data.count('B') == 20
    assert data.count('C') == 10

    # Negative numbers.
    data = take(take_using_weights(['A', 'B', 'C'], [-20, 10, 0]), 70)
    assert data.count('A') == 0
    assert data.count('B') == 70
    assert data.count('C') == 0
