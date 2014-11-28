from __future__ import print_function
from prompt_toolkit.completion import Completer, Completion
import sqlparse

class PGCompleter(Completer):
    keywords = [
        'SELECT',
        'INSERT',
        'ALTER',
        'DROP',
        'DELETE',
        'FROM',
    ]

    table_names = []
    column_names = ['*']
    all_completions = set(keywords)

    def __init__(self, smart_completion=True):
        super(self.__class__, self).__init__()
        self.smart_completion = smart_completion

    @classmethod
    def extend_keywords(cls, additional_keywords):
        cls.keywords.extend(additional_keywords)
        cls.all_completions.update(additional_keywords)

    @classmethod
    def extend_table_names(cls, table_names):
        cls.table_names.extend(table_names)
        cls.all_completions.update(table_names)

    @classmethod
    def extend_column_names(cls, column_names):
        cls.column_names.extend(column_names)
        cls.all_completions.update(column_names)

    @staticmethod
    def find_matches(text, collection):
        for item in collection:
            if item.startswith(text) or item.startswith(text.upper()):
                yield Completion(item, -len(text))

    def get_completions(self, document):

        word_before_cursor = document.get_word_before_cursor()

        if not self.smart_completion:
            return self.find_matches(word_before_cursor, self.all_completions)

        # If we've partially typed a word then word_before_cursor won't be an
        # empty string. In that case we want to remove the partially typed
        # string before sending it to the sqlparser. Otherwise the last token
        # will always be the partially typed string which renders the smart
        # completion useless because it will always return the list of keywords
        # as completion.

        if word_before_cursor:
            parsed = sqlparse.parse(document.text[:-len(word_before_cursor)])
        else:
            parsed = sqlparse.parse(document.text)

        last_token = ''
        if parsed:
            last_token = parsed[0].token_prev(len(parsed[0].tokens)).value

        if last_token.lower() in ('select', 'where', 'having', 'set',
                'order by', 'group by'):
            return self.find_matches(word_before_cursor, self.column_names)
        elif last_token.lower() in ('from', 'update', 'insert into'):
            return self.find_matches(word_before_cursor, self.table_names)
        else:
            return self.find_matches(word_before_cursor, self.keywords)
