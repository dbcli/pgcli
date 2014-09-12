from __future__ import unicode_literals

from prompt_toolkit.line import Line

import unittest


class LineTest(unittest.TestCase):
    def setUp(self):
        self.cli = Line()

    def test_initial(self):
        self.assertEqual(self.cli.text, '')
        self.assertEqual(self.cli.cursor_position, 0)

    def test_insert_text(self):
        self.cli.insert_text('some_text')
        self.assertEqual(self.cli.text, 'some_text')
        self.assertEqual(self.cli.cursor_position, len('some_text'))

    def test_cursor_movement(self):
        self.cli.insert_text('some_text')
        self.cli.cursor_left()
        self.cli.cursor_left()
        self.cli.cursor_left()
        self.cli.cursor_right()
        self.cli.insert_text('A')

        self.assertEqual(self.cli.text, 'some_teAxt')
        self.assertEqual(self.cli.cursor_position, len('some_teA'))

    def test_backspace(self):
        self.cli.insert_text('some_text')
        self.cli.cursor_left()
        self.cli.cursor_left()
        self.cli.delete_before_cursor()

        self.assertEqual(self.cli.text, 'some_txt')
        self.assertEqual(self.cli.cursor_position, len('some_t'))

    def test_cursor_up(self):
        # Cursor up to a line thats longer.
        self.cli.insert_text('long line1\nline2')
        self.cli.cursor_up()

        self.assertEqual(self.cli.document.cursor_position, 5)

        # Going up when already at the top.
        self.cli.cursor_up()
        self.assertEqual(self.cli.document.cursor_position, 5)

        # Going up to a line that's shorter.
        self.cli.reset()
        self.cli.insert_text('line1\nlong line2')

        self.cli.cursor_up()
        self.assertEqual(self.cli.document.cursor_position, 5)

    def test_cursor_down(self):
        self.cli.insert_text('line1\nline2')
        self.cli.cursor_position = 3

        # Normally going down
        self.cli.cursor_down()
        self.assertEqual(self.cli.document.cursor_position, len('line1\nlin'))

        # Going down to a line that's storter.
        self.cli.reset()
        self.cli.insert_text('long line1\na\nb')
        self.cli.cursor_position = 3

        self.cli.cursor_down()
        self.assertEqual(self.cli.document.cursor_position, len('long line1\na'))

#    def test_auto_up_and_down(self):
#        self.cli.insert_text('long line3\nlong line4')
#
#        # Test current
#        self.assertEqual(self.cli.text, 'long line3\nlong line4')
#        self.assertEqual(self.cli.cursor_position, len('long line3\nlong line4'))
#
#        # Go up.
#        self.cli.auto_up()
#        self.assertEqual(self.cli.text, 'long line3\nlong line4')
#        self.assertEqual(self.cli.cursor_position, len('long line3'))
#
#        # Go up again (goes to first item.)
#        self.cli.auto_up()
#        self.assertEqual(self.cli.text, 'line1\nline2')
#        self.assertEqual(self.cli.cursor_position, len('line1\nline2'))
#
#        # Go up again (goes to first line of first item.)
#        self.cli.auto_up()
#        self.assertEqual(self.cli.text, 'line1\nline2')
#        self.assertEqual(self.cli.cursor_position, len('line1'))
#
#        # Go up again (while we're at the first item in history.)
#        # (Nothing changes.)
#        self.cli.auto_up()
#        self.assertEqual(self.cli.text, 'line1\nline2')
#        self.assertEqual(self.cli.cursor_position, len('line1'))
#
#        # Go down (to second line of first item.)
#        self.cli.auto_down()
#        self.assertEqual(self.cli.text, 'line1\nline2')
#        self.assertEqual(self.cli.cursor_position, len('line1\nline2'))
#
#        # Go down again (to first line of second item.)
#        # (Going down goes to the first character of a line.)
#        self.cli.auto_down()
#        self.assertEqual(self.cli.text, 'long line3\nlong line4')
#        self.assertEqual(self.cli.cursor_position, len(''))
#
#        # Go down again (to second line of second item.)
#        self.cli.auto_down()
#        self.assertEqual(self.cli.text, 'long line3\nlong line4')
#        self.assertEqual(self.cli.cursor_position, len('long line3\n'))
#
#        # Go down again after the last line. (nothing should happen.)
#        self.cli.auto_down()
#        self.assertEqual(self.cli.text, 'long line3\nlong line4')
#        self.assertEqual(self.cli.cursor_position, len('long line3\n'))

    def test_join_next_line(self):
        self.cli.insert_text('line1\nline2\nline3')
        self.cli.cursor_up()
        self.cli.join_next_line()

        self.assertEqual(self.cli.text, 'line1\nline2line3')

        # Test when there is no '\n' in the text
        self.cli.reset()
        self.cli.insert_text('line1')
        self.cli.cursor_position = 0
        self.cli.join_next_line()

        self.assertEqual(self.cli.text, 'line1')

    def test_newline(self):
        self.cli.insert_text('hello world')
        self.cli.newline()

        self.assertEqual(self.cli.text, 'hello world\n')

    def test_swap_characters_before_cursor(self):
        self.cli.insert_text('hello world')
        self.cli.cursor_left()
        self.cli.cursor_left()
        self.cli.swap_characters_before_cursor()

        self.assertEqual(self.cli.text, 'hello wrold')
