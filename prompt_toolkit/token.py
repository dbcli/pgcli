"""
The Token class.

A `Token` has some semantics for a piece of text that is given a style through
a :class:`~prompt_toolkit.styles.Style` class. A pygments lexer for instance,
returns a list of (Token, text) tuples. Each fragment of text has a token
assigned, which when combined with a style sheet, will determine the fine
style.

This used to be interchangeable with ``pygments.token``, but our `Token` class
got some additional functionality.
"""

# If we don't need any lexers or style classes from Pygments, we don't want
# Pygments to be installed for only the following 10 lines of code. So, there
# is some duplication, but this should stay compatible with Pygments.

__all__ = (
    'Token',
    'ZeroWidthEscape',
)

_token_or_cache = {}

class _TokenType(tuple):
    def __getattr__(self, val):
        if not val or not val[0].isupper():
            return tuple.__getattribute__(self, val)

        new = _TokenType(self + (val,))
        setattr(self, val, new)
        return new

    def __repr__(self):
        return 'Token' + (self and '.' or '') + '.'.join(self)

    def __or__(self, other):
        """
        Concatenate two token types. (Compare it with an HTML element that has
        two classnames.) The styling of those two tokens will be combined.
        """
        # NOTE: Don't put an assertion on _TokenType here. We want to be
        #       compatible with Pygments tokens as well.

        try:
            return _token_or_cache[self, other]
        except KeyError:
            result = _TokenType(tuple(self) + (':', ) + tuple(other))
            _token_or_cache[self, other] = result
            return result


Token = _TokenType()


# Built-in tokens:

#: `ZeroWidthEscape` can be used for raw VT escape sequences that don't
#: cause the cursor position to move. (E.g. FinalTerm's escape sequences
#: for shell integration.)
ZeroWidthEscape = Token.ZeroWidthEscape
