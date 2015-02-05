from __future__ import print_function
import logging
from prompt_toolkit.completion import Completer, Completion
from .packages.sqlcompletion import suggest_type
from .packages.parseutils import last_word
from re import compile


_logger = logging.getLogger(__name__)

class PGCompleter(Completer):
    keywords = ['ACCESS', 'ADD', 'ALL', 'ALTER TABLE', 'AND', 'ANY', 'AS',
            'ASC', 'AUDIT', 'BETWEEN', 'BY', 'CASE', 'CHAR', 'CHECK',
            'CLUSTER', 'COLUMN', 'COMMENT', 'COMPRESS', 'CONNECT', 'COPY',
            'CREATE', 'CURRENT', 'DATE', 'DECIMAL', 'DEFAULT', 'DELETE FROM',
            'DESC', 'DESCRIBE', 'DISTINCT', 'DROP', 'ELSE', 'EXCLUSIVE',
            'EXISTS', 'FILE', 'FLOAT', 'FOR', 'FROM', 'FULL', 'GRANT',
            'GROUP BY', 'HAVING', 'IDENTIFIED', 'IMMEDIATE', 'IN', 'INCREMENT',
            'INDEX', 'INITIAL', 'INSERT INTO', 'INTEGER', 'INTERSECT', 'INTO',
            'IS', 'JOIN', 'LEFT', 'LEVEL', 'LIKE', 'LIMIT', 'LOCK', 'LONG',
            'MAXEXTENTS', 'MINUS', 'MLSLABEL', 'MODE', 'MODIFY', 'NOAUDIT',
            'NOCOMPRESS', 'NOT', 'NOWAIT', 'NULL', 'NUMBER', 'OF', 'OFFLINE',
            'ON', 'ONLINE', 'OPTION', 'OR', 'ORDER BY', 'OUTER', 'PCTFREE',
            'PRIMARY', 'PRIOR', 'PRIVILEGES', 'RAW', 'RENAME', 'RESOURCE',
            'REVOKE', 'RIGHT', 'ROW', 'ROWID', 'ROWNUM', 'ROWS', 'SELECT',
            'SESSION', 'SET', 'SHARE', 'SIZE', 'SMALLINT', 'START',
            'SUCCESSFUL', 'SYNONYM', 'SYSDATE', 'TABLE', 'THEN', 'TO',
            'TRIGGER', 'UID', 'UNION', 'UNIQUE', 'UPDATE', 'USE', 'USER',
            'VALIDATE', 'VALUES', 'VARCHAR', 'VARCHAR2', 'VIEW', 'WHEN',
            'WHENEVER', 'WHERE', 'WITH', ]

    functions = ['AVG', 'COUNT', 'DISTINCT', 'FIRST', 'FORMAT', 'LAST',
            'LCASE', 'LEN', 'MAX', 'MIN', 'MID', 'NOW', 'ROUND', 'SUM', 'TOP',
            'UCASE']

    def __init__(self, smart_completion=True):
        super(self.__class__, self).__init__()
        self.smart_completion = smart_completion
        self.reserved_words = set()
        for x in self.keywords:
            self.reserved_words.update(x.split())
        self.name_pattern = compile("^[_a-z][_a-z0-9\$]*$")

        self.special_commands = []
        self.databases = []
        self.dbmetadata = {}
        self.search_path = []

        self.all_completions = set(self.keywords + self.functions)

    def escape_name(self, name):
        if name and ((not self.name_pattern.match(name))
                or (name.upper() in self.reserved_words)
                or (name.upper() in self.functions)):
            name = '"%s"' % name

        return name

    def unescape_name(self, name):
        """ Unquote a string."""
        if name and name[0] == '"' and name[-1] == '"':
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

    def extend_schemata(self, schemata):

        # data is a DataFrame with columns [schema]
        schemata = self.escaped_names(schemata)
        for schema in schemata:
            self.dbmetadata[schema] = {}

        self.all_completions.update(schemata)

    def extend_tables(self, table_data):

        # table_data is a list of (schema_name, table_name) tuples
        table_data = [self.escaped_names(d) for d in table_data]

        # dbmetadata['schema_name']['table_name'] should be a list of column
        # names. Default to an asterisk
        for schema, table in table_data:
            self.dbmetadata[schema][table] = ['*']

        self.all_completions.update(t[1] for t in table_data)

    def extend_columns(self, column_data):

        # column_data is a list of (schema_name, table_name, column_name) tuples
        column_data = [self.escaped_names(d) for d in column_data]

        for schema, table, column in column_data:
            self.dbmetadata[schema][table].append(column)

        self.all_completions.update(t[2] for t in column_data)

    def set_search_path(self, search_path):
        self.search_path = self.escaped_names(search_path)

    def reset_completions(self):
        self.databases = []
        self.search_path = []
        self.dbmetadata = {}
        self.all_completions = set(self.keywords)

    @staticmethod
    def find_matches(text, collection):
        text = last_word(text, include='most_punctuations')
        for item in sorted(collection):
            if (item.startswith(text) or item.startswith(text.upper()) or
                    item.startswith(text.lower())):
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
                schema_names = self.dbmetadata.keys()
                schema_names = self.find_matches(word_before_cursor, schema_names)
                completions.extend(schema_names)

            elif suggestion['type'] == 'table':

                if suggestion['schema']:
                    try:
                        tables = self.dbmetadata[suggestion['schema']].keys()
                    except KeyError:
                        #schema doesn't exist
                        tables = []
                else:
                    schemas = self.search_path
                    meta = self.dbmetadata
                    tables = [tbl for schema in schemas
                                    for tbl in meta[schema].keys()]

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
        :param scoped_tbls: list of (schema, table, alias) tuples
        :return: list of column names
        """

        columns = []
        meta = self.dbmetadata

        for tbl in scoped_tbls:
            if tbl[0]:
                # A fully qualified schema.table reference
                schema = self.escape_name(tbl[0])
                table = self.escape_name(tbl[1])
                try:
                    # Get columns from the corresponding schema.table
                    columns.extend(meta[schema][table])
                except KeyError:
                    # Either the schema or table doesn't exist
                    pass
            else:
                for schema in self.search_path:
                    table = self.escape_name(tbl[1])
                    try:
                        columns.extend(meta[schema][table])
                        break
                    except KeyError:
                        pass

        return columns



