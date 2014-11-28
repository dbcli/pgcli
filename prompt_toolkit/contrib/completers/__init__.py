from __future__ import unicode_literals

from six import string_types
from prompt_toolkit.completion import Completer, Completion

import os



class WordCompleter(Completer):
    def __init__(self, words):
        self.words = list(words)
        assert all(isinstance(w, string_types) for w in self.words)

    def get_completions(self, document):
        word_before_cursor = document.get_word_before_cursor()

        for a in self.words:
            if a.startswith(word_before_cursor):
                yield Completion(a, -len(word_before_cursor))


class PathCompleter(Completer):
    """
    Complete for Path variables.
    """
    def __init__(self, include_files=True):
        self.include_files = include_files

    def get_completions(self, document):
        text = document.text_before_cursor
        try:
            directory = os.path.dirname(text) or '.'
            prefix = os.path.basename(text)

            for filename in os.listdir(directory):
                if filename.startswith(prefix):
                    completion = filename[len(prefix):]

                    if os.path.isdir(os.path.join(directory, filename)):
                        completion += '/'
                    else:
                        if not self.include_files:
                            continue

                    yield Completion(completion, 0, display=filename)
        except OSError:
            pass
