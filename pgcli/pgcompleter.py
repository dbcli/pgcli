from __future__ import print_function, unicode_literals
import logging
import re
import itertools
import operator
from collections import namedtuple, defaultdict
from pgspecial.namedqueries import NamedQueries
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.contrib.completers import PathCompleter
from prompt_toolkit.document import Document
from .packages.sqlcompletion import (
    suggest_type, Special, Database, Schema, Table, Function, Column, View,
    Keyword, NamedQuery, Datatype, Alias, Path, JoinCondition, Join)
from .packages.function_metadata import ColumnMetadata, ForeignKey
from .packages.parseutils import last_word, TableReference
from .packages.pgliterals.main import get_literals
from .packages.prioritization import PrevalenceCounter
from .config import load_config, config_location, get_config

try:
    from collections import OrderedDict
except ImportError:
    from .packages.ordereddict import OrderedDict

_logger = logging.getLogger(__name__)

NamedQueries.instance = NamedQueries.from_config(
    load_config(config_location() + 'config'))


Match = namedtuple('Match', ['completion', 'priority'])

normalize_ref = lambda ref: ref if ref[0] == '"' else '"' + ref.lower() +  '"'

class PGCompleter(Completer):
    keywords = get_literals('keywords')
    functions = get_literals('functions')
    datatypes = get_literals('datatypes')

    def __init__(self, smart_completion=True, pgspecial=None, settings=None):
        super(PGCompleter, self).__init__()
        self.smart_completion = smart_completion
        self.pgspecial = pgspecial
        self.prioritizer = PrevalenceCounter()
        settings = settings or {}
        self.casing_file = settings.get('casing_file')
        self.generate_casing_file = settings.get('generate_casing_file')
        self.asterisk_column_order = settings.get(
            'asterisk_column_order', 'table_order')

        self.reserved_words = set()
        for x in self.keywords:
            self.reserved_words.update(x.split())
        self.name_pattern = re.compile("^[_a-z][_a-z0-9\$]*$")

        self.databases = []
        self.dbmetadata = {'tables': {}, 'views': {}, 'functions': {},
                           'datatypes': {}}
        self.search_path = []
        self.casing = {}

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

    def extend_casing(self, words):
        """ extend casing data

        :return:
        """
        # casing should be a dict {lowercasename:PreferredCasingName}
        self.casing = dict((word.lower(), word) for word in words)

    def extend_relations(self, data, kind):
        """ extend metadata for tables or views

        :param data: list of (schema_name, rel_name) tuples
        :param kind: either 'tables' or 'views'
        :return:
        """

        data = [self.escaped_names(d) for d in data]

        # dbmetadata['tables']['schema_name']['table_name'] should be an
        # OrderedDict {column_name:ColumnMetaData}.
        metadata = self.dbmetadata[kind]
        for schema, relname in data:
            try:
                metadata[schema][relname] = OrderedDict()
            except KeyError:
                _logger.error('%r %r listed in unrecognized schema %r',
                              kind, relname, schema)
            self.all_completions.add(relname)

    def extend_columns(self, column_data, kind):
        """ extend column metadata

        :param column_data: list of (schema_name, rel_name, column_name, column_type) tuples
        :param kind: either 'tables' or 'views'
        :return:
        """
        metadata = self.dbmetadata[kind]
        for schema, relname, colname, datatype in column_data:
            (schema, relname, colname) = self.escaped_names(
                [schema, relname, colname])
            column = ColumnMetadata(name=colname, datatype=datatype,
                foreignkeys=[])
            metadata[schema][relname][colname] = column
            self.all_completions.add(colname)

    def extend_functions(self, func_data):

        # func_data is a list of function metadata namedtuples
        # with fields schema_name, func_name, arg_list, result,
        # is_aggregate, is_window, is_set_returning

        # dbmetadata['schema_name']['functions']['function_name'] should return
        # the function metadata namedtuple for the corresponding function
        metadata = self.dbmetadata['functions']

        for f in func_data:
            schema, func = self.escaped_names([f.schema_name, f.func_name])

            if func in metadata[schema]:
                metadata[schema][func].append(f)
            else:
                metadata[schema][func] = [f]

            self.all_completions.add(func)

    def extend_foreignkeys(self, fk_data):

        # fk_data is a list of ForeignKey namedtuples, with fields
        # parentschema, childschema, parenttable, childtable,
        # parentcolumns, childcolumns

        # These are added as a list of ForeignKey namedtuples to the
        # ColumnMetadata namedtuple for both the child and parent
        meta = self.dbmetadata['tables']

        for fk in fk_data:
            e = self.escaped_names
            parentschema, childschema = e([fk.parentschema, fk.childschema])
            parenttable, childtable = e([fk.parenttable, fk.childtable])
            childcol, parcol = e([fk.childcolumn, fk.parentcolumn])
            childcolmeta =  meta[childschema][childtable][childcol]
            parcolmeta =  meta[parentschema][parenttable][parcol]
            fk = ForeignKey(parentschema, parenttable, parcol,
                childschema, childtable, childcol)
            childcolmeta.foreignkeys.append((fk))
            parcolmeta.foreignkeys.append((fk))

    def extend_datatypes(self, type_data):

        # dbmetadata['datatypes'][schema_name][type_name] should store type
        # metadata, such as composite type field names. Currently, we're not
        # storing any metadata beyond typename, so just store None
        meta = self.dbmetadata['datatypes']

        for t in type_data:
            schema, type_name = self.escaped_names(t)
            meta[schema][type_name] = None
            self.all_completions.add(type_name)

    def extend_query_history(self, text, is_init=False):
        if is_init:
            # During completer initialization, only load keyword preferences,
            # not names
            self.prioritizer.update_keywords(text)
        else:
            self.prioritizer.update(text)

    def set_search_path(self, search_path):
        self.search_path = self.escaped_names(search_path)

    def reset_completions(self):
        self.databases = []
        self.special_commands = []
        self.search_path = []
        self.dbmetadata = {'tables': {}, 'views': {}, 'functions': {},
                           'datatypes': {}}
        self.all_completions = set(self.keywords + self.functions)

    def find_matches(self, text, collection, mode='fuzzy',
                     meta=None, meta_collection=None,
                     type_priority=0, priority_collection = None):
        """Find completion matches for the given text.

        Given the user's input text and a collection of available
        completions, find completions matching the last word of the
        text.

        `mode` can be either 'fuzzy', or 'strict'
            'fuzzy': fuzzy matching, ties broken by name prevalance
            `keyword`: start only matching, ties broken by keyword prevalance

        yields prompt_toolkit Completion instances for any matches found
        in the collection of available completions.

        """

        text = last_word(text, include='most_punctuations').lower()
        text_len = len(text)

        if text and text[0] == '"':
            # text starts with double quote; user is manually escaping a name
            # Match on everything that follows the double-quote. Note that
            # text_len is calculated before removing the quote, so the
            # Completion.position value is correct
            text = text[1:]

        if mode == 'fuzzy':
            fuzzy = True
            priority_func = self.prioritizer.name_count
        else:
            fuzzy = False
            priority_func = self.prioritizer.keyword_count

        # Construct a `_match` function for either fuzzy or non-fuzzy matching
        # The match function returns a 2-tuple used for sorting the matches,
        # or None if the item doesn't match
        # Note: higher priority values mean more important, so use negative
        # signs to flip the direction of the tuple
        if fuzzy:
            regex = '.*?'.join(map(re.escape, text))
            pat = re.compile('(%s)' % regex)

            def _match(item):
                r = pat.search(self.unescape_name(item.lower()))
                if r:
                    return -len(r.group()), -r.start()
        else:
            match_end_limit = len(text)

            def _match(item):
                match_point = item.lower().find(text, 0, match_end_limit)
                if match_point >= 0:
                    # Use negative infinity to force keywords to sort after all
                    # fuzzy matches
                    return -float('Infinity'), -match_point

        # Fallback to meta param if meta_collection param is None
        meta_collection = meta_collection or itertools.repeat(meta)
        # Fallback to 0 if priority_collection param is None
        priority_collection = priority_collection or itertools.repeat(0)

        collection = zip(collection, meta_collection, priority_collection)

        matches = []

        for item, meta, prio in collection:
            sort_key = _match(item)
            if sort_key:
                if meta and len(meta) > 50:
                    # Truncate meta-text to 50 characters, if necessary
                    meta = meta[:47] + u'...'

                # Lexical order of items in the collection, used for
                # tiebreaking items with the same match group length and start
                # position. Since we use *higher* priority to mean "more
                # important," we use -ord(c) to prioritize "aa" > "ab" and end
                # with 1 to prioritize shorter strings (ie "user" > "users").
                # We also use the unescape_name to make sure quoted names have
                # the same priority as unquoted names.
                lexical_priority = tuple(-ord(c) for c in self.unescape_name(item)) + (1,)

                item = self.case(item)
                priority = type_priority, prio, sort_key, priority_func(item), lexical_priority

                matches.append(Match(
                    completion=Completion(item, -text_len, display_meta=meta),
                    priority=priority))
        return matches

    def case(self, word):
        return self.casing.get(word, word)

    def get_completions(self, document, complete_event, smart_completion=None):
        word_before_cursor = document.get_word_before_cursor(WORD=True)

        if smart_completion is None:
            smart_completion = self.smart_completion

        # If smart_completion is off then match any word that starts with
        # 'word_before_cursor'.
        if not smart_completion:
            matches = self.find_matches(word_before_cursor, self.all_completions,
                                        mode='strict')
            completions = [m.completion for m in matches]
            return sorted(completions, key=operator.attrgetter('text'))

        matches = []
        suggestions = suggest_type(document.text, document.text_before_cursor)

        for suggestion in suggestions:
            suggestion_type = type(suggestion)
            _logger.debug('Suggestion type: %r', suggestion_type)

            # Map suggestion type to method
            # e.g. 'table' -> self.get_table_matches
            matcher = self.suggestion_matchers[suggestion_type]
            matches.extend(matcher(self, suggestion, word_before_cursor))

        # Sort matches so highest priorities are first
        matches = sorted(matches, key=operator.attrgetter('priority'),
                         reverse=True)

        return [m.completion for m in matches]

    def get_column_matches(self, suggestion, word_before_cursor):
        tables = suggestion.tables
        _logger.debug("Completion column scope: %r", tables)
        scoped_cols = self.populate_scoped_cols(tables)
        colit = scoped_cols.items
        flat_cols = list(itertools.chain(*((c.name for c in cols)
            for t, cols in colit())))
        if suggestion.require_last_table:
            # require_last_table is used for 'tb11 JOIN tbl2 USING (...' which should
            # suggest only columns that appear in the last table and one more
            ltbl = tables[-1].ref
            flat_cols = list(
              set(c.name for t, cs in colit() if t.ref == ltbl for c in cs) &
              set(c.name for t, cs in colit() if t.ref != ltbl for c in cs))
        lastword = last_word(word_before_cursor, include='most_punctuations')
        if lastword == '*':
            if self.asterisk_column_order == 'alphabetic':
                flat_cols.sort()
                for cols in scoped_cols.values():
                    cols.sort(key=operator.attrgetter('name'))
            if (lastword != word_before_cursor and len(tables) == 1
              and word_before_cursor[-len(lastword) - 1] == '.'):
                # User typed x.*; replicate "x." for all columns except the
                # first, which gets the original (as we only replace the "*"")
                sep = ', ' + word_before_cursor[:-1]
                collist = sep.join(self.case(c) for c in flat_cols)
            elif len(scoped_cols) > 1:
                # Multiple tables; qualify all columns
                collist = ', '.join(t.ref + '.' + self.case(c.name)
                    for t, cs in colit() for c in cs)
            else:
                # Plain columns
                collist = ', '.join(self.case(c) for c in flat_cols)

            return [Match(completion=Completion(collist, -1,
                display_meta='columns', display='*'), priority=(1,1,1))]

        return self.find_matches(word_before_cursor, flat_cols, meta='column')

    def generate_alias(self, tbl, tbls):
        """ Generate a unique table alias
        tbl - name of the table to alias, quoted if it needs to be
        tbls - set of table refs already in use, normalized with normalize_ref
        """
        if tbl[0] == '"':
            aliases = ('"' + tbl[1:-1] + str(i) + '"' for i in itertools.count(2))
        else:
            aliases = (self.case(tbl) + str(i) for i in itertools.count(2))
        return next(a for a in aliases if normalize_ref(a) not in tbls)

    def get_join_matches(self, suggestion, word_before_cursor):
        tbls = suggestion.tables
        cols = self.populate_scoped_cols(tbls)
        # Set up some data structures for efficient access
        qualified = dict((normalize_ref(t.ref), t.schema) for t in tbls)
        ref_prio = dict((normalize_ref(t.ref), n) for n, t in enumerate(tbls))
        refs = set(normalize_ref(t.ref) for t in tbls)
        other_tbls = set((t.schema, t.name)
            for t in list(cols)[:-1])
        joins, prios = [], []
        # Iterate over FKs in existing tables to find potential joins
        fks = ((fk, rtbl, rcol) for rtbl, rcols in cols.items()
            for rcol in rcols for fk in rcol.foreignkeys)
        col = namedtuple('col', 'schema tbl col')
        for fk, rtbl, rcol in fks:
            right = col(rtbl.schema, rtbl.name, rcol.name)
            child = col(fk.childschema, fk.childtable, fk.childcolumn)
            parent = col(fk.parentschema, fk.parenttable, fk.parentcolumn)
            left = child if parent == right else parent
            if suggestion.schema and left.schema != suggestion.schema:
                continue
            c = self.case
            if normalize_ref(left.tbl) in refs:
                lref = self.generate_alias(left.tbl, refs)
                join = '{0} {4} ON {4}.{1} = {2}.{3}'.format(
                    c(left.tbl), c(left.col), rtbl.ref, c(right.col), lref)
            else:
                join = '{0} ON {0}.{1} = {2}.{3}'.format(
                    c(left.tbl), c(left.col), rtbl.ref, c(right.col))
            # Schema-qualify if (1) new table in same schema as old, and old
            # is schema-qualified, or (2) new in other schema, except public
            if not suggestion.schema and (qualified[normalize_ref(rtbl.ref)]
                and left.schema == right.schema
                or left.schema not in(right.schema, 'public')):
                join = left.schema + '.' + join
            joins.append(join)
            prios.append(ref_prio[normalize_ref(rtbl.ref)] * 2 + (
                0 if (left.schema, left.tbl) in other_tbls else 1))

        return self.find_matches(word_before_cursor, joins, meta='join',
            priority_collection=prios, type_priority=100)

    def get_join_condition_matches(self, suggestion, word_before_cursor):
        col = namedtuple('col', 'schema tbl col')
        tbls = self.populate_scoped_cols(suggestion.tables).items
        cols = [(t, c) for t, cs in tbls() for c in cs]
        try:
            lref = (suggestion.parent or suggestion.tables[-1]).ref
            ltbl, lcols = [(t, cs) for (t, cs) in tbls() if t.ref == lref][-1]
        except IndexError: # The user typed an incorrect table qualifier
            return []
        conds, found_conds = [], set()

        def add_cond(lcol, rcol, rref, meta, prio):
            prefix = '' if suggestion.parent else ltbl.ref + '.'
            case = self.case
            cond = prefix + case(lcol) + ' = ' + rref + '.' + case(rcol)
            if cond not in found_conds:
                found_conds.add(cond)
                conds.append((cond, meta, prio + ref_prio[rref]))

        def list_dict(pairs): # Turns [(a, b), (a, c)] into {a: [b, c]}
            d = defaultdict(list)
            for pair in pairs:
                d[pair[0]].append(pair[1])
            return d

        # Tables that are closer to the cursor get higher prio
        ref_prio = dict((tbl.ref, num) for num, tbl
            in enumerate(suggestion.tables))
        # Map (schema, table, col) to tables
        coldict = list_dict(((t.schema, t.name, c.name), t)
            for t, c in cols if t.ref != lref)
        # For each fk from the left table, generate a join condition if
        # the other table is also in the scope
        fks = ((fk, lcol.name) for lcol in lcols for fk in lcol.foreignkeys)
        for fk, lcol in fks:
            left = col(ltbl.schema, ltbl.name, lcol)
            child = col(fk.childschema, fk.childtable, fk.childcolumn)
            par = col(fk.parentschema, fk.parenttable, fk.parentcolumn)
            left, right = (child, par) if left == child else (par, child)
            for rtbl in coldict[right]:
                add_cond(left.col, right.col, rtbl.ref, 'fk join', 2000)
        # For name matching, use a {(colname, coltype): TableReference} dict
        coltyp = namedtuple('coltyp', 'name datatype')
        col_table = list_dict((coltyp(c.name, c.datatype), t) for t, c in cols)
        # Find all name-match join conditions
        for c in (coltyp(c.name, c.datatype) for c in lcols):
            for rtbl in (t for t in col_table[c] if t.ref != ltbl.ref):
                add_cond(c.name, c.name, rtbl.ref, 'name join', 1000
                    if c.datatype in ('integer', 'bigint', 'smallint') else 0)

        conds, metas, prios = zip(*conds) if conds else ([], [], [])

        return self.find_matches(word_before_cursor, conds,
          meta_collection=metas, type_priority=100, priority_collection=prios)

    def get_function_matches(self, suggestion, word_before_cursor):
        if suggestion.filter == 'for_from_clause':
            # Only suggest functions allowed in FROM clause
            filt = lambda f: not f.is_aggregate and not f.is_window
            funcs = self.populate_functions(suggestion.schema, filt)
        else:
            funcs = self.populate_schema_objects(
                suggestion.schema, 'functions')

        # Function overloading means we way have multiple functions of the same
        # name at this point, so keep unique names only
        funcs = set(funcs)

        funcs = self.find_matches(word_before_cursor, funcs, meta='function')

        if not suggestion.schema and not suggestion.filter:
            # also suggest hardcoded functions using startswith matching
            predefined_funcs = self.find_matches(
                word_before_cursor, self.functions, mode='strict',
                meta='function')
            funcs.extend(predefined_funcs)

        return funcs

    def get_schema_matches(self, _, word_before_cursor):
        schema_names = self.dbmetadata['tables'].keys()

        # Unless we're sure the user really wants them, hide schema names
        # starting with pg_, which are mostly temporary schemas
        if not word_before_cursor.startswith('pg_'):
            schema_names = [s for s in schema_names if not s.startswith('pg_')]

        return self.find_matches(word_before_cursor, schema_names, meta='schema')

    def get_table_matches(self, suggestion, word_before_cursor):
        tables = self.populate_schema_objects(suggestion.schema, 'tables')

        # Unless we're sure the user really wants them, don't suggest the
        # pg_catalog tables that are implicitly on the search path
        if not suggestion.schema and (
                not word_before_cursor.startswith('pg_')):
            tables = [t for t in tables if not t.startswith('pg_')]

        return self.find_matches(word_before_cursor, tables, meta='table')

    def get_view_matches(self, suggestion, word_before_cursor):
        views = self.populate_schema_objects(suggestion.schema, 'views')

        if not suggestion.schema and (
                not word_before_cursor.startswith('pg_')):
            views = [v for v in views if not v.startswith('pg_')]

        return self.find_matches(word_before_cursor, views, meta='view')

    def get_alias_matches(self, suggestion, word_before_cursor):
        aliases = suggestion.aliases
        return self.find_matches(word_before_cursor, aliases,
                                 meta='table alias')

    def get_database_matches(self, _, word_before_cursor):
        return self.find_matches(word_before_cursor, self.databases,
                                 meta='database')

    def get_keyword_matches(self, _, word_before_cursor):
        return self.find_matches(word_before_cursor, self.keywords,
                                 mode='strict', meta='keyword')

    def get_path_matches(self, _, word_before_cursor):
        completer = PathCompleter(expanduser=True)
        document = Document(text=word_before_cursor,
                            cursor_position=len(word_before_cursor))
        for c in completer.get_completions(document, None):
            yield Match(completion=c, priority = None)

    def get_special_matches(self, _, word_before_cursor):
        if not self.pgspecial:
            return []

        commands = self.pgspecial.commands
        cmd_names = commands.keys()
        desc = [commands[cmd].description for cmd in cmd_names]
        return self.find_matches(word_before_cursor, cmd_names, mode='strict',
                                 meta_collection=desc)

    def get_datatype_matches(self, suggestion, word_before_cursor):
        # suggest custom datatypes
        types = self.populate_schema_objects(suggestion.schema, 'datatypes')
        matches = self.find_matches(word_before_cursor, types, meta='datatype')

        if not suggestion.schema:
            # Also suggest hardcoded types
            matches.extend(self.find_matches(word_before_cursor, self.datatypes,
                                             mode='strict', meta='datatype'))

        return matches

    def get_namedquery_matches(self, _, word_before_cursor):
        return self.find_matches(
            word_before_cursor, NamedQueries.instance.list(), meta='named query')

    suggestion_matchers = {
        JoinCondition: get_join_condition_matches,
        Join: get_join_matches,
        Column: get_column_matches,
        Function: get_function_matches,
        Schema: get_schema_matches,
        Table: get_table_matches,
        View: get_view_matches,
        Alias: get_alias_matches,
        Database: get_database_matches,
        Keyword: get_keyword_matches,
        Special: get_special_matches,
        Datatype: get_datatype_matches,
        NamedQuery: get_namedquery_matches,
        Path: get_path_matches,
    }

    def populate_scoped_cols(self, scoped_tbls):
        """ Find all columns in a set of scoped_tables
        :param scoped_tbls: list of TableReference namedtuples
        :return: {TableReference:{colname:ColumnMetaData}}
        """

        columns = OrderedDict()
        meta = self.dbmetadata

        def addcols(schema, rel, alias, reltype, cols):
            tbl = TableReference(schema, rel, alias, reltype == 'functions')
            if tbl not in columns:
                columns[tbl] = []
            columns[tbl].extend(cols)

        for tbl in scoped_tbls:
            schemas = [tbl.schema] if tbl.schema else self.search_path
            for schema in schemas:
                relname = self.escape_name(tbl.name)
                schema = self.escape_name(schema)
                if tbl.is_function:
                # Return column names from a set-returning function
                # Get an array of FunctionMetadata objects
                    functions = meta['functions'].get(schema, {}).get(relname)
                    for func in (functions or []):
                        # func is a FunctionMetadata object
                        cols = func.fields()
                        addcols(schema, relname, tbl.alias, 'functions', cols)
                else:
                    for reltype in ('tables', 'views'):
                        cols = meta[reltype].get(schema, {}).get(relname)
                        if cols:
                            cols = cols.values()
                            addcols(schema, relname, tbl.alias, reltype, cols)
                            break

        return columns

    def populate_schema_objects(self, schema, obj_type):
        """Returns list of tables or functions for a (optional) schema"""

        metadata = self.dbmetadata[obj_type]
        if schema:
            try:
                objects = metadata[self.escape_name(schema)].keys()
            except KeyError:
                # schema doesn't exist
                objects = []
        else:
            schemas = self.search_path
            objects = [obj for schema in schemas
                           for obj in metadata[schema].keys()]

        return objects

    def populate_functions(self, schema, filter_func):
        """Returns a list of function names

        filter_func is a function that accepts a FunctionMetadata namedtuple
        and returns a boolean indicating whether that function should be
        kept or discarded
        """

        metadata = self.dbmetadata['functions']

        # Because of multiple dispatch, we can have multiple functions
        # with the same name, which is why `for meta in metas` is necessary
        # in the comprehensions below
        if schema:
            schema = self.escape_name(schema)
            try:
                return [func for (func, metas) in metadata[schema].items()
                                for meta in metas
                                    if filter_func(meta)]
            except KeyError:
                return []
        else:
            return [func for schema in self.search_path
                            for (func, metas) in metadata[schema].items()
                                for meta in metas
                                    if filter_func(meta)]



