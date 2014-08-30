#!/usr/bin/env python
from __future__ import unicode_literals

import unittest
import six

from prompt_toolkit.inputstream import InputStream
from prompt_toolkit.line import Line, Document, ReturnInput


class _CLILogger(object):
    """ Dummy CLI class that records all the called methods. """
    def __init__(self):
        self.log = []

    def __call__(self, name, *a):
        self.log.append((name,) + a)


class InputProtocolTest(unittest.TestCase):
    def setUp(self):
        self.cli = _CLILogger()
        self.stream = InputStream(self.cli)

    def test_simple_feed_text(self):
        self.stream.feed('test')
        self.assertEqual(self.cli.log, [
                        ('insert_char', 't'),
                        ('insert_char', 'e'),
                        ('insert_char', 's'),
                        ('insert_char', 't')
                    ])

    def test_some_control_sequences(self):
        self.stream.feed('t\x01e\x02s\x03t\x04\x05\x06')
        self.assertEqual(self.cli.log, [
                        ('insert_char', 't'),
                        ('ctrl_a', ),
                        ('insert_char', 'e'),
                        ('ctrl_b', ),
                        ('insert_char', 's'),
                        ('ctrl_c', ),
                        ('insert_char', 't'),
                        ('ctrl_d', ),
                        ('ctrl_e', ),
                        ('ctrl_f', ),
                    ])

    def test_enter(self):
        self.stream.feed('A\rB\nC\t')
        self.assertEqual(self.cli.log, [
                        ('insert_char', 'A'),
                        ('ctrl_m', ),
                        ('insert_char', 'B'),
                        ('ctrl_j', ),
                        ('insert_char', 'C'),
                        ('ctrl_i', ),
                    ])

    def test_backspace(self):
        self.stream.feed('A\x7f')
        self.assertEqual(self.cli.log, [
                        ('insert_char', 'A'),
                        ('backspace', ),
                    ])

    def test_cursor_movement(self):
        self.stream.feed('\x1b[AA\x1b[BB\x1b[CC\x1b[DD')
        self.assertEqual(self.cli.log, [
                        ('arrow_up',),
                        ('insert_char', 'A'),
                        ('arrow_down',),
                        ('insert_char', 'B'),
                        ('arrow_right',),
                        ('insert_char', 'C'),
                        ('arrow_left',),
                        ('insert_char', 'D'),
                    ])

    def test_home_end(self):
        self.stream.feed('\x1b[H\x1b[F')
        self.stream.feed('\x1b[1~\x1b[4~') # tmux
        self.stream.feed('\x1b[7~\x1b[8~') # xrvt
        self.assertEqual(self.cli.log, [
                        ('home',), ('end',),
                        ('home',), ('end',),
                        ('home',), ('end',),
                    ])

    def test_page_up_down(self):
        self.stream.feed('\x1b[5~\x1b[6~')
        self.assertEqual(self.cli.log, [
                        ('page_up',),
                        ('page_down',),
                    ])

    def test_f_keys(self):
        # F1 - F4
        self.stream.feed('\x1bOP')
        self.stream.feed('\x1bOQ')
        self.stream.feed('\x1bOR')
        self.stream.feed('\x1bOS')

        # F5 - F10
        self.stream.feed('\x1b[15~')
        self.stream.feed('\x1b[17~')
        self.stream.feed('\x1b[18~')
        self.stream.feed('\x1b[19~')
        self.stream.feed('\x1b[20~')
        self.stream.feed('\x1b[21~')

        self.assertEqual(self.cli.log, [
                        ('F1',), ('F2',), ('F3',), ('F4',),
                        ('F5',), ('F6',), ('F7',), ('F8',), ('F9',), ('F10',),
                    ])


