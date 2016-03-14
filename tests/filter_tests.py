from __future__ import unicode_literals
from prompt_toolkit.filters import Condition, Never, Always, Filter
from prompt_toolkit.filters.types import CLIFilter, SimpleFilter
from prompt_toolkit.filters.utils import to_cli_filter, to_simple_filter
from prompt_toolkit.filters.cli import HasArg, HasFocus, HasSelection

import unittest


class FilterTest(unittest.TestCase):
    def test_condition_filter_args(self):
        c = Condition(lambda a, b, c:True)
        self.assertTrue(c.test_args('a', 'b', 'c'))
        self.assertFalse(c.test_args())
        self.assertFalse(c.test_args('a'))
        self.assertFalse(c.test_args('a', 'b'))
        self.assertFalse(c.test_args('a', 'b', 'c', 'd'))

        c2 = Condition(lambda a, b=1:True)
        self.assertTrue(c2.test_args('a'))
        self.assertTrue(c2.test_args('a', 'b'))
        self.assertFalse(c2.test_args('a', 'b', 'c'))
        self.assertFalse(c2.test_args())

        c3 = Condition(lambda *a: True)
        self.assertTrue(c3.test_args())
        self.assertTrue(c3.test_args('a'))
        self.assertTrue(c3.test_args('a', 'b'))

    def test_and_arg(self):
        c1 = Condition(lambda a: True)
        c2 = Condition(lambda a: True)
        c3 = c1 & c2

        self.assertTrue(c3.test_args('a'))
        self.assertFalse(c3.test_args())
        self.assertFalse(c3.test_args('a', 'b'))

    def test_or_arg(self):
        c1 = Condition(lambda a: True)
        c2 = Condition(lambda a: True)
        c3 = c1 | c2

        self.assertTrue(c3.test_args('a'))
        self.assertFalse(c3.test_args())
        self.assertFalse(c3.test_args('a', 'b'))

    def test_condition(self):
        c = Condition(lambda a: a % 2 == 0)
        self.assertTrue(c(4))
        self.assertTrue(c(6))
        self.assertFalse(c(5))
        self.assertFalse(c(3))

    def test_never(self):
        self.assertFalse(Never()())

    def test_always(self):
        self.assertTrue(Always()())

    def test_invert(self):
        self.assertFalse((~Always())())
        self.assertTrue((~Never()()))

        c = ~Condition(lambda: False)
        self.assertTrue(c())

    def test_or(self):
        for a in (True, False):
            for b in (True, False):
                c1 = Condition(lambda: a)
                c2 = Condition(lambda: b)
                c3 = c1 | c2

                self.assertTrue(isinstance(c3, Filter))
                self.assertEqual(c3(), a or b)

    def test_and(self):
        for a in (True, False):
            for b in (True, False):
                c1 = Condition(lambda: a)
                c2 = Condition(lambda: b)
                c3 = c1 & c2

                self.assertTrue(isinstance(c3, Filter))
                self.assertEqual(c3(), a and b)

    def test_cli_filter(self):
        c1 = Condition(lambda cli: True)
        self.assertTrue(isinstance(c1, CLIFilter))
        self.assertFalse(isinstance(c1, SimpleFilter))

        c2 = Condition(lambda: True)
        self.assertFalse(isinstance(c2, CLIFilter))
        self.assertTrue(isinstance(c2, SimpleFilter))

        c3 = c1 | c2
        self.assertFalse(isinstance(c3, CLIFilter))
        self.assertFalse(isinstance(c3, SimpleFilter))

        c4 = Condition(lambda cli: True)
        c5 = Condition(lambda cli: True)
        c6 = c4 & c5
        c7 = c4 | c5
        self.assertTrue(isinstance(c6, CLIFilter))
        self.assertTrue(isinstance(c7, CLIFilter))
        self.assertFalse(isinstance(c6, SimpleFilter))
        self.assertFalse(isinstance(c7, SimpleFilter))

        c8 = Condition(lambda *args: True)
        self.assertTrue(isinstance(c8, CLIFilter))
        self.assertTrue(isinstance(c8, SimpleFilter))

    def test_to_cli_filter(self):
        f1 = to_cli_filter(True)
        f2 = to_cli_filter(False)
        f3 = to_cli_filter(Condition(lambda cli: True))
        f4 = to_cli_filter(Condition(lambda cli: False))

        self.assertTrue(isinstance(f1, CLIFilter))
        self.assertTrue(isinstance(f2, CLIFilter))
        self.assertTrue(isinstance(f3, CLIFilter))
        self.assertTrue(isinstance(f4, CLIFilter))
        self.assertTrue(f1(None))
        self.assertFalse(f2(None))
        self.assertTrue(f3(None))
        self.assertFalse(f4(None))

        self.assertRaises(TypeError, to_cli_filter, 4)
        self.assertRaises(TypeError, to_cli_filter, Condition(lambda: True))

    def test_to_simple_filter(self):
        f1 = to_simple_filter(True)
        f2 = to_simple_filter(False)
        f3 = to_simple_filter(Condition(lambda: True))
        f4 = to_simple_filter(Condition(lambda: False))

        self.assertTrue(isinstance(f1, SimpleFilter))
        self.assertTrue(isinstance(f2, SimpleFilter))
        self.assertTrue(isinstance(f3, SimpleFilter))
        self.assertTrue(isinstance(f4, SimpleFilter))
        self.assertTrue(f1())
        self.assertFalse(f2())
        self.assertTrue(f3())
        self.assertFalse(f4())

        self.assertRaises(TypeError, to_simple_filter, 4)
        self.assertRaises(TypeError, to_simple_filter, Condition(lambda cli: True))

    def test_cli_filters(self):
        self.assertTrue(isinstance(HasArg(), CLIFilter))
        self.assertTrue(isinstance(HasFocus('BUFFER_NAME'), CLIFilter))
        self.assertTrue(isinstance(HasSelection(), CLIFilter))
