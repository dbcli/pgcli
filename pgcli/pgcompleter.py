from __future__ import print_function
from prompt_toolkit.completion import Completer, Completion
import sqlparse

class PGCompleter(Completer):
    keywords = ['ACCESS', 'ADD', 'ALL', 'ALTER TABLE', 'AND', 'ANY', 'AS',
            'ASC', 'AUDIT', 'BETWEEN', 'BY', 'CHAR', 'CHECK', 'CLUSTER',
            'COLUMN', 'COMMENT', 'COMPRESS', 'CONNECT', 'CREATE', 'CURRENT',
            'DATE', 'DECIMAL', 'DEFAULT', 'DELETE FROM', 'DESC', 'DESCRIBE',
            'DISTINCT', 'DROP', 'ELSE', 'EXCLUSIVE', 'EXISTS', 'FILE', 'FLOAT',
            'FOR', 'FROM', 'GRANT', 'GROUP', 'HAVING', 'IDENTIFIED',
            'IMMEDIATE', 'IN', 'INCREMENT', 'INDEX', 'INITIAL', 'INSERT INTO',
            'INTEGER', 'INTERSECT', 'INTO', 'IS', 'LEVEL', 'LIKE', 'LOCK',
            'LONG', 'MAXEXTENTS', 'MINUS', 'MLSLABEL', 'MODE', 'MODIFY',
            'NOAUDIT', 'NOCOMPRESS', 'NOT', 'NOWAIT', 'NULL', 'NUMBER', 'OF',
            'OFFLINE', 'ON', 'ONLINE', 'OPTION', 'OR', 'ORDER', 'PCTFREE',
            'PRIOR', 'PRIVILEGES', 'PUBLIC', 'RAW', 'RENAME', 'RESOURCE',
            'REVOKE', 'ROW', 'ROWID', 'ROWNUM', 'ROWS', 'SELECT', 'SESSION',
            'SET', 'SHARE', 'SIZE', 'SMALLINT', 'START', 'SUCCESSFUL',
            'SYNONYM', 'SYSDATE', 'TABLE', 'THEN', 'TO', 'TRIGGER', 'UID',
            'UNION', 'UNIQUE', 'UPDATE', 'USE', 'USER', 'VALIDATE', 'VALUES',
            'VARCHAR', 'VARCHAR2', 'VIEW', 'WHENEVER', 'WHERE', 'WITH', ]

    special_commands = []

    database_names = []
    table_names = []
    column_names = ['*']
    all_completions = set(keywords)

    def __init__(self, smart_completion=True):
        super(self.__class__, self).__init__()
        self.smart_completion = smart_completion

    def extend_special_commands(self, special_commands):
        # Special commands are not part of all_completions since they can only
        # be at the beginning of a line.
        self.special_commands.extend(special_commands)

    def extend_database_names(self, database_names):
        self.database_names.extend(database_names)

    def extend_keywords(self, additional_keywords):
        self.keywords.extend(additional_keywords)
        self.all_completions.update(additional_keywords)

    def extend_table_names(self, table_names):
        self.table_names.extend(table_names)
        self.all_completions.update(table_names)

    def extend_column_names(self, column_names):
        self.column_names.extend(column_names)
        self.all_completions.update(column_names)

    def reset_completions(self):
        self.table_names = []
        self.column_names = ['*']
        self.all_completions = set(self.keywords)

    @staticmethod
    def find_matches(text, collection):
        for item in collection:
            if item.startswith(text) or item.startswith(text.upper()):
                yield Completion(item, -len(text))

    def get_completions(self, document, complete_event):

        word_before_cursor = document.get_word_before_cursor(WORD=True)

        # If smart_completion is off then match any word that starts with
        # 'word_before_cursor'.
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
            last_token = parsed[0].token_prev(len(parsed[0].tokens))
            last_token = last_token.value if last_token else ''

        if last_token.lower() in ('select', 'where', 'having', 'set',
                'order by', 'group by'):
            return self.find_matches(word_before_cursor, self.column_names)
        elif last_token.lower() in ('from', 'update', 'into', 'describe'):
            return self.find_matches(word_before_cursor, self.table_names)
        elif last_token.lower() in ('d',):  # This for the \d special command.
            return self.find_matches(word_before_cursor, self.table_names)
        elif last_token.lower() in ('c', 'use'):  # This for the \c special command.
            return self.find_matches(word_before_cursor, self.database_names)
        else:
            return self.find_matches(word_before_cursor,
                    self.keywords + self.special_commands)