class LineTest(unittest.TestCase):
    def setUp(self):
        self.cli = Line()

    def test_setup(self):
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

    def test_home_end(self):
        self.cli.insert_text('some_text')
        self.cli.home()
        self.cli.insert_text('A')
        self.cli.end()
        self.cli.insert_text('B')
        self.assertEqual(self.cli.text, 'Asome_textB')
        self.assertEqual(self.cli.cursor_position, len('Asome_textB'))

    def test_backspace(self):
        self.cli.insert_text('some_text')
        self.cli.cursor_left()
        self.cli.cursor_left()
        self.cli.delete_character_before_cursor()

        self.assertEqual(self.cli.text, 'some_txt')
        self.assertEqual(self.cli.cursor_position, len('some_t'))

    def test_cursor_word_back(self):
        self.cli.insert_text('hello world word3')
        self.cli.cursor_word_back()

        self.assertEqual(self.cli.text, 'hello world word3')
        self.assertEqual(self.cli.cursor_position, len('hello world '))

    def test_cursor_to_start_of_line(self):
        self.cli.insert_text('hello world\n  line2\nline3')
        self.assertEqual(self.cli.cursor_position, len('hello world\n  line2\nline3'))
        self.cli.cursor_position = len('hello world\n  li') # Somewhere on the second line.

        self.cli.cursor_to_start_of_line()
        self.assertEqual(self.cli.cursor_position, len('hello world\n'))

        self.cli.cursor_to_start_of_line(after_whitespace=True)
        self.assertEqual(self.cli.cursor_position, len('hello world\n  '))

    def test_cursor_to_end_of_line(self):
        self.cli.insert_text('hello world\n  line2\nline3')
        self.cli.cursor_position = 0

        self.cli.cursor_to_end_of_line()
        self.assertEqual(self.cli.cursor_position, len('hello world'))

    def test_cursor_word_forward(self):
        self.cli.insert_text('hello world word3')
        self.cli.home()
        self.cli.cursor_word_forward()

        self.assertEqual(self.cli.text, 'hello world word3')
        self.assertEqual(self.cli.cursor_position, len('hello '))

    def test_cursor_to_end_of_word(self):
        self.cli.insert_text('hello world')
        self.cli.home()

        self.cli.cursor_to_end_of_word()
        self.assertEqual(self.cli.cursor_position, len('hello') - 1)

        self.cli.cursor_to_end_of_word()
        self.assertEqual(self.cli.cursor_position, len('hello world') - 1)

    def test_delete_word(self):
        self.cli.insert_text('hello world word3')
        self.cli.home()
        self.cli.cursor_word_forward()
        self.cli.delete_word()

        self.assertEqual(self.cli.text, 'hello word3')
        self.assertEqual(self.cli.cursor_position, len('hello '))

    def test_delete_until_end(self):
        self.cli.insert_text('this is a sentence.')
        self.cli.home()
        self.cli.cursor_word_forward()
        self.cli.delete_until_end()

        self.assertEqual(self.cli.text, 'this ')
        self.assertEqual(self.cli.cursor_position, len('this '))

    def test_delete_until_end_of_line(self):
        self.cli.insert_text('line1\nline2\nline3')
        self.cli.cursor_position = len('line1\nli')

        deleted_text = self.cli.delete_until_end_of_line()

        self.assertEqual(self.cli.text, 'line1\nli\nline3')
        self.assertEqual(deleted_text, 'ne2')

        # If we only have one line.
        self.cli.reset()
        self.cli.insert_text('line1')
        self.cli.cursor_position = 2

        deleted_text = self.cli.delete_until_end_of_line()

        self.assertEqual(self.cli.text, 'li')
        self.assertEqual(deleted_text, 'ne1')

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

    def test_auto_up_and_down(self):
        self.cli.insert_text('line1\nline2')
        with self.assertRaises(ReturnInput):
            self.cli.return_input()
        self.cli.insert_text('long line3\nlong line4')

        # Test current
        self.assertEqual(self.cli.text, 'long line3\nlong line4')
        self.assertEqual(self.cli.cursor_position, len('long line3\nlong line4'))

        # Go up.
        self.cli.auto_up()
        self.assertEqual(self.cli.text, 'long line3\nlong line4')
        self.assertEqual(self.cli.cursor_position, len('long line3'))

        # Go up again (goes to first item.)
        self.cli.auto_up()
        self.assertEqual(self.cli.text, 'line1\nline2')
        self.assertEqual(self.cli.cursor_position, len('line1\nline2'))

        # Go up again (goes to first line of first item.)
        self.cli.auto_up()
        self.assertEqual(self.cli.text, 'line1\nline2')
        self.assertEqual(self.cli.cursor_position, len('line1'))

        # Go up again (while we're at the first item in history.)
        # (Nothing changes.)
        self.cli.auto_up()
        self.assertEqual(self.cli.text, 'line1\nline2')
        self.assertEqual(self.cli.cursor_position, len('line1'))

        # Go down (to second line of first item.)
        self.cli.auto_down()
        self.assertEqual(self.cli.text, 'line1\nline2')
        self.assertEqual(self.cli.cursor_position, len('line1\nline2'))

        # Go down again (to first line of second item.)
        # (Going down goes to the first character of a line.)
        self.cli.auto_down()
        self.assertEqual(self.cli.text, 'long line3\nlong line4')
        self.assertEqual(self.cli.cursor_position, len(''))

        # Go down again (to second line of second item.)
        self.cli.auto_down()
        self.assertEqual(self.cli.text, 'long line3\nlong line4')
        self.assertEqual(self.cli.cursor_position, len('long line3\n'))

        # Go down again after the last line. (nothing should happen.)
        self.cli.auto_down()
        self.assertEqual(self.cli.text, 'long line3\nlong line4')
        self.assertEqual(self.cli.cursor_position, len('long line3\n'))

    def test_delete_current_line(self):
        self.cli.insert_text('line1\nline2\nline3')
        self.cli.cursor_up()

        deleted_text = self.cli.delete_current_line()

        self.assertEqual(self.cli.text, 'line1\nline3')
        self.assertEqual(deleted_text, 'line2')
        self.assertEqual(self.cli.cursor_position, len('line1\n'))

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

    def test_go_to_matching_bracket(self):
        self.cli.insert_text('A ( B [ C ) >')
        self.cli.home()
        self.cli.cursor_right()
        self.cli.cursor_right()

        self.assertEqual(self.cli.cursor_position, 2)
        self.cli.go_to_matching_bracket()
        self.assertEqual(self.cli.cursor_position, 10)
        self.cli.go_to_matching_bracket()
        self.assertEqual(self.cli.cursor_position, 2)

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


