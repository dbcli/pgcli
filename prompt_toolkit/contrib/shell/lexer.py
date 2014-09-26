"""
Lexer for any shell input line.
"""
# XXX: Don't import unicode_literals from __future__, this will break ParametersLexer

from pygments.lexer import RegexLexer
from pygments.token import Token

import re

__all__ = ('ParametersLexer', 'TextToken')


class ParametersLexer(RegexLexer):
    flags = re.DOTALL | re.MULTILINE | re.VERBOSE

    tokens = {
        'root': [
            (r'\s+', Token.WhiteSpace),
            (r'''
                    (
                        # Part of string inside a double quote.
                        "([^"\\]|\\.)*("|$)
                        |

                        # Part of string inside a single quote.
                        # (no escaping in single quotes.)
                        '[^']*('|$)
                        |

                        # Escaped character outside quotes
                        \\(.|$)
                        |

                        # Any not-quote character.
                        [^'"\ \\]+
                    )+
            ''', Token.Text),
            (r'.', Token.Error),  # Can not happen normally.
        ]
    }


class TextToken(object):
    """
    Takes a 'Text' token from the lexer and unescapes it.
    """
    def __init__(self, text):
        unescaped_text = []

        #: Indicate that the input text has a backslash at the end.
        trailing_backslash = False

        #: Indicates that we have unclosed double quotes
        inside_double_quotes = False

        #: Indicates that we have unclosed single quotes
        inside_single_quotes = False

        # Unescape it
        i = 0
        get = lambda: text[i]
        while i < len(text):
            # Inside double quotes.
            if get() == '"':
                i += 1

                while i < len(text):
                    if get() == '\\':
                        i += 1
                        if i < len(text):
                            unescaped_text.append(get())
                            i += 1
                        else:
                            inside_double_quotes = True
                            trailing_backslash = True
                            break
                    elif get() == '"':
                        i += 1
                        break
                    else:
                        unescaped_text.append(get())
                        i += 1
                else:
                    # (while-loop failed without a break.)
                    inside_double_quotes = True

            # Inside single quotes.
            elif get() == "'":
                i += 1

                while i < len(text):
                    if get() == "'":
                        i += 1
                        break
                    else:
                        unescaped_text.append(get())
                        i += 1
                else:
                    inside_single_quotes = True

            # Backslash outside quotes.
            elif text[i] == "\\":
                i += 1

                if i < len(text):
                    unescaped_text.append(get())
                    i += 1
                else:
                    trailing_backslash = True

            # Any other character.
            else:
                unescaped_text.append(get())
                i += 1

        self.unescaped_text = u''.join(unescaped_text)
        self.trailing_backslash = trailing_backslash
        self.inside_double_quotes = inside_double_quotes
        self.inside_single_quotes = inside_single_quotes

    def transform_appended_text(self, text):
        if self.inside_single_quotes:
            text = text.replace("'", r"\'")
            text += "'"

        if self.inside_double_quotes:
            text = text.replace('"', r'\"')
            text += '"'

        # TODO: handle trailing backslash
        return text


def lex_document(document, only_before_cursor=False):
    """
    Lex the document using the `ParametersLexer`.
    """
    lexer = ParametersLexer(stripnl=False, stripall=False, ensurenl=False)

    # Take Text tokens before cursor
    if only_before_cursor:
        tokens = list(lexer.get_tokens(document.text_before_cursor))
    else:
        tokens = list(lexer.get_tokens(document.text))
    parts = [t[1] for t in tokens if t[0] in Token.Text]

    # Separete the last token (where we are currently one)
    starting_new_token = not tokens or tokens[-1][0] in Token.WhiteSpace
    if starting_new_token:
        last_part = ''
    else:
        last_part = parts.pop()

    # Unescape tokens
    parts = [TextToken(t).unescaped_text for t in parts]
    last_part_token = TextToken(last_part)

    return parts, last_part_token
