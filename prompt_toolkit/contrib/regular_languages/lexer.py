"""
`GrammarLexer` is compatible with Pygments lexers and can be used to highlight
the input using a regular grammar with token annotations.
"""
from __future__ import unicode_literals
from pygments.token import Token

from .compiler import _CompiledGrammar

__all__ = (
    'GrammarLexer',
)


class GrammarLexer(object):
    """
    Lexer which can be used for highlighting of tokens according to variables in the grammar.

    (It does not actual lexing of the string, but it exposes an API, compatible
    with the Pygments lexer class.)

    :param compiled_grammar: Grammar as returned by the `compile()` function.
    :param tokens: (optionally) Dictionary mapping variable names of the
                   regular grammar to the Pygments Token that should be used
                   for this part.
    :param lexers: (optionally) Dictionary mapping variable names of the
                   regular grammar to the lexers that should be used for this part.
                   (This can call other lexer classes recursively.)
    """
    def __init__(self, compiled_grammar, tokens=None, default_token=None, lexers=None):
        assert isinstance(compiled_grammar, _CompiledGrammar)
        assert lexers is None or isinstance(lexers, dict)
        assert tokens is None or isinstance(tokens, dict)

        self.compiled_grammar = compiled_grammar
        self.tokens = tokens
        self.default_token = default_token or Token
        self.lexers = dict((name, lexer(stripnl=False, stripall=False, ensurenl=False))
                           for name, lexer in (lexers or {}).items())

    def __call__(self, stripnl=False, stripall=False, ensurenl=False):
        """
        For compatibility with Pygments lexers.
        (Signature of Pygments Lexer.__init__)
        """
        return self

    def get_tokens(self, text):
        m = self.compiled_grammar.match_prefix(text)

        if m:
            characters = [[self.default_token, c] for c in text]

            for v in m.variables():
                # If we have a Pygmenst lexer for this part of the input.
                # Tokenize recursively and apply tokens.
                lexer = self.lexers.get(v.varname)
                token = self.tokens.get(v.varname)

                if lexer:
                    lexer_tokens = lexer.get_tokens(text[v.start:v.stop])
                    i = v.start
                    for t, s in lexer_tokens:
                        for c in s:
                            if characters[i][0] == self.default_token:
                                characters[i][0] = t
                            i += 1

                elif token:
                    for i in range(v.start, v.stop):
                        if characters[i][0] == self.default_token:
                            characters[i][0] = token

            # Highlight trailing input.
            trailing_input = m.trailing_input()
            if trailing_input:
                for i in range(trailing_input.start, trailing_input.stop):
                    characters[i][0] = Token.TrailingInput

            return characters
        else:
            return [(Token, text)]
