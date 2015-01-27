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
    """
    def __init__(self, words, ignore_case=False, meta_dict=None):
        self.words = list(words)
        self.ignore_case = ignore_case
        self.meta_dict = meta_dict or {}
        assert all(isinstance(w, string_types) for w in self.words)

        if ignore_case:
            self.words = [w.lower() for w in self.words]

    def get_completions(self, document, complete_event):
        word_before_cursor = document.get_word_before_cursor()

        if self.ignore_case:
            word_before_cursor = word_before_cursor.lower()

        for a in self.words:
            if a.startswith(word_before_cursor):
                display_meta = self.meta_dict.get(a, '')
                yield Completion(a, -len(word_before_cursor), display_meta=display_meta)
