from __future__ import unicode_literals

from pygments.token import Token
from .utils import TokenList

__all__ = (
    'PasswordProcessor',
    'BracketsMismatchProcessor',
)


class PasswordProcessor(object):
    """
    Processor that turns masks the input. (For passwords.)
    """
    def __init__(self, char='*'):
        self.char = char

    def process_tokens(self, tokens):
        return [(token, self.char * len(text)) for token, text in tokens]


class BracketsMismatchProcessor(object):
    """
    Processor that replaces the token type of bracket mismatches by an Error.
    """
    error_token = Token.Error

    def process_tokens(self, tokens):
        tokens = list(TokenList(tokens))

        stack = []  # Pointers to the result array

        for index, (token, text) in enumerate(tokens):
            top = tokens[stack[-1]][1] if stack else ''

            if text in '({[]})':
                if text in '({[':
                    # Put open bracket on the stack
                    stack.append(index)

                elif (text == ')' and top == '(' or
                      text == '}' and top == '{' or
                      text == ']' and top == '['):
                    # Match found
                    stack.pop()
                else:
                    # No match for closing bracket.
                    tokens[index] = (self.error_token, text)

        # Highlight unclosed tags that are still on the stack.
        for index in stack:
            tokens[index] = (Token.Error, tokens[index][1])

        return tokens
