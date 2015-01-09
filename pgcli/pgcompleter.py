from __future__ import print_function
import logging
from collections import defaultdict
from prompt_toolkit.completion import Completer, Completion
from .packages.sqlcompletion import suggest_type
from .packages.parseutils import last_word
from re import compile

_logger = logging.getLogger(__name__)

class PGCompleter(Completer):
    keywords = ['ACCESS', 'ADD', 'ALL', 'ALTER TABLE', 'AND', 'ANY', 'AS',
            'ASC', 'AUDIT', 'BETWEEN', 'BY', 'CASE', 'CHAR', 'CHECK',
            'CLUSTER', 'COLUMN', 'COMMENT', 'COMPRESS', 'CONNECT', 'CREATE',
            'CURRENT', 'DATE', 'DECIMAL', 'DEFAULT', 'DELETE FROM', 'DESC',
            'DESCRIBE', 'DISTINCT', 'DROP', 'ELSE', 'EXCLUSIVE', 'EXISTS',
            'FILE', 'FLOAT', 'FOR', 'FROM', 'FULL', 'GRANT', 'GROUP BY',
            'HAVING', 'IDENTIFIED', 'IMMEDIATE', 'IN', 'INCREMENT', 'INDEX',
            'INITIAL', 'INSERT INTO', 'INTEGER', 'INTERSECT', 'INTO', 'IS',
            'JOIN', 'LEFT', 'LEVEL', 'LIKE', 'LOCK', 'LONG', 'MAXEXTENTS',
            'MINUS', 'MLSLABEL', 'MODE', 'MODIFY', 'NOAUDIT', 'NOCOMPRESS',
            'NOT', 'NOWAIT', 'NULL', 'NUMBER', 'OF', 'OFFLINE', 'ON', 'ONLINE',
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
    all_completions = set(keywords + functions)

    def __init__(self, smart_completion=True):
        super(self.__class__, self).__init__()
        self.smart_completion = smart_completion

        self.name_pattern = compile("^[_a-z][_a-z0-9\$]*$")

    def extend_escape_name(self, name):
        if not self.name_pattern.match(name) or name in self.keywords or name in self.functions:
            name = '"%s"' % name

        return name

    def extend_unescape_name(self, name):
        if name[0] == '"' and name[-1] == '"':
            name = name[1:-1]

        return name

    def extend_escaped_names(self, names):
        return [self.extend_escape_name(name) for name in names]

    def extend_special_commands(self, special_commands):
        # Special commands are not part of all_completions since they can only
        # be at the beginning of a line.
        self.special_commands.extend(special_commands)

    def extend_database_names(self, databases):
        databases = self.extend_escaped_names(databases)

        self.databases.extend(databases)

    def extend_keywords(self, additional_keywords):
        self.keywords.extend(additional_keywords)
        self.all_completions.update(additional_keywords)

    def extend_table_names(self, tables):
        tables = self.extend_escaped_names(tables)

        self.tables.extend(tables)
        self.all_completions.update(tables)

    def extend_column_names(self, table, columns):
        columns = self.extend_escaped_names(columns)

        unescaped_table_name = self.extend_unescape_name(table)

        self.columns[unescaped_table_name].extend(columns)
        self.all_completions.update(columns)

    def reset_completions(self):
        self.databases = []
        self.tables = []
        self.columns = defaultdict(lambda: ['*'])
        self.all_completions = set(self.keywords)

    @staticmethod
    def find_matches(text, collection):
        text = last_word(text, include='most_punctuations')
        for item in collection:
            item_unescaped = item[1:] if item[0] == '"' else item

            if item_unescaped.startswith(text) or item_unescaped.startswith(text.upper()):
                yield Completion(item, -len(text))

    def get_completions(self, document, complete_event, smart_completion=None):
        word_before_cursor = document.get_word_before_cursor(WORD=True)
        if smart_completion is None:
            smart_completion = self.smart_completion

        # If smart_completion is off then match any word that starts with
        # 'word_before_cursor'.
        if not smart_completion:
            return self.find_matches(word_before_cursor, self.all_completions)

        category, scope = suggest_type(document.text,
                document.text_before_cursor)

        if category == 'columns':
            _logger.debug("Completion: 'columns' Scope: %r", scope)
            scoped_cols = self.populate_scoped_cols(scope)
            return self.find_matches(word_before_cursor, scoped_cols)
        elif category == 'columns-and-functions':
            _logger.debug("Completion: 'columns-and-functions' Scope: %r",
                    scope)
            scoped_cols = self.populate_scoped_cols(scope)
            return self.find_matches(word_before_cursor, scoped_cols +
                    self.functions)
        elif category == 'tables':
            _logger.debug("Completion: 'tables' Scope: %r", scope)
            return self.find_matches(word_before_cursor, self.tables)
        elif category == 'databases':
            _logger.debug("Completion: 'databases' Scope: %r", scope)
            return self.find_matches(word_before_cursor, self.databases)
        elif category == 'keywords':
            _logger.debug("Completion: 'keywords' Scope: %r", scope)
            return self.find_matches(word_before_cursor, self.keywords +
                    self.special_commands)

    def populate_scoped_cols(self, tables):
        scoped_cols = []
        for table in tables:
            unescaped_table_name = self.extend_unescape_name(table)
            scoped_cols.extend(self.columns[unescaped_table_name])
        return scoped_cols
