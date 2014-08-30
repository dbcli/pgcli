"""
Lexer for any shell input line.
"""
from pygments.lexer import RegexLexer
from pygments.token import Token

import re

__all__ = ('ParametersLexer', 'TextToken')

class ParametersLexer(RegexLexer):
    flags = re.DOTALL | re.MULTILINE | re.VERBOSE

    tokens =  {
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
                    (r'.', Token.Error), # Can not happen normally.
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
                    if get()  == '\\':
                        i += 1
                        if i < len(text):
                            unescaped_text.append(get())
                            i += 1
                        else:
                            inside_double_quotes = True
                            trailing_backslash = True
                            break
                    elif get()  == '"':
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


