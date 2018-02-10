"""
`GrammarLexer` is compatible with other lexers and can be used to highlight
the input using a regular grammar with annotations.
"""
from __future__ import unicode_literals
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text.utils import split_lines
from prompt_toolkit.lexers import Lexer

from .compiler import _CompiledGrammar
from six.moves import range
import six

__all__ = [
    'GrammarLexer',
]


class GrammarLexer(Lexer):
    """
    Lexer which can be used for highlighting of fragments according to variables in the grammar.

    (It does not actual lexing of the string, but it exposes an API, compatible
    with the Pygments lexer class.)

    :param compiled_grammar: Grammar as returned by the `compile()` function.
    :param lexers: Dictionary mapping variable names of the regular grammar to
                   the lexers that should be used for this part. (This can
                   call other lexers recursively.) If you wish a part of the
                   grammar to just get one fragment, use a
                   `prompt_toolkit.lexers.SimpleLexer`.
    """
    def __init__(self, compiled_grammar, default_style='', lexers=None):
        assert isinstance(compiled_grammar, _CompiledGrammar)
        assert isinstance(default_style, six.text_type)
        assert lexers is None or all(isinstance(v, Lexer) for k, v in lexers.items())
        assert lexers is None or isinstance(lexers, dict)

        self.compiled_grammar = compiled_grammar
        self.default_style = default_style
        self.lexers = lexers or {}

    def _get_text_fragments(self, text):
        m = self.compiled_grammar.match_prefix(text)

        if m:
            characters = [[self.default_style, c] for c in text]

            for v in m.variables():
                # If we have a `Lexer` instance for this part of the input.
                # Tokenize recursively and apply tokens.
                lexer = self.lexers.get(v.varname)

                if lexer:
                    document = Document(text[v.start:v.stop])
                    lexer_tokens_for_line = lexer.lex_document(document)
                    text_fragments = []
                    for i in range(len(document.lines)):
                        text_fragments.extend(lexer_tokens_for_line(i))
                        text_fragments.append(('', '\n'))
                    if text_fragments:
                        text_fragments.pop()

                    i = v.start
                    for t, s in text_fragments:
                        for c in s:
                            if characters[i][0] == self.default_style:
                                characters[i][0] = t
                            i += 1

            # Highlight trailing input.
            trailing_input = m.trailing_input()
            if trailing_input:
                for i in range(trailing_input.start, trailing_input.stop):
                    characters[i][0] = 'class:trailing-input'

            return characters
        else:
            return [('', text)]

    def lex_document(self, document):
        lines = list(split_lines(self._get_text_fragments(document.text)))

        def get_line(lineno):
            try:
                return lines[lineno]
            except IndexError:
                return []

        return get_line
