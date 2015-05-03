from __future__ import unicode_literals

from prompt_toolkit.buffer import Buffer

import unittest


class BufferTest(unittest.TestCase):
    def setUp(self):
        self.buffer = Buffer()

    def test_initial(self):
        self.assertEqual(self.buffer.text, '')
        self.assertEqual(self.buffer.cursor_position, 0)

    def test_insert_text(self):
        self.buffer.insert_text('some_text')
        self.assertEqual(self.buffer.text, 'some_text')
        self.assertEqual(self.buffer.cursor_position, len('some_text'))

    def test_cursor_movement(self):
        self.buffer.insert_text('some_text')
        self.buffer.cursor_left()
        self.buffer.cursor_left()
        self.buffer.cursor_left()
        self.buffer.cursor_right()
        self.buffer.insert_text('A')

        self.assertEqual(self.buffer.text, 'some_teAxt')
        self.assertEqual(self.buffer.cursor_position, len('some_teA'))

    def test_backspace(self):
        self.buffer.insert_text('some_text')
        self.buffer.cursor_left()
        self.buffer.cursor_left()
        self.buffer.delete_before_cursor()

        self.assertEqual(self.buffer.text, 'some_txt')
        self.assertEqual(self.buffer.cursor_position, len('some_t'))

    def test_cursor_up(self):
        # Cursor up to a line thats longer.
        self.buffer.insert_text('long line1\nline2')
        self.buffer.cursor_up()

        self.assertEqual(self.buffer.document.cursor_position, 5)

        # Going up when already at the top.
        self.buffer.cursor_up()
        self.assertEqual(self.buffer.document.cursor_position, 5)

        # Going up to a line that's shorter.
        self.buffer.reset()
        self.buffer.insert_text('line1\nlong line2')

        self.buffer.cursor_up()
        self.assertEqual(self.buffer.document.cursor_position, 5)

    def test_cursor_down(self):
        self.buffer.insert_text('line1\nline2')
        self.buffer.cursor_position = 3

        # Normally going down
        self.buffer.cursor_down()
        self.assertEqual(self.buffer.document.cursor_position, len('line1\nlin'))

        # Going down to a line that's storter.
        self.buffer.reset()
        self.buffer.insert_text('long line1\na\nb')
        self.buffer.cursor_position = 3

        self.buffer.cursor_down()
        self.assertEqual(self.buffer.document.cursor_position, len('long line1\na'))

    def test_join_next_line(self):
        self.buffer.insert_text('line1\nline2\nline3')
        self.buffer.cursor_up()
        self.buffer.join_next_line()

        self.assertEqual(self.buffer.text, 'line1\nline2 line3')

        # Test when there is no '\n' in the text
        self.buffer.reset()
        self.buffer.insert_text('line1')
        self.buffer.cursor_position = 0
        self.buffer.join_next_line()

        self.assertEqual(self.buffer.text, 'line1')

    def test_newline(self):
        self.buffer.insert_text('hello world')
        self.buffer.newline()

        self.assertEqual(self.buffer.text, 'hello world\n')

    def test_swap_characters_before_cursor(self):
        self.buffer.insert_text('hello world')
        self.buffer.cursor_left()
        self.buffer.cursor_left()
        self.buffer.swap_characters_before_cursor()

        self.assertEqual(self.buffer.text, 'hello wrold')
