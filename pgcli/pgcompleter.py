from __future__ import print_function
import logging
from collections import defaultdict
from prompt_toolkit.completion import Completer, Completion
from .packages.sqlcompletion import suggest_type
from .packages.parseutils import last_word
from re import compile
from pandas import DataFrame

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
            'JOIN', 'LEFT', 'LEVEL', 'LIKE', 'LIMIT', 'LOCK', 'LONG',
            'MAXEXTENTS', 'MINUS', 'MLSLABEL', 'MODE', 'MODIFY', 'NOAUDIT',
            'NOCOMPRESS', 'NOT', 'NOWAIT', 'NULL', 'NUMBER', 'OF', 'OFFLINE',
            'ON', 'ONLINE', 'OPTION', 'OR', 'ORDER BY', 'OUTER', 'PCTFREE',
            'PRIMARY', 'PRIOR', 'PRIVILEGES', 'PUBLIC', 'RAW', 'RENAME',
            'RESOURCE', 'REVOKE', 'RIGHT', 'ROW', 'ROWID', 'ROWNUM', 'ROWS',
            'SELECT', 'SESSION', 'SET', 'SHARE', 'SIZE', 'SMALLINT', 'START',
            'SUCCESSFUL', 'SYNONYM', 'SYSDATE', 'TABLE', 'THEN', 'TO',
            'TRIGGER', 'UID', 'UNION', 'UNIQUE', 'UPDATE', 'USE', 'USER',
            'VALIDATE', 'VALUES', 'VARCHAR', 'VARCHAR2', 'VIEW', 'WHEN',
            'WHENEVER', 'WHERE', 'WITH', ]

    functions = ['AVG', 'COUNT', 'DISTINCT', 'FIRST', 'FORMAT', 'LAST',
            'LCASE', 'LEN', 'MAX', 'MIN', 'MID', 'NOW', 'ROUND', 'SUM', 'TOP',
            'UCASE']

    special_commands = []

    databases = []
    schemata = DataFrame({}, columns=['schema'])
    tables = DataFrame({}, columns=['schema', 'table', 'alias'])
    columns = DataFrame({}, columns=['schema', 'table', 'column'])

    all_completions = set(keywords + functions)

    def __init__(self, smart_completion=True):
        super(self.__class__, self).__init__()
        self.smart_completion = smart_completion
        self.reserved_words = set()
        for x in self.keywords:
            self.reserved_words.update(x.split())
        self.name_pattern = compile("^[_a-z][_a-z0-9\$]*$")

    def escape_name(self, name):
        if ((not self.name_pattern.match(name))
                or (name.upper() in self.reserved_words)
                or (name.upper() in self.functions)):
            name = '"%s"' % name

        return name

    def unescape_name(self, name):
        """ Unquote a string."""
        if name[0] == '"' and name[-1] == '"':
            name = name[1:-1]

        return name

    def escaped_names(self, names):
        return [self.escape_name(name) for name in names]

    def extend_special_commands(self, special_commands):
        # Special commands are not part of all_completions since they can only
        # be at the beginning of a line.
        self.special_commands.extend(special_commands)

    def extend_database_names(self, databases):
        databases = self.escaped_names(databases)
        self.databases.extend(databases)

    def extend_keywords(self, additional_keywords):
        self.keywords.extend(additional_keywords)
        self.all_completions.update(additional_keywords)

    def extend_schemata(self, data):

        # data is a DataFrame with columns [schema]
        self.schemata = self.schemata.append(data)
        self.all_completions.update(data['schema'])

    def extend_tables(self, data):

        # data is a DataFrame with columns [schema, table, is_visible]
        data[['schema', 'table']].apply(self.escaped_names)
        self.tables = self.tables.append(data)

        self.all_completions.update(data['schema'])
        self.all_completions.update(data['table'])

        # Auto-add '*' as a column in all tables
        cols = data[['schema', 'table']].copy()
        cols['column'] = '*'
        self.columns = self.columns.append(cols)

    def extend_columns(self, data):

        # data is a DataFrame with columns [schema, table, column]
        data[['schema', 'table', 'column']].apply(self.escaped_names)
        self.columns = self.columns.append(data)
        self.all_completions.update(data.column)

    def reset_completions(self):
        self.databases = []
        self.schemata = DataFrame({}, columns=['schema'])
        self.tables = DataFrame({}, columns=['schema', 'table', 'alias'])
        self.columns = DataFrame({}, columns=['schema', 'table', 'column'])
        self.all_completions = set(self.keywords)

    @staticmethod
    def find_matches(text, collection):
        text = last_word(text, include='most_punctuations')
        for item in collection:
            if item.startswith(text) or item.startswith(text.upper()):
                yield Completion(item, -len(text))

    def get_completions(self, document, complete_event, smart_completion=None):
        word_before_cursor = document.get_word_before_cursor(WORD=True)
        if smart_completion is None:
            smart_completion = self.smart_completion

        # If smart_completion is off then match any word that starts with
        # 'word_before_cursor'.
        if not smart_completion:
            return self.find_matches(word_before_cursor, self.all_completions)

        completions = []
        suggestions = suggest_type(document.text, document.text_before_cursor)

        for suggestion in suggestions:

            _logger.debug('Suggestion type: %r', suggestion['type'])

            if suggestion['type'] == 'column':
                tables = suggestion['tables']
                _logger.debug("Completion column scope: %r", tables)
                scoped_cols = self.populate_scoped_cols(tables)
                cols = self.find_matches(word_before_cursor, scoped_cols)
                completions.extend(cols)

            elif suggestion['type'] == 'function':
                funcs = self.find_matches(word_before_cursor, self.functions)
                completions.extend(funcs)

            elif suggestion['type'] == 'schema':
                schemata = self.find_matches(word_before_cursor, self.schemata)
                completions.extend(schemata)

            elif suggestion['type'] == 'table':
                meta = self.tables

                if suggestion['schema']:
                    tables = meta.table[meta.schema == suggestion['schema']]
                else:
                    tables = meta.table[meta.is_visible]

                tables = self.find_matches(word_before_cursor, tables)
                completions.extend(tables)
            elif suggestion['type'] == 'alias':
                aliases = suggestion['aliases']
                aliases = self.find_matches(word_before_cursor, aliases)
                completions.extend(aliases)
            elif suggestion['type'] == 'database':
                dbs = self.find_matches(word_before_cursor, self.databases)
                completions.extend(dbs)

            elif suggestion['type'] == 'keyword':
                keywords = self.keywords + self.special_commands
                keywords = self.find_matches(word_before_cursor, keywords)
                completions.extend(keywords)

        return completions

    def populate_scoped_cols(self, scoped_tbls):
        """ Find all columns in a set of scoped_tables
        :param scoped_tbls: DataFrame with columns [schema, table, alias]
        :return: list of column names
        """

        columns = self.columns  # dataframe with columns [schema, table, column]

        scoped_tbls[['schema', 'table', 'alias']].apply(self.unescape_name)

        # For fully qualified tables, inner join on (schema, table)
        qualed = scoped_tbls.merge(columns, how='inner', on=['schema', 'table'])

        # Only allow unqualified table reference on visible tables
        vis_tables = self.tables[self.tables['is_visible']]
        unqualed_tables = scoped_tbls.merge(vis_tables, how='inner', on=['table'])
        unqualed = unqualed_tables.merge(columns, how='inner', on=['table'])

        return list(qualed['column']) + list(unqualed['column'])


