"""
Lexer interface and implementation.
Used for syntax highlighting.
"""
from __future__ import unicode_literals
from abc import ABCMeta, abstractmethod
from six import with_metaclass
from pygments.token import Token

__all__ = (
    'Lexer',
    'SimpleLexer',
    'PygmentsLexer',
)


class Lexer(with_metaclass(ABCMeta, object)):
    """
    Base class for all lexers.
    """
    @abstractmethod
    def get_tokens(self, cli, text):
        """
        Takes a `Document` and returns a list of tokens.
        """
        return [(Token, text)]


class SimpleLexer(Lexer):
    """
    Lexer that returns everything as just one token.
    """
    def __init__(self, default_token=Token):
        self.default_token = default_token

    def get_tokens(self, cli, text):
        return [(self.default_token, text)]


class PygmentsLexer(Lexer):
    """
    Lexer that calls a pygments lexer.
    """
    def __init__(self, pygments_lexer_cls):
        self.pygments_lexer_cls = pygments_lexer_cls

        # Instantiate the Pygments lexer.
        self.pygments_lexer = pygments_lexer_cls(
            stripnl=False,
            stripall=False,
            ensurenl=False)

    def get_tokens(self, cli, text):
        return self.pygments_lexer.get_tokens(text)
