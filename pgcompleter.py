from prompt_toolkit.completion import Completer, Completion

class PGCompleter(Completer):
    keywords = [
        'SELECT',
        'INSERT',
        'ALTER',
        'DROP',
        'DELETE',
        'FROM',
        'WHERE',
    ]

    @classmethod
    def extend_keywords(cls, additional_keywords):
        cls.keywords.extend(additional_keywords)

    def get_completions(self, document):
        word_before_cursor = document.get_word_before_cursor()

        for keyword in self.keywords:
            if (keyword.startswith(word_before_cursor) or
                    keyword.startswith(word_before_cursor.upper())):
                yield Completion(keyword, -len(word_before_cursor))
