from __future__ import unicode_literals

from six import string_types
from prompt_toolkit.completion import Completer, Completion

__all__ = (
    'WordCompleter',
)


class WordCompleter(Completer):
    """
    Simple autocompletion on a list of words.

    :param words: List of words.
    :param ignore_case: If True, case-insensitive completion.
    :param meta_dict: Optional dict mapping words to their meta-information.
    :param WORD: When True, use WORD characters.
    :param match_middle: When True, match not only the start, but also in the
                         middle of the word.
    """
    def __init__(self, words, ignore_case=False, meta_dict=None, WORD=False,
                 match_middle=False):
        self.words = list(words)
        self.ignore_case = ignore_case
        self.meta_dict = meta_dict or {}
        self.WORD = WORD
        self.match_middle = match_middle
        assert all(isinstance(w, string_types) for w in self.words)

    def get_completions(self, document, complete_event):
        word_before_cursor = document.get_word_before_cursor(WORD=self.WORD)

        if self.ignore_case:
            word_before_cursor = word_before_cursor.lower()

        def word_matches(word):
            """ True when the word before the cursor matches. """
            if self.match_middle:
                return word_before_cursor in word
            else:
                return word.startswith(word_before_cursor)

        for a in self.words:
            if word_matches(a.lower()):
                display_meta = self.meta_dict.get(a, '')
                yield Completion(a, -len(word_before_cursor), display_meta=display_meta)
