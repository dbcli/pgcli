from __future__ import print_function
from collections import defaultdict
from prompt_toolkit.completion import Completer, Completion
from .packages.sqlcompletion import suggest_type
from .packages.parseutils import last_word

class PGCompleter(Completer):
    keywords = ['ACCESS', 'ADD', 'ALL', 'ALTER TABLE', 'AND', 'ANY', 'AS',
            'ASC', 'AUDIT', 'BETWEEN', 'BY', 'CASE', 'CHAR', 'CHECK',
            'CLUSTER', 'COLUMN', 'COMMENT', 'COMPRESS', 'CONNECT', 'CREATE',
            'CURRENT', 'DATE', 'DECIMAL', 'DEFAULT', 'DELETE FROM', 'DESC',
            'DESCRIBE', 'DISTINCT', 'DROP', 'ELSE', 'EXCLUSIVE', 'EXISTS',
            'FILE', 'FLOAT', 'FOR', 'FROM', 'FULL', 'GRANT', 'GROUP BY',
            'HAVING', 'IDENTIFIED', 'IMMEDIATE', 'IN', 'INCREMENT', 'INDEX',
            'INITIAL', 'INSERT INTO', 'INTEGER', 'INTERSECT', 'INTO', 'IS',
            'LEFT', 'LEVEL', 'LIKE', 'LOCK', 'LONG', 'MAXEXTENTS', 'MINUS',
            'MLSLABEL', 'MODE', 'MODIFY', 'NOAUDIT', 'NOCOMPRESS', 'NOT',
            'NOWAIT', 'NULL', 'NUMBER', 'OF', 'OFFLINE', 'ON', 'ONLINE',
            'OPTION', 'OR', 'ORDER BY', 'OUTER', 'PCTFREE', 'PRIMARY', 'PRIOR',
            'PRIVILEGES', 'PUBLIC', 'RAW', 'RENAME', 'RESOURCE', 'REVOKE',
            'RIGHT', 'ROW', 'ROWID', 'ROWNUM', 'ROWS', 'SELECT', 'SESSION',
            'SET', 'SHARE', 'SIZE', 'SMALLINT', 'START', 'SUCCESSFUL',
            'SYNONYM', 'SYSDATE', 'TABLE', 'THEN', 'TO', 'TRIGGER', 'UID',
            'UNION', 'UNIQUE', 'UPDATE', 'USE', 'USER', 'VALIDATE', 'VALUES',
            'VARCHAR', 'VARCHAR2', 'VIEW', 'WHEN', 'WHENEVER', 'WHERE', 'WITH',
            ]

    functions = ['AVG', 'COUNT', 'DISTINCT', 'FIRST', 'FORMAT', 'LAST',
            'LCASE', 'LEN', 'MAX', 'MIN', 'MID', 'NOW', 'ROUND', 'SUM', 'TOP',
            'UCASE']

    special_commands = []

    databases = []
    tables = []
    # This will create a defaultdict which is initialized with a list that has
    # a '*' by default.
    columns = defaultdict(lambda: ['*'])
    all_completions = set(keywords)

    def __init__(self, smart_completion=True):
        super(self.__class__, self).__init__()
        self.smart_completion = smart_completion

    def extend_special_commands(self, special_commands):
        # Special commands are not part of all_completions since they can only
        # be at the beginning of a line.
        self.special_commands.extend(special_commands)

    def extend_database_names(self, databases):
        self.databases.extend(databases)

    def extend_keywords(self, additional_keywords):
        self.keywords.extend(additional_keywords)
        self.all_completions.update(additional_keywords)

    def extend_table_names(self, tables):
        self.tables.extend(tables)
        self.all_completions.update(tables)

    def extend_column_names(self, table, columns):
        self.columns[table].extend(columns)
        self.all_completions.update(columns)

    def reset_completions(self):
        self.tables = []
        self.columns = defaultdict(lambda: ['*'])
        self.all_completions = set(self.keywords)

    @staticmethod
    def find_matches(text, collection):
        text = last_word(text, include='most_punctuations')
        for item in collection:
            if item.startswith(text) or item.startswith(text.upper()):
                yield Completion(item, -len(text))

    def get_completions(self, document, complete_event):

        word_before_cursor = document.get_word_before_cursor(WORD=True)

        # If smart_completion is off then match any word that starts with
        # 'word_before_cursor'.
        if not self.smart_completion:
            return self.find_matches(word_before_cursor, self.all_completions)

        category, scope, match_all = suggest_type(document.text,
                document.text_before_cursor)

        word_to_match = '' if match_all else word_before_cursor

        if category == 'columns':
            scoped_cols = []
            for table in scope:
                scoped_cols.extend(self.columns[table])
            return self.find_matches(word_to_match, scoped_cols)
        elif category == 'columns-and-functions':
            scoped_cols = []
            for table in scope:
                scoped_cols.extend(self.columns[table])
            return self.find_matches(word_to_match, scoped_cols +
                    self.functions)
        elif category == 'tables':
            return self.find_matches(word_to_match, self.tables)
        elif category == 'databases':
            return self.find_matches(word_to_match, self.databases)
        elif category == 'keywords':
            return self.find_matches(word_to_match, self.keywords +
                    self.special_commands)
