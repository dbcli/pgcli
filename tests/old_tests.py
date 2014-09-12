#!/usr/bin/env python
"""

Old tests. To be cleaned up.

"""
from __future__ import unicode_literals

import unittest


#class PromptTest(unittest.TestCase):
#    def setUp(self):
#        self.line = Line()
#        self.line.insert_text('some text')
#
#        self.code = Code(self.line.document)
#        self.prompt = Prompt(self.line, self.code)
#
#    def _test_token_text_list(self, data):
#        # Test whether data is list of (Token, text) tuples.
#        for token, text in data:
#            self.assertIsInstance(token, pygments.token._TokenType)
#            self.assertIsInstance(text, six.text_type)
#
#    def test_get_prompt(self):
#        result = list(self.prompt.get_prompt())
#        self._test_token_text_list(result)
#
#    def test_second_line_prefix(self):
#        result = list(self.prompt.get_second_line_prefix())
#        self._test_token_text_list(result)
#
#    def test_get_help_tokens(self):
#        result = list(self.prompt.get_second_line_prefix())
#        self._test_token_text_list(result)
#

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

#    def test_literal_nomatch_suffix(self):
#        stream = TokenStream([ 'my-variable', 'suffix' ])
#        result = list(self.literal.parse(stream))
#
#        self.assertEqual(len(result), 0)

    def test_literal_nomatch_invalid(self):
        stream = TokenStream([ 'invalid' ])
        result = list(self.literal.parse(stream))

        self.assertEqual(len(result), 0)


#class VariableTest(unittest.TestCase):
#    def setUp(self):
#        self.variable = Variable(placeholder='my-variable', dest='destination')

