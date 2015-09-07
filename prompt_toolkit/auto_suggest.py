"""
Fish-style [0] like auto-suggestion.

While a user types input in a certain buffer, suggestions are generated
(asynchronously.) Usually, they are displayed after the input. When the cursor
presses the right arrow and the cursor is at the end of the input, the
suggestion will be inserted.

[0] http://fishshell.com/
"""
from __future__ import unicode_literals
from abc import ABCMeta, abstractmethod
from six import with_metaclass

__all__ = (
    'Suggestion',
    'AutoSuggest',
    'AutoSuggestFromHistory',
)


class Suggestion(object):
    """
    Suggestion returned by an auto-suggest algorithm.
    """
    def __init__(self, text):
        self.text = text

    def __repr__(self):
        return 'Suggestion(%0)' % self.text


class AutoSuggest(with_metaclass(ABCMeta, object)):
    """
    Base class for auto suggestion implementations.
    """
    @abstractmethod
    def get_suggestion(self, buffer, document):
        """
        Return `None` or a `Suggestion` instance.
        """


class AutoSuggestFromHistory(AutoSuggest):
    """
    Give suggestions based on the lines in the history.
    """
    def get_suggestion(self, buffer, document):
        history = buffer.history
        text = document.text

        # Only create a suggestion when the buffer is not empty
        # and the buffer has only one line of input.
        if text and not '\n' in text:
            # Find first matching line in history.
            for string in reversed(list(history)):
                for line in reversed(string.splitlines()):
                    if line.startswith(text):
                        return Suggestion(line[len(text):])
