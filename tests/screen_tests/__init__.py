from __future__ import unicode_literals

from prompt_toolkit.renderer import Screen, Char, Size, Point
from pygments.token import Token

import unittest


class ScreenTest(unittest.TestCase):
    def setUp(self):
        self.screen = Screen(Size(rows=10, columns=80))

    def test_current_height(self):
        # Screen is still empty, so it doesn't have a height.
        self.assertEqual(self.screen.current_height, 1)

        # After writing a character.
        self.screen._buffer[5][0] = Char()
        self.assertEqual(self.screen.current_height, 6)

    def test_get_cursor_position(self):
        # Test initial position
        self.assertEqual(self.screen.get_cursor_position(), Point(y=0, x=0))

        # Test after writing something.
        self.screen.write_char('w', Token)
        self.screen.write_char('x', Token)
        self.screen.write_char('y', Token, set_cursor_position=True)
        self.screen.write_char('z', Token)
        self.assertEqual(self.screen.get_cursor_position(), Point(y=0, x=2))

    def test_write_char(self):
        self.screen.write_char('x', Token.X)
        self.screen.write_char('y', Token.Y)
        self.screen.write_char('z', Token.Z)
        self.screen.write_char('\n', Token)
        self.screen.write_char('a', Token.A)
        self.screen.write_char('b', Token.B)
        self.screen.write_char('c', Token.C)

        self.assertEqual(self.screen._buffer[0][0].char, 'x')
        self.assertEqual(self.screen._buffer[0][1].char, 'y')
        self.assertEqual(self.screen._buffer[0][2].char, 'z')
        self.assertEqual(self.screen._buffer[1][0].char, 'a')
        self.assertEqual(self.screen._buffer[1][1].char, 'b')
        self.assertEqual(self.screen._buffer[1][2].char, 'c')

        self.assertEqual(self.screen._buffer[0][0].token, Token.X)
        self.assertEqual(self.screen._buffer[0][1].token, Token.Y)
        self.assertEqual(self.screen._buffer[0][2].token, Token.Z)
        self.assertEqual(self.screen._buffer[1][0].token, Token.A)
        self.assertEqual(self.screen._buffer[1][1].token, Token.B)
        self.assertEqual(self.screen._buffer[1][2].token, Token.C)

    def test_write_at_pos(self):
        # Test first write
        x = Char('x', Token.X, z_index=0)
        self.screen.write_at_pos(5, 3, x)
        self.assertEqual(self.screen._buffer[5][3], x)

        # Test higher z_index.
        y = Char('y', Token.Y, z_index=10)
        self.screen.write_at_pos(5, 3, y)
        self.assertEqual(self.screen._buffer[5][3], y)

        # Test lower z_index. (Should not replace.)
        z = Char('z', Token.Z, z_index=8)
        self.screen.write_at_pos(5, 3, z)
        self.assertEqual(self.screen._buffer[5][3], y)

    def test_write_highlighted_at_pos(self):
        self.screen.write_highlighted_at_pos(4, 2, [(Token.ABC, 'abc'), (Token.DEF, 'def')])

        self.assertEqual(self.screen._buffer[4][2].char, 'a')
        self.assertEqual(self.screen._buffer[4][3].char, 'b')
        self.assertEqual(self.screen._buffer[4][4].char, 'c')
        self.assertEqual(self.screen._buffer[4][2].token, Token.ABC)
        self.assertEqual(self.screen._buffer[4][3].token, Token.ABC)
        self.assertEqual(self.screen._buffer[4][4].token, Token.ABC)

        self.assertEqual(self.screen._buffer[4][5].char, 'd')
        self.assertEqual(self.screen._buffer[4][6].char, 'e')
        self.assertEqual(self.screen._buffer[4][7].char, 'f')
        self.assertEqual(self.screen._buffer[4][5].token, Token.DEF)
        self.assertEqual(self.screen._buffer[4][6].token, Token.DEF)
        self.assertEqual(self.screen._buffer[4][7].token, Token.DEF)

    def test_write_highlighted(self):
        self.screen.write_highlighted([(Token.ABC, 'abc'), (Token.DEF, 'def')])
        self.screen.write_highlighted([(Token.GHI, 'ghi'), (Token.JKL, 'jkl')])

        self.assertEqual(self.screen._buffer[0][4].char, 'e')
        self.assertEqual(self.screen._buffer[0][8].char, 'i')

        self.assertEqual(self.screen._buffer[0][4].token, Token.DEF)
        self.assertEqual(self.screen._buffer[0][8].token, Token.GHI)
