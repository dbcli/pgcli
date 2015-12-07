from __future__ import unicode_literals

from prompt_toolkit.utils import take_using_weights

import unittest
import itertools


class SplitLinesTest(unittest.TestCase):
    def test_using_weights(self):
        def take(generator, count):
            return list(itertools.islice(generator, 0, count))

        # Check distribution.
        data = take(take_using_weights(['A', 'B', 'C'], [5, 10, 20]), 35)
        self.assertEqual(data.count('A'), 5)
        self.assertEqual(data.count('B'), 10)
        self.assertEqual(data.count('C'), 20)

        self.assertEqual(data,
            ['A', 'B', 'C', 'C', 'B', 'C', 'C', 'A', 'B', 'C', 'C', 'B', 'C',
             'C', 'A', 'B', 'C', 'C', 'B', 'C', 'C', 'A', 'B', 'C', 'C',
             'B', 'C', 'C', 'A', 'B', 'C', 'C', 'B', 'C', 'C'])

        # Another order.
        data = take(take_using_weights(['A', 'B', 'C'], [20, 10, 5]), 35)
        self.assertEqual(data.count('A'), 20)
        self.assertEqual(data.count('B'), 10)
        self.assertEqual(data.count('C'), 5)

        # Bigger numbers.
        data = take(take_using_weights(['A', 'B', 'C'], [20, 10, 5]), 70)
        self.assertEqual(data.count('A'), 40)
        self.assertEqual(data.count('B'), 20)
        self.assertEqual(data.count('C'), 10)

        # Negative numbers.
        data = take(take_using_weights(['A', 'B', 'C'], [-20, 10, 0]), 70)
        self.assertEqual(data.count('A'), 0)
        self.assertEqual(data.count('B'), 70)
        self.assertEqual(data.count('C'), 0)
