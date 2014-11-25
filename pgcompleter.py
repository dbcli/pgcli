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

    @classmethod
    def extend_keywords(cls, additional_keywords):
        cls.keywords.extend(additional_keywords)

    @classmethod
    def extend_table_names(cls, table_names):
        cls.table_names.extend(table_names)

    @classmethod
    def extend_column_names(cls, column_names):
        cls.column_names.extend(column_names)

    def get_completions(self, document):

        def find_matches(text, collection):
            for item in collection:
                if item.startswith(text) or item.startswith(text.upper()):
                    yield Completion(item, -len(text))

        word_before_cursor = document.get_word_before_cursor()

        parsed = sqlparse.parse(document.text[:-len(word_before_cursor)])

        last_token = ''
        if parsed:
            last_token = parsed[0].token_prev(len(parsed[0].tokens)).value

        #print(last_token)

        if last_token.lower() in ('select', 'where', 'having', 'set', 'order by', 'group by'):
            return find_matches(word_before_cursor, self.column_names)
        elif last_token.lower() in ('from', 'update', 'insert into'):
            return find_matches(word_before_cursor, self.table_names)
        else:
            return find_matches(word_before_cursor, self.keywords)
