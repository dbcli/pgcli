from __future__ import print_function
from prompt_toolkit.completion import Completer, Completion
import sqlparser

class PGCompleter(Completer):
    keywords = [
        'SELECT',
        'INSERT',
        'ALTER',
        'DROP',
        'DELETE',
    ]

    table_names = []
    column_names = []

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
        segment = sqlparser.whichSegment(document.text)

        if segment in ('select', 'where', 'having', 'set', 'order by', 'group by'):
            return find_matches(word_before_cursor, self.column_names)
        elif segment in ('from', 'update', 'insert into'):
            return find_matches(word_before_cursor, self.table_names)
        elif segment == 'beginning':
            return find_matches(word_before_cursor, self.keywords)
        else:
            return find_matches(word_before_cursor, sqlparser.reserved)
