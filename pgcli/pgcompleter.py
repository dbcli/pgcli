from __future__ import print_function
import logging
from prompt_toolkit.completion import Completer, Completion
from .packages.sqlcompletion import suggest_type
from .packages.parseutils import last_word
from re import compile

try:
    from collections import Counter
except ImportError:
    # python 2.6
    from .packages.counter import Counter

_logger = logging.getLogger(__name__)

class PGCompleter(Completer):
    keywords = ['ACCESS', 'ADD', 'ALL', 'ALTER TABLE', 'AND', 'ANY', 'AS',
            'ASC', 'AUDIT', 'BETWEEN', 'BY', 'CASE', 'CHAR', 'CHECK',
            'CLUSTER', 'COLUMN', 'COMMENT', 'COMPRESS', 'CONNECT', 'COPY',
            'CREATE', 'CURRENT', 'DATABASE', 'DATE', 'DECIMAL', 'DEFAULT',
            'DELETE FROM', 'DELIMITER', 'DESC', 'DESCRIBE', 'DISTINCT', 'DROP',
            'ELSE', 'ENCODING', 'ESCAPE', 'EXCLUSIVE', 'EXISTS', 'EXTENSION',
            'FILE', 'FLOAT', 'FOR', 'FORMAT', 'FORCE_QUOTE', 'FORCE_NOT_NULL',
            'FREEZE', 'FROM', 'FULL', 'FUNCTION', 'GRANT', 'GROUP BY',
            'HAVING', 'HEADER', 'IDENTIFIED', 'IMMEDIATE', 'IN', 'INCREMENT',
            'INDEX', 'INITIAL', 'INSERT INTO', 'INTEGER', 'INTERSECT', 'INTO',
            'IS', 'JOIN', 'LEFT', 'LEVEL', 'LIKE', 'LIMIT', 'LOCK', 'LONG',
            'MAXEXTENTS', 'MINUS', 'MLSLABEL', 'MODE', 'MODIFY', 'NOAUDIT',
            'NOCOMPRESS', 'NOT', 'NOWAIT', 'NULL', 'NUMBER', 'OIDS', 'OF',
            'OFFLINE', 'ON', 'ONLINE', 'OPTION', 'OR', 'ORDER BY', 'OUTER',
            'OWNER', 'PCTFREE', 'PRIMARY', 'PRIOR', 'PRIVILEGES', 'QUOTE',
            'RAW', 'RENAME', 'RESOURCE', 'REVOKE', 'RIGHT', 'ROW', 'ROWID',
            'ROWNUM', 'ROWS', 'SELECT', 'SESSION', 'SET', 'SHARE', 'SIZE',
            'SMALLINT', 'START', 'SUCCESSFUL', 'SYNONYM', 'SYSDATE', 'TABLE',
            'TEMPLATE', 'THEN', 'TO', 'TRIGGER', 'TRUNCATE', 'UID', 'UNION',
            'UNIQUE', 'UPDATE', 'USE', 'USER', 'USING', 'VALIDATE', 'VALUES',
            'VARCHAR', 'VARCHAR2', 'VIEW', 'WHEN', 'WHENEVER', 'WHERE', 'WITH']

    functions = ['AVG', 'COUNT', 'FIRST', 'FORMAT', 'LAST', 'LCASE', 'LEN',
                 'MAX', 'MIN', 'MID', 'NOW', 'ROUND', 'SUM', 'TOP', 'UCASE']

    def __init__(self, smart_completion=True):
        super(PGCompleter, self).__init__()
        self.smart_completion = smart_completion
        self.reserved_words = set()
        for x in self.keywords:
            self.reserved_words.update(x.split())
        self.name_pattern = compile("^[_a-z][_a-z0-9\$]*$")

        self.special_commands = []
        self.databases = []
        self.dbmetadata = {'tables': {}, 'views': {}, 'functions': {}}
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

        # schemata is a list of schema names
        schemata = self.escaped_names(schemata)
        metadata = self.dbmetadata['tables']
        for schema in schemata:
            metadata[schema] = {}

        # dbmetadata.values() are the 'tables' and 'functions' dicts
        for metadata in self.dbmetadata.values():
            for schema in schemata:
                metadata[schema] = {}

        self.all_completions.update(schemata)

    def extend_relations(self, data, kind):
        """ extend metadata for tables or views

        :param data: list of (schema_name, rel_name) tuples
        :param kind: either 'tables' or 'views'
        :return:
        """

        data = [self.escaped_names(d) for d in data]

        # dbmetadata['tables']['schema_name']['table_name'] should be a list of
        # column names. Default to an asterisk
        metadata = self.dbmetadata[kind]
        for schema, relname in data:
            try:
                metadata[schema][relname] = ['*']
            except AttributeError:
                _logger.error('%r %r listed in unrecognized schema %r',
                              kind, relname, schema)

        self.all_completions.update(t[1] for t in data)

    def extend_columns(self, column_data, kind):
        """ extend column metadata

        :param column_data: list of (schema_name, rel_name, column_name) tuples
        :param kind: either 'tables' or 'views'
        :return:
        """

        column_data = [self.escaped_names(d) for d in column_data]
        metadata = self.dbmetadata[kind]
        for schema, relname, column in column_data:
            metadata[schema][relname].append(column)

        self.all_completions.update(t[2] for t in column_data)

    def extend_functions(self, func_data):

        # func_data is an iterator of (schema_name, function_name)

        # dbmetadata['functions']['schema_name']['function_name'] should return
        # function metadata -- right now we're not storing any further metadata
        # so just default to None as a placeholder
        metadata = self.dbmetadata['functions']

        for f in func_data:
            schema, func = self.escaped_names(f)
            metadata[schema][func] = None
            self.all_completions.add(func)

    def set_search_path(self, search_path):
        self.search_path = self.escaped_names(search_path)

    def reset_completions(self):
        self.databases = []
        self.search_path = []
        self.dbmetadata = {'tables': {}, 'views': {}, 'functions': {}}
        self.all_completions = set(self.keywords + self.functions)

    @staticmethod
    def find_matches(text, collection, start_only=False):
        """Find completion matches for the given text.

        Given the user's input text and a collection of available
        completions, find completions matching the last word of the
        text.

        If `start_only` is True, the text will match an available
        completion only at the beginning. Otherwise, a completion is
        considered a match if the text appears anywhere within it.

        yields prompt_toolkit Completion instances for any matches found
        in the collection of available completions.

        """

        text = last_word(text, include='most_punctuations').lower()

        for item in sorted(collection):
            match_end_limit = len(text) if start_only else None
            match_point = item.lower().find(text, 0, match_end_limit)

            if match_point >= 0:
                yield Completion(item, -len(text))

    def get_completions(self, document, complete_event, smart_completion=None):
        word_before_cursor = document.get_word_before_cursor(WORD=True)
        if smart_completion is None:
            smart_completion = self.smart_completion

        # If smart_completion is off then match any word that starts with
        # 'word_before_cursor'.
        if not smart_completion:
            return self.find_matches(word_before_cursor, self.all_completions,
                                     start_only=True)

        completions = []
        suggestions = suggest_type(document.text, document.text_before_cursor)

        for suggestion in suggestions:

            _logger.debug('Suggestion type: %r', suggestion['type'])

            if suggestion['type'] == 'column':
                tables = suggestion['tables']
                _logger.debug("Completion column scope: %r", tables)
                scoped_cols = self.populate_scoped_cols(tables)

                if suggestion.get('drop_unique'):
                    # drop_unique is used for 'tb11 JOIN tbl2 USING (...'
                    # which should suggest only columns that appear in more than
                    # one table
                    scoped_cols = [col for (col, count)
                                         in Counter(scoped_cols).items()
                                           if count > 1 and col != '*']

                cols = self.find_matches(word_before_cursor, scoped_cols)
                completions.extend(cols)

            elif suggestion['type'] == 'function':
                # suggest user-defined functions using substring matching
                funcs = self.populate_schema_objects(
                    suggestion['schema'], 'functions')
                user_funcs = self.find_matches(word_before_cursor, funcs)
                completions.extend(user_funcs)

                if not suggestion['schema']:
                    # also suggest hardcoded functions using startswith
                    # matching
                    predefined_funcs = self.find_matches(word_before_cursor,
                                                         self.functions,
                                                         start_only=True)
                    completions.extend(predefined_funcs)

            elif suggestion['type'] == 'schema':
                schema_names = self.dbmetadata['tables'].keys()

                # Unless we're sure the user really wants them, hide schema
                # names starting with pg_, which are mostly temporary schemas
                if not word_before_cursor.startswith('pg_'):
                    schema_names = [s for s in schema_names
                                      if not s.startswith('pg_')]

                schema_names = self.find_matches(word_before_cursor, schema_names)
                completions.extend(schema_names)

            elif suggestion['type'] == 'table':
                tables = self.populate_schema_objects(
                    suggestion['schema'], 'tables')

                # Unless we're sure the user really wants them, don't suggest
                # the pg_catalog tables that are implicitly on the search path
                if not suggestion['schema'] and (
                        not word_before_cursor.startswith('pg_')):
                    tables = [t for t in tables if not t.startswith('pg_')]

                tables = self.find_matches(word_before_cursor, tables)
                completions.extend(tables)

            elif suggestion['type'] == 'view':
                views = self.populate_schema_objects(
                    suggestion['schema'], 'views')

                if not suggestion['schema'] and (
                        not word_before_cursor.startswith('pg_')):
                    views = [v for v in views if not v.startswith('pg_')]

                views = self.find_matches(word_before_cursor, views)
                completions.extend(views)

            elif suggestion['type'] == 'alias':
                aliases = suggestion['aliases']
                aliases = self.find_matches(word_before_cursor, aliases)
                completions.extend(aliases)

            elif suggestion['type'] == 'database':
                dbs = self.find_matches(word_before_cursor, self.databases)
                completions.extend(dbs)

            elif suggestion['type'] == 'keyword':
                keywords = self.find_matches(word_before_cursor, self.keywords,
                                             start_only=True)
                completions.extend(keywords)

            elif suggestion['type'] == 'special':
                special = self.find_matches(word_before_cursor,
                                            self.special_commands,
                                            start_only=True)
                completions.extend(special)

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
                # A fully qualified schema.relname reference
                schema = self.escape_name(tbl[0])
                relname = self.escape_name(tbl[1])

                # We don't know if schema.relname is a table or view. Since
                # tables and views cannot share the same name, we can check one
                # at a time
                try:
                    columns.extend(meta['tables'][schema][relname])

                    # Table exists, so don't bother checking for a view
                    continue
                except KeyError:
                    pass

                try:
                    columns.extend(meta['views'][schema][relname])
                except KeyError:
                    pass

            else:
                # Schema not specified, so traverse the search path looking for
                # a table or view that matches. Note that in order to get proper
                # shadowing behavior, we need to check both views and tables for
                # each schema before checking the next schema
                for schema in self.search_path:
                    relname = self.escape_name(tbl[1])

                    try:
                        columns.extend(meta['tables'][schema][relname])
                        break
                    except KeyError:
                        pass

                    try:
                        columns.extend(meta['views'][schema][relname])
                        break
                    except KeyError:
                        pass

        return columns

    def populate_schema_objects(self, schema, obj_type):
        """Returns list of tables or functions for a (optional) schema"""

        metadata = self.dbmetadata[obj_type]

        if schema:
            try:
                objects = metadata[schema].keys()
            except KeyError:
                #schema doesn't exist
                objects = []
        else:
            schemas = self.search_path
            objects = [obj for schema in schemas
                           for obj in metadata[schema].keys()]

        return objects