class DocumentTest(unittest.TestCase):
    def setUp(self):
        self.document = Document(
                    'line 1\n' +
                    'line 2\n' +
                    'line 3\n' +
                    'line 4\n',
                    len(
                        'line 1\n' +
                        'lin')
                )

    def test_current_char(self):
        self.assertEqual(self.document.current_char, 'e')

    def test_text_before_cursor(self):
        self.assertEqual(self.document.text_before_cursor, 'line 1\nlin')

    def test_text_after_cursor(self):
        self.assertEqual(self.document.text_after_cursor,
                    'e 2\n' +
                    'line 3\n' +
                    'line 4\n')

    def test_lines(self):
        self.assertEqual(self.document.lines, [
                    'line 1',
                    'line 2',
                    'line 3',
                    'line 4', '' ])

    def test_line_count(self):
        self.assertEqual(self.document.line_count, 5)

    def test_current_line_before_cursor(self):
        self.assertEqual(self.document.current_line_before_cursor, 'lin')

    def test_current_line_after_cursor(self):
        self.assertEqual(self.document.current_line_after_cursor, 'e 2')

    def test_current_line(self):
        self.assertEqual(self.document.current_line, 'line 2')

    def test_cursor_position(self):
        self.assertEqual(self.document.cursor_position_row, 1)
        self.assertEqual(self.document.cursor_position_col, 3)

        d = Document('', 0)
        self.assertEqual(d.cursor_position_row, 0)
        self.assertEqual(d.cursor_position_col, 0)

    def test_translate_index_to_position(self):
        pos = self.document.translate_index_to_position(
                len('line 1\nline 2\nlin'))

        self.assertEqual(pos[0], 3)
        self.assertEqual(pos[1], 3)

    def test_cursor_at_end(self):
        doc = Document('hello', 3)
        self.assertEqual(doc.cursor_at_the_end, False)

        doc2 = Document('hello', 5)
        self.assertEqual(doc2.cursor_at_the_end, True)


from prompt_toolkit.code import Code
from prompt_toolkit.prompt import Prompt

import pygments

class PromptTest(unittest.TestCase):
    def setUp(self):
        self.line = Line()
        self.line.insert_text('some text')

        self.code = Code(self.line.document)
        self.prompt = Prompt(self.line, self.code)

    def _test_token_text_list(self, data):
        # Test whether data is list of (Token, text) tuples.
        for token, text in data:
            self.assertIsInstance(token, pygments.token._TokenType)
            self.assertIsInstance(text, six.text_type)

    def test_get_prompt(self):
        result = list(self.prompt.get_prompt())
        self._test_token_text_list(result)

    def test_second_line_prefix(self):
        result = list(self.prompt.get_second_line_prefix())
        self._test_token_text_list(result)

    def test_get_help_tokens(self):
        result = list(self.prompt.get_second_line_prefix())
        self._test_token_text_list(result)


#--


from prompt_toolkit.contrib.shell.lexer import ParametersLexer, TextToken
from pygments.token import Token

class ParameterLexerTest(unittest.TestCase):
    def setUp(self):
        self.lexer = ParametersLexer(stripnl=False, stripall=False, ensurenl=False)

    def test_simple(self):
        t = list(self.lexer.get_tokens('aaa bbb ccc'))
        self.assertEqual(t, [
            (Token.Text, 'aaa'),
            (Token.WhiteSpace, ' '),
            (Token.Text, 'bbb'),
            (Token.WhiteSpace, ' '),
            (Token.Text, 'ccc') ])

    def test_complex(self):
        t = list(self.lexer.get_tokens('''a'a 'a " b "bb ccc\\'''))
        # The tokenizer separates text and whitespace, but keeps all the characters.
        self.assertEqual(t, [
            (Token.Text, "a'a 'a"),
            (Token.WhiteSpace, ' '),
            (Token.Text, '" b "bb'),
            (Token.WhiteSpace, ' '),
            (Token.Text, 'ccc\\') ])


