"""
Lexer interface and implementations.
Used for syntax highlighting.
"""
from __future__ import unicode_literals
from .base import Lexer, SimpleLexer, DynamicLexer
from .pygments import PygmentsLexer, SyntaxSync, SyncFromStart, RegexSync

__all__ = [
    # Base.
    'Lexer',
    'SimpleLexer',
    'DynamicLexer',

    # Pygments.
    'PygmentsLexer',
    'RegexSync',
    'SyncFromStart',
    'SyntaxSync',
]
