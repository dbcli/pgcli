"""
The `Code` object is responsible for parsing a document, received from the `Line` class.
It's usually tokenized, using a Pygments lexer.
"""
from __future__ import unicode_literals
from pygments.token import Token

__all__ = (
    'Code',
    'CodeBase',
    'Completion'
    'ValidationError',
)


class Completion(object):
    def __init__(self, display='', suffix=''): # XXX: rename suffix to 'addition'
        self.display = display
        self.suffix = suffix

    def __repr__(self):
        return 'Completion(display=%r, suffix=%r)' % (self.display, self.suffix)


class ValidationError(Exception):
    def __init__(self, line, column, message=''):
        self.line = line
        self.column = column
        self.message = message



class CodeBase(object):
    """ Dummy base class for Code implementations.

    The methods in here are methods that are expected to exist for the `Line`
    and `Renderer` classes. """
    def __init__(self, document):
        self.document = document
        self.text = document.text
        self.cursor_position = document.cursor_position

    def get_tokens(self):
        return [(Token, self.text)]

    def complete(self):
        """ return one `Completion` instance or None. """
        # If there is one completion, return that.
        completions = list(self.get_completions())

        # Return the common prefix.
        return _commonprefix([ c.suffix for c in completions ])

    def get_completions(self):
        """ Yield `Completion` instances. """
        if False:
            yield

    def validate(self):
        """
        Validate the input.
        If invalid, this should raise `self.validation_error`.
        """
        pass



class Code(CodeBase):
    """
    Representation of a code document.
    (Immutable class -- caches tokens)

    :attr document: :class:`~prompt_toolkit.line.Document`
    """
    #: The pygments Lexer class to use.
    lexer_cls = None

    def __init__(self, document):
        super(Code, self).__init__(document)
        self._tokens = None

    @property
    def _lexer(self):
        """ Return lexer instance. """
        if self.lexer_cls:
            return self.lexer_cls(
                    stripnl=False,
                    stripall=False,
                    ensurenl=False)
        else:
            return None

    def get_tokens(self):
        """ Return the list of tokens for the input text. """
        # This implements caching. Usually, you override `_get_tokens`
        if self._tokens is None:
            self._tokens = self._get_tokens()
        return self._tokens

    def get_tokens_before_cursor(self):
        """ Return the list of tokens that appear before the cursor. If the
        cursor is in the middle of a token, that token will be split.  """
        count = 0
        result = []
        for c in self.get_tokens():
            if count + len(c[1]) < self.cursor_position:
                result.append(c)
                count += len(c[1])
            elif count < self.cursor_position:
                result.append((c[0], c[1][:self.cursor_position - count]))
                break
            else:
                break
        return result

    def _get_tokens(self):
        if self._lexer:
            return list(self._lexer.get_tokens(self.text))
        else:
            return [(Token, self.text)]


def _commonprefix(strings):
    # Similar to os.path.commonprefix
    if not strings:
        return ''

    else:
        s1 = min(strings)
        s2 = max(strings)

        for i, c in enumerate(s1):
            if c != s2[i]:
                return s1[:i]

        return s1
