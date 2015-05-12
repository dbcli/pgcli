from __future__ import unicode_literals

from prompt_toolkit.contrib.regular_languages import compile
from prompt_toolkit.contrib.regular_languages.compiler import Match, Variables
from prompt_toolkit.contrib.regular_languages.completion import GrammarCompleter
from prompt_toolkit.completion import Completer, Completion, CompleteEvent
from prompt_toolkit.document import Document

import unittest


class GrammarTest(unittest.TestCase):
    def test_simple_match(self):
        g = compile('hello|world')

        m = g.match('hello')
        self.assertTrue(isinstance(m, Match))

        m = g.match('world')
        self.assertTrue(isinstance(m, Match))

        m = g.match('somethingelse')
        self.assertEqual(m, None)

    def test_variable_varname(self):
        """
        Test `Variable` with varname.
        """
        g = compile('((?P<varname>hello|world)|test)')

        m = g.match('hello')
        variables = m.variables()
        self.assertTrue(isinstance(variables, Variables))
        self.assertEqual(variables.get('varname'), 'hello')
        self.assertEqual(variables['varname'], 'hello')

        m = g.match('world')
        variables = m.variables()
        self.assertTrue(isinstance(variables, Variables))
        self.assertEqual(variables.get('varname'), 'world')
        self.assertEqual(variables['varname'], 'world')

        m = g.match('test')
        variables = m.variables()
        self.assertTrue(isinstance(variables, Variables))
        self.assertEqual(variables.get('varname'), None)
        self.assertEqual(variables['varname'], None)

    def test_prefix(self):
        """
        Test `match_prefix`.
        """
        g = compile(r'(hello\ world|something\ else)')

        m = g.match_prefix('hello world')
        self.assertTrue(isinstance(m, Match))

        m = g.match_prefix('he')
        self.assertTrue(isinstance(m, Match))

        m = g.match_prefix('')
        self.assertTrue(isinstance(m, Match))

        m = g.match_prefix('som')
        self.assertTrue(isinstance(m, Match))

        m = g.match_prefix('hello wor')
        self.assertTrue(isinstance(m, Match))

        m = g.match_prefix('no-match')
        self.assertEqual(m.trailing_input().start, 0)
        self.assertEqual(m.trailing_input().stop, len('no-match'))

        m = g.match_prefix('hellotest')
        self.assertEqual(m.trailing_input().start, len('hello'))
        self.assertEqual(m.trailing_input().stop, len('hellotest'))

    def test_completer(self):
        class completer1(Completer):
            def get_completions(self, document, complete_event):
                yield Completion('before-%s-after' % document.text, -len(document.text))
                yield Completion('before-%s-after-B' % document.text, -len(document.text))

        class completer2(Completer):
            def get_completions(self, document, complete_event):
                yield Completion('before2-%s-after2' % document.text, -len(document.text))
                yield Completion('before2-%s-after2-B' % document.text, -len(document.text))

        # Create grammar.  "var1" + "whitespace" + "var2"
        g = compile(r'(?P<var1>[a-z]*) \s+ (?P<var2>[a-z]*)')

        # Test 'get_completions()'
        completer = GrammarCompleter(g, {'var1': completer1(), 'var2': completer2()})
        completions = list(completer.get_completions(
            Document('abc def', len('abc def')),
            CompleteEvent()))

        self.assertEqual(len(completions), 2)
        self.assertEqual(completions[0].text, 'before2-def-after2')
        self.assertEqual(completions[0].start_position, -3)
        self.assertEqual(completions[1].text, 'before2-def-after2-B')
        self.assertEqual(completions[1].start_position, -3)
