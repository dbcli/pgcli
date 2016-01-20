from __future__ import unicode_literals

from prompt_toolkit.layout.utils import split_lines
from prompt_toolkit.token import Token

import unittest


class SplitLinesTest(unittest.TestCase):
    def test_split_lines(self):
        lines = list(split_lines([(Token.A, 'line1\nline2\nline3')]))

        self.assertEqual(lines, [
            [(Token.A, 'line1')],
            [(Token.A, 'line2')],
            [(Token.A, 'line3')],
        ])

    def test_split_lines_2(self):
        lines = list(split_lines([
            (Token.A, 'line1'),
            (Token.B, 'line2\nline3\nline4')
        ]))

        self.assertEqual(lines, [
            [(Token.A, 'line1'), (Token.B, 'line2')],
            [(Token.B, 'line3')],
            [(Token.B, 'line4')],
        ])