class TextTokenTest(unittest.TestCase):
    def test_simple(self):
        t = TextToken('hello')
        t.unescaped_text = 'hello'

    def test_double_quotes(self):
        t = TextToken('h"e"llo" wor"ld')
        self.assertEqual(t.unescaped_text, 'hello world')
        self.assertEqual(t.inside_double_quotes, False)
        self.assertEqual(t.inside_single_quotes, False)
        self.assertEqual(t.trailing_backslash, False)

    def test_single_quotes(self):
        t = TextToken("h'e'llo' wo'rld")
        self.assertEqual(t.unescaped_text, 'hello world')
        self.assertEqual(t.inside_double_quotes, False)
        self.assertEqual(t.inside_single_quotes, False)
        self.assertEqual(t.trailing_backslash, False)

    def test_backslashes(self):
        t = TextToken("hello\ wo\\rld")
        self.assertEqual(t.unescaped_text, 'hello world')
        self.assertEqual(t.inside_double_quotes, False)
        self.assertEqual(t.inside_single_quotes, False)
        self.assertEqual(t.trailing_backslash, False)

    def test_open_double_quote(self):
        t = TextToken('he"llo world')
        self.assertEqual(t.unescaped_text, 'hello world')
        self.assertEqual(t.inside_double_quotes, True)
        self.assertEqual(t.inside_single_quotes, False)
        self.assertEqual(t.trailing_backslash, False)

    def test_open_single_quote(self):
        t = TextToken("he'llo world")
        self.assertEqual(t.unescaped_text, 'hello world')
        self.assertEqual(t.inside_double_quotes, False)
        self.assertEqual(t.inside_single_quotes, True)
        self.assertEqual(t.trailing_backslash, False)

    def test_trailing_backslash(self):
        t = TextToken("hello\\ world\\")
        self.assertEqual(t.unescaped_text, 'hello world')
        self.assertEqual(t.inside_double_quotes, False)
        self.assertEqual(t.inside_single_quotes, False)
        self.assertEqual(t.trailing_backslash, True)

#---

from prompt_toolkit.contrib.shell.rules import TokenStream

class TokenStreamTest(unittest.TestCase):
    def test_tokenstream(self):
        s = TokenStream([ 'aaa', 'bbb', 'ccc',  ])

        # Test top
        self.assertEqual(s.first_token, 'aaa')
        self.assertEqual(s.has_more_tokens, True)

        # Pop
        self.assertEqual(s.pop(), 'aaa')
        self.assertEqual(s.first_token, 'bbb')
        self.assertEqual(s.has_more_tokens, True)

        # Test restore point
        with s.restore_point:
            self.assertEqual(s.pop(), 'bbb')
            self.assertEqual(s.first_token, 'ccc')
            self.assertEqual(s.pop(), 'ccc')

            self.assertEqual(s.has_more_tokens, False)
            self.assertEqual(s.first_token, None)

        # State should have been restored after the with block.
        self.assertEqual(s.first_token, 'bbb')
        self.assertEqual(s.has_more_tokens, True)

#--

from prompt_toolkit.contrib.shell.rules import Literal
from prompt_toolkit.contrib.shell.nodes import LiteralNode

class LiteralTest(unittest.TestCase):
    def setUp(self):
        self.literal = Literal('my-variable', dest='key')

    def test_literal_match(self):
        stream = TokenStream([ 'my-variable' ])
        result = list(self.literal.parse(stream))

        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], LiteralNode)
        self.assertEqual(result[0].rule, self.literal)
        self.assertEqual(result[0]._text, 'my-variable')
        self.assertEqual(result[0].get_variables(), { 'key': 'my-variable' })

    def test_literal_nomatch_suffix(self):
        stream = TokenStream([ 'my-variable', 'suffix' ])
        result = list(self.literal.parse(stream))

        self.assertEqual(len(result), 0)

    def test_literal_nomatch_invalid(self):
        stream = TokenStream([ 'invalid' ])
        result = list(self.literal.parse(stream))

        self.assertEqual(len(result), 0)


#class VariableTest(unittest.TestCase):
#    def setUp(self):
#        self.variable = Variable(placeholder='my-variable', dest='destination')


if __name__ == '__main__':
   unittest.main()
